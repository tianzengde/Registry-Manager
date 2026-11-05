import { spawn } from "node:child_process";
import { mkdtemp, rm, access } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createServer } from "node:net";
import { DatabaseSync } from "node:sqlite";
import { hashSync } from "bcryptjs";
async function freePort() {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  await new Promise((resolve) => server.close(resolve));
  return port;
}
export async function setup() {
  await access(".output/server/index.mjs").catch(() => {
    throw new Error("Run npm run build before npm test");
  });
  const directory = await mkdtemp(join(tmpdir(), "registry-manager-test-"));
  const database = join(directory, "legacy.sqlite");
  // Seed the original Tortoise schema and a bcrypt account. The app must preserve it.
  const db = new DatabaseSync(database);
  db.exec(`CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username VARCHAR(64) NOT NULL UNIQUE, password_hash VARCHAR(256) NOT NULL, is_active INT NOT NULL DEFAULT 1, is_admin INT NOT NULL DEFAULT 0, last_login_at TIMESTAMP, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE repositories (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name VARCHAR(256) NOT NULL UNIQUE, is_public INT NOT NULL DEFAULT 0, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE operation_logs (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, actor VARCHAR(64) NOT NULL, action VARCHAR(64) NOT NULL, target VARCHAR(256) NOT NULL, detail TEXT, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);`);
  const password = "isolated-fixture-password";
  for (const [username, admin, active] of [
    ["admin", 1, 1],
    ["member", 0, 1],
    ["disabled", 0, 0],
  ])
    db.prepare(
      "INSERT INTO users (username,password_hash,is_admin,is_active) VALUES (?,?,?,?)",
    ).run(username, hashSync(password, 4), admin, active);
  db.prepare(
    "INSERT INTO operation_logs (actor,action,target,detail) VALUES (?,?,?,?)",
  ).run("admin", "legacy.record", "migration", "preserved");
  db.close();
  const mockPort = await freePort(),
    appPort = await freePort();
  let output = "";
  const children = [];
  async function stop() {
    await Promise.all(
      children.map(
        (child) =>
          new Promise((resolve) => {
            if (child.exitCode !== null) return resolve();
            child.once("exit", resolve);
            child.kill("SIGTERM");
          }),
      ),
    );
    await rm(directory, { recursive: true, force: true });
  }
  function start(args, env) {
    const child = spawn(process.execPath, args, {
      env: { ...process.env, ...env },
      stdio: ["ignore", "pipe", "pipe"],
    });
    child.stdout.on("data", (data) => (output += data));
    child.stderr.on("data", (data) => (output += data));
    children.push(child);
    return child;
  }
  async function waitFor(url, child) {
    for (let n = 0; n < 100; n++) {
      if (child.exitCode !== null) throw new Error(output);
      try {
        await fetch(url);
        return;
      } catch {
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
    }
    throw new Error(`Fixture did not start: ${output}`);
  }
  try {
    const mock = start(["scripts/mock-registry.mjs"], {
      MOCK_PORT: String(mockPort),
    });
    await waitFor(`http://127.0.0.1:${mockPort}/v2/`, mock);
    const app = start([".output/server/index.mjs"], {
      HOST: "127.0.0.1",
      PORT: String(appPort),
      NUXT_REGISTRY_URL: `http://127.0.0.1:${mockPort}`,
      NUXT_DATABASE_PATH: database,
      NUXT_ADMIN_INITIAL_PASSWORD: "must-not-replace-existing-password",
      NUXT_ALLOW_TAG_DELETE: "true",
      NUXT_COOKIE_SECURE: "false",
      NUXT_REGISTRY_USERNAME: "",
      NUXT_REGISTRY_PASSWORD: "",
    });
    await waitFor(`http://127.0.0.1:${appPort}/api/health`, app);
    return { base: `http://127.0.0.1:${appPort}`, password, database, stop };
  } catch (error) {
    await stop();
    throw error;
  }
}
