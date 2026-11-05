import { randomBytes } from "node:crypto";
import { compareSync, hashSync } from "bcryptjs";
const attempts = new Map<string, { count: number; until: number }>();
export default defineEventHandler(async (event) => {
  checkOrigin(event);
  const path = (getRouterParam(event, "path") || "").replace(/\/$/, "");
  const method = event.method;
  if (path === "auth/login" && method === "POST") {
    const ip = getRequestIP(event) || "local";
    for (const [key, value] of attempts)
      if (value.until < Date.now()) attempts.delete(key);
    const attempt = attempts.get(ip);
    if (attempt && attempt.count >= 10)
      throw createError({
        statusCode: 429,
        statusMessage: "尝试过多，请 15 分钟后重试",
      });
    const body = await readBody(event);
    if (
      typeof body?.username !== "string" ||
      typeof body?.password !== "string" ||
      body.password.length > 1024
    )
      throw createError({
        statusCode: 400,
        statusMessage: "请输入用户名和密码",
      });
    const user = db()
      .prepare("SELECT * FROM users WHERE username=? AND is_active=1")
      .get(body.username) as any;
    if (!user || !compareSync(body.password, user.password_hash)) {
      attempts.set(ip, {
        count: (attempt?.count || 0) + 1,
        until: attempt?.until || Date.now() + 900000,
      });
      throw createError({ statusCode: 401, statusMessage: "用户名或密码错误" });
    }
    attempts.delete(ip);
    const token = randomBytes(32).toString("hex");
    db().prepare("DELETE FROM web_sessions WHERE expires_at<?").run(Date.now());
    db()
      .prepare("INSERT INTO web_sessions VALUES (?,?,?)")
      .run(sessionHash(token), user.id, Date.now() + 86400000);
    setCookie(event, "registry_session", token, {
      httpOnly: true,
      sameSite: "lax",
      secure: !!useRuntimeConfig().cookieSecure,
      path: "/",
      maxAge: 86400,
    });
    db()
      .prepare("UPDATE users SET last_login_at=CURRENT_TIMESTAMP WHERE id=?")
      .run(user.id);
    log(user.username, "login", "auth", "Web 登录");
    return publicUser(user);
  }
  if (path === "auth/logout" && method === "POST") {
    const token = getCookie(event, "registry_session");
    if (token)
      db()
        .prepare("DELETE FROM web_sessions WHERE token=?")
        .run(sessionHash(token));
    deleteCookie(event, "registry_session", { path: "/" });
    return { ok: true };
  }
  if (path === "auth/me" && method === "GET")
    return publicUser(requireUser(event));
  if (path === "auth/password" && method === "POST") {
    const user = requireUser(event);
    const body = await readBody(event);
    if (
      typeof body?.current_password !== "string" ||
      !compareSync(body.current_password, user.password_hash)
    )
      throw createError({ statusCode: 400, statusMessage: "当前密码不正确" });
    if (
      typeof body.new_password !== "string" ||
      body.new_password.length < 8 ||
      Buffer.byteLength(body.new_password) > 72
    )
      throw createError({
        statusCode: 400,
        statusMessage: "新密码至少 8 个字符，且不超过 72 字节",
      });
    db()
      .prepare(
        "UPDATE users SET password_hash=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
      )
      .run(hashSync(body.new_password, 12), user.id);
    db().prepare("DELETE FROM web_sessions WHERE user_id=?").run(user.id);
    deleteCookie(event, "registry_session", { path: "/" });
    log(user.username, "password", "auth", "修改密码");
    return { ok: true };
  }
  if (path === "health" && method === "GET") {
    requireUser(event);
    try {
      await registryRequest("");
      return { connected: true };
    } catch {
      return { connected: false };
    }
  }
  if (path === "settings" && method === "GET") {
    requireUser(event, true);
    const config = useRuntimeConfig();
    return {
      registry_url: config.registryUrl,
      registry_public_url:
        config.registryPublicUrl || getRequestURL(event).host,
      allow_tag_delete: config.allowTagDelete,
    };
  }
  if (path === "repositories" && method === "GET") {
    const user = currentUser(event);
    const names = await registryList("_catalog", "repositories");
    const visible = names.filter((name) => user || visibility(name));
    const result: any[] = [];
    for (let i = 0; i < visible.length; i += 8)
      result.push(
        ...(await Promise.all(
          visible.slice(i, i + 8).map(async (name) => {
            try {
              const tags = await registryList(
                `${repoPath(name)}/tags/list`,
                "tags",
              );
              return {
                name,
                is_public: visibility(name),
                tags_count: tags.length,
                tags,
                error: false,
              };
            } catch {
              return {
                name,
                is_public: visibility(name),
                tags_count: null,
                tags: [],
                error: true,
              };
            }
          }),
        )),
      );
    return result;
  }
  const repoMatch = path.match(
    /^repositories\/(.+)\/(tags|manifests\/([^/]+))$/,
  );
  if (repoMatch && method === "GET") {
    const name = repoMatch[1]!;
    if (!currentUser(event) && !visibility(name))
      throw createError({ statusCode: 403, statusMessage: "此仓库需要登录" });
    if (repoMatch[2] === "tags")
      return {
        repository: name,
        tags: await registryList(`${repoPath(name)}/tags/list`, "tags"),
      };
    return metadata(name, repoMatch[3]!);
  }
  if (path.startsWith("repositories/") && method === "PUT") {
    const user = requireUser(event, true);
    const name = path.slice(13);
    repoPath(name);
    const body = await readBody(event);
    if (typeof body?.is_public !== "boolean")
      throw createError({ statusCode: 400, statusMessage: "可见性参数无效" });
    if (name === "public" || name.startsWith("public/"))
      throw createError({
        statusCode: 400,
        statusMessage: "public 命名空间固定为公开",
      });
    db()
      .prepare(
        "INSERT INTO repositories (name,is_public) VALUES (?,?) ON CONFLICT(name) DO UPDATE SET is_public=excluded.is_public, updated_at=CURRENT_TIMESTAMP",
      )
      .run(name, Number(body.is_public));
    log(
      user.username,
      "repo.update_visibility",
      name,
      body.is_public ? "设为公开" : "设为私有",
    );
    return { name, is_public: body.is_public };
  }
  const image = path.match(/^images\/(.+)\/manifests\/(sha256:[a-f0-9]{64})$/);
  if (image && method === "DELETE") {
    const user = requireUser(event, true);
    if (!useRuntimeConfig().allowTagDelete)
      throw createError({
        statusCode: 403,
        statusMessage: "未启用删除，请设置 NUXT_ALLOW_TAG_DELETE=true",
      });
    await registryRequest(`${repoPath(image[1]!)}/manifests/${image[2]}`, {
      method: "DELETE",
    });
    log(user.username, "delete", image[1]!, `删除 manifest ${image[2]}`);
    return { ok: true };
  }
  if (path === "logs/operations" && method === "GET") {
    requireUser(event, true);
    const q = getQuery(event);
    const skip = Math.max(0, Number(q.skip) || 0),
      limit = Math.min(200, Math.max(1, Number(q.limit) || 30));
    const term = `%${String(q.search || "")}%`;
    const where = "WHERE actor LIKE ? OR target LIKE ? OR action LIKE ?";
    return {
      total: db()
        .prepare(`SELECT count(*) n FROM operation_logs ${where}`)
        .get(term, term, term)?.n,
      items: db()
        .prepare(
          `SELECT * FROM operation_logs ${where} ORDER BY id DESC LIMIT ? OFFSET ?`,
        )
        .all(term, term, term, limit, skip),
    };
  }
  if (path === "dashboard/overview" && method === "GET") {
    requireUser(event, true);
    const totals = db()
      .prepare(
        "SELECT COALESCE(SUM(pulls),0) pulls, COALESCE(SUM(pushes),0) pushes FROM repo_daily_stats WHERE day>=date('now','-29 days')",
      )
      .get() as any;
    return {
      pulls_30d: totals.pulls,
      pushes_30d: totals.pushes,
      recent_events: db()
        .prepare("SELECT * FROM pull_push_events ORDER BY id DESC LIMIT 12")
        .all(),
      daily: db()
        .prepare(
          "SELECT day,SUM(pulls) pulls,SUM(pushes) pushes FROM repo_daily_stats WHERE day>=date('now','-29 days') GROUP BY day ORDER BY day",
        )
        .all(),
    };
  }
  throw createError({ statusCode: 404, statusMessage: "接口不存在" });
});
