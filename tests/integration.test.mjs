import { test, before, after } from "node:test";
import { setup } from "./setup.mjs";
import assert from "node:assert/strict";
let base, password, fixture;
before(async () => {
  fixture = await setup();
  base = fixture.base;
  password = fixture.password;
});
after(async () => {
  await fixture?.stop();
});
let cookie = "";
async function request(path, init = {}) {
  return fetch(`${base}${path}`, {
    ...init,
    headers: { ...(cookie ? { Cookie: cookie } : {}), ...init.headers },
  });
}
test("Nuxt API, authentication, nested repositories, OCI, proxy and deletion", async () => {
  assert.match(new URL(base).hostname, /^(127\.0\.0\.1|localhost)$/);
  assert.equal((await request("/api/auth/me")).status, 401);
  assert.equal((await request("/v2/")).status, 401);
  assert.equal((await request("/v2")).status, 401);
  assert.equal(
    (await request("/api/repositories/acme/api/manifests/latest")).status,
    403,
  );
  const anonymous = await (await request("/api/repositories")).json();
  assert.deepEqual(
    anonymous.map((r) => r.name),
    ["public/alpine"],
  );
  assert.equal(
    (await request("/v2/public/alpine/manifests/latest")).status,
    200,
  );
  const basic = (name) =>
    `Basic ${Buffer.from(`${name}:${password}`).toString("base64")}`;
  assert.equal(
    (await request("/v2/", { headers: { Authorization: basic("admin") } }))
      .status,
    200,
  );
  assert.equal(
    (await request("/v2/", { headers: { Authorization: basic("disabled") } }))
      .status,
    401,
  );
  assert.equal(
    (
      await request("/v2/acme/api/manifests/latest", {
        method: "PUT",
        headers: { Authorization: basic("member") },
        body: "{}",
      })
    ).status,
    403,
  );
  assert.equal(
    (
      await request("/api/logs/operations", {
        headers: { Authorization: basic("member") },
      })
    ).status,
    403,
  );
  const login = await request("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: "admin", password }),
  });
  assert.equal(login.status, 200);
  assert.match(login.headers.get("set-cookie"), /HttpOnly/i);
  cookie = login.headers.get("set-cookie").split(";")[0];
  assert.equal(
    (await (await request("/api/auth/me")).json()).username,
    "admin",
  );
  assert.equal(
    (
      await request("/api/auth/logout", {
        method: "POST",
        headers: { Origin: "https://untrusted.invalid" },
      })
    ).status,
    403,
  );
  const repos = await (await request("/api/repositories")).json();
  assert.equal(repos.length, 6);
  assert.equal(repos.find((r) => r.name === "acme/api").tags_count, 3);
  const manifest = await (
    await request("/api/repositories/acme/api/manifests/latest")
  ).json();
  assert.equal(manifest.architecture, "arm64");
  const head = await request("/v2/acme/api/manifests/latest", {
    method: "HEAD",
  });
  assert.equal(head.status, 200);
  assert.ok(Number(head.headers.get("content-length")) > 0);
  assert.equal(head.headers.get("docker-content-digest"), manifest.digest);
  assert.equal(await head.text(), "");
  assert.equal(manifest.size_bytes, 28672000);
  const index = await (
    await request("/api/repositories/public/alpine/manifests/latest")
  ).json();
  assert.equal(index.platforms.length, 2);
  const ociAccept =
    "application/vnd.oci.image.index.v1+json, application/vnd.oci.image.manifest.v1+json";
  const oci = await request("/v2/public/alpine/manifests/oci-required", {
    headers: { Accept: ociAccept },
  });
  assert.equal(oci.status, 200);
  assert.equal((await oci.json()).received_accept, ociAccept);
  const ociHead = await request("/v2/public/alpine/manifests/oci-required", {
    method: "HEAD",
    headers: { Accept: ociAccept },
  });
  assert.equal(ociHead.status, 200);
  for (const method of ["POST", "PUT"]) {
    const empty = await request("/v2/acme/api/blobs/uploads/", {
      method,
      signal: AbortSignal.timeout(5000),
    });
    assert.equal(empty.status, method === "POST" ? 202 : 201);
    assert.equal((await empty.json()).bytes, 0);
  }

  assert.equal((await request("/v2/acme/api/manifests/latest")).status, 200);
  const upload = await request("/v2/acme/api/blobs/uploads/", {
    method: "POST",
    body: "stream-content",
    headers: { "Content-Type": "application/octet-stream" },
  });
  assert.equal(upload.status, 202);
  assert.equal(
    upload.headers.get("location"),
    "/v2/acme/api/blobs/uploads/test?state=ok",
  );
  const payload = await upload.json();
  assert.equal(payload.bytes, 14);
  assert.equal(payload.cookie, "");
  assert.equal(payload.auth, "");
  const visibility = await request("/api/repositories/acme/api", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_public: true }),
  });
  assert.equal(visibility.status, 200);
  assert.equal(
    (
      await request("/api/images/acme/api/manifests/" + manifest.digest, {
        method: "DELETE",
      })
    ).status,
    200,
  );
  const logs = await (await request("/api/logs/operations")).json();
  assert.ok(logs.items.some((item) => item.action === "delete"));
  assert.ok(logs.items.some((item) => item.action === "legacy.record"));
  const overview = await (await request("/api/dashboard/overview")).json();
  assert.ok(overview.pulls_30d >= 1);
  assert.equal(
    (
      await request("/api/auth/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: "wrong",
          new_password: "new-test-password",
        }),
      })
    ).status,
    400,
  );
  const change = await request("/api/auth/password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_password: password,
      new_password: "new-test-password",
    }),
  });
  assert.equal(change.status, 200);
  assert.equal((await request("/api/auth/me")).status, 401);
  const relogin = await request("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: "admin", password: "new-test-password" }),
  });
  assert.equal(relogin.status, 200);
  cookie = relogin.headers.get("set-cookie").split(";")[0];
  await request("/api/auth/logout", { method: "POST" });
  assert.equal((await request("/api/auth/me")).status, 401);
});
