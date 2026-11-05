import { Readable } from "node:stream";
export default defineEventHandler(async (event) => {
  const raw = getRequestURL(event);
  const path = raw.pathname.slice(4);
  setHeader(event, "Docker-Distribution-API-Version", "registry/2.0");
  // Docker clients authenticate with Basic credentials; browser cookies are never forwarded upstream.
  const user = currentUser(event);
  const write = !["GET", "HEAD", "OPTIONS"].includes(event.method);
  checkOrigin(event);
  const match = path.match(/^(.+)\/(?:manifests|blobs|tags)\//);
  if (!user && (!match || write || !visibility(match[1]!))) {
    setHeader(event, "WWW-Authenticate", 'Basic realm="Registry Manager"');
    throw createError({ statusCode: 401, statusMessage: "需要 Registry 认证" });
  }
  if (write && !user?.is_admin)
    throw createError({ statusCode: 403, statusMessage: "需要管理员权限" });
  const config = useRuntimeConfig();
  const base = config.registryUrl.replace(/\/$/, "");
  if (
    event.method === "DELETE" &&
    path.includes("/manifests/") &&
    !config.allowTagDelete
  )
    throw createError({ statusCode: 403, statusMessage: "镜像删除未启用" });
  const headers = new Headers(getProxyRequestHeaders(event));
  const accept = getHeader(event, "accept");
  if (accept) headers.set("accept", accept);
  headers.delete("authorization");
  headers.delete("cookie");
  headers.set("accept-encoding", "identity");
  for (const [key, value] of Object.entries(registryHeaders()))
    headers.set(key, value);
  const abort = new AbortController();
  event.node.res.once("close", () => {
    if (!event.node.res.writableFinished) abort.abort();
  });
  const hasBody =
    !["GET", "HEAD"].includes(event.method) &&
    (Number(getHeader(event, "content-length") || 0) > 0 ||
      !!getHeader(event, "transfer-encoding"));
  let response: Response;
  try {
    response = await fetch(`${base}${raw.pathname}${raw.search}`, {
      method: event.method,
      headers,
      ...(hasBody
        ? { body: getRequestWebStream(event), duplex: "half" as const }
        : {}),
      redirect: "manual",
      signal: AbortSignal.any([
        abort.signal,
        AbortSignal.timeout(30 * 60 * 1000),
      ]),
    });
  } catch {
    throw createError({
      statusCode: 502,
      statusMessage: "Registry 上游连接失败",
    });
  }
  setResponseStatus(event, response.status);
  for (const [key, value] of response.headers) {
    if (
      ![
        "connection",
        "transfer-encoding",
        "content-encoding",
        "set-cookie",
      ].includes(key) &&
      !(key === "content-length" && response.headers.has("content-encoding"))
    )
      setHeader(event, key, value);
  }
  {
    const location = response.headers.get("location");
    if (location) {
      const url = new URL(location, base);
      if (url.pathname.startsWith("/v2/"))
        setHeader(event, "location", `${url.pathname}${url.search}`);
    }
    const manifest = path.match(/^(.+)\/manifests\/([^/]+)$/);
    if (response.ok && manifest && ["GET", "PUT"].includes(event.method)) {
      const action = event.method === "GET" ? "pull" : "push";
      const day = new Date().toISOString().slice(0, 10);
      db()
        .prepare(
          "INSERT INTO pull_push_events (repository,tag,action) VALUES (?,?,?)",
        )
        .run(manifest[1]!, manifest[2]!, action);
      db()
        .prepare(
          `INSERT INTO repo_daily_stats (repository,day,pulls,pushes,last_activity_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(repository,day) DO UPDATE SET pulls=pulls+excluded.pulls,pushes=pushes+excluded.pushes,last_activity_at=CURRENT_TIMESTAMP`,
        )
        .run(
          manifest[1]!,
          day,
          action === "pull" ? 1 : 0,
          action === "push" ? 1 : 0,
        );
    }
  }
  if (!response.body) return event.node.res.end();
  const stream = Readable.fromWeb(response.body as any);
  event.node.res.once("close", () => stream.destroy());
  return sendStream(event, stream);
});
