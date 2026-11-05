import { DatabaseSync } from "node:sqlite";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { randomBytes, createHash } from "node:crypto";
import { hashSync } from "bcryptjs";
let instance: DatabaseSync;
export function db() {
  if (instance) return instance;
  const config = useRuntimeConfig();
  const path = resolve(config.databasePath);
  mkdirSync(dirname(path), { recursive: true });
  instance = new DatabaseSync(path);
  instance.exec(`PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1, is_admin INTEGER NOT NULL DEFAULT 0, last_login_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS repositories (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, is_public INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS operation_logs (id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS pull_push_events (id INTEGER PRIMARY KEY, repository TEXT NOT NULL, tag TEXT, action TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS repo_daily_stats (id INTEGER PRIMARY KEY, repository TEXT NOT NULL, day TEXT NOT NULL, pulls INTEGER NOT NULL DEFAULT 0, pushes INTEGER NOT NULL DEFAULT 0, last_activity_at TEXT, UNIQUE(repository, day));
    CREATE TABLE IF NOT EXISTS web_sessions (token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires_at INTEGER NOT NULL);
  `);
  if (!instance.prepare("SELECT id FROM users LIMIT 1").get()) {
    const password = String(
      config.adminInitialPassword || randomBytes(18).toString("base64url"),
    );
    instance
      .prepare(
        "INSERT INTO users (username,password_hash,is_admin) VALUES (?,?,1)",
      )
      .run("admin", hashSync(password, 12));
    if (!config.adminInitialPassword)
      console.warn(
        `[Registry Manager] 首次管理员密码: ${password}（请登录后修改）`,
      );
  }
  return instance;
}
export function log(
  actor: string,
  action: string,
  target: string,
  detail = "",
) {
  db()
    .prepare(
      "INSERT INTO operation_logs (actor, action, target, detail) VALUES (?,?,?,?)",
    )
    .run(actor, action, target, detail);
}
export function sessionHash(value: string) {
  return createHash("sha256").update(value).digest("hex");
}
export function visibility(name: string): boolean {
  if (name === "public" || name.startsWith("public/")) return true;
  return !!db()
    .prepare("SELECT is_public FROM repositories WHERE name=?")
    .get(name)?.is_public;
}
