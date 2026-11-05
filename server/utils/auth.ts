import { compareSync } from "bcryptjs";
import type { H3Event } from "h3";
export interface User {
  id: number;
  username: string;
  is_admin: number;
  is_active: number;
  password_hash: string;
  created_at: string;
}
export function currentUser(event: H3Event): User | undefined {
  const token = getCookie(event, "registry_session");
  if (token) {
    const user = db()
      .prepare(
        "SELECT u.* FROM users u JOIN web_sessions s ON s.user_id=u.id WHERE s.token=? AND s.expires_at>? AND u.is_active=1",
      )
      .get(sessionHash(token), Date.now());
    if (user) return user as unknown as User;
  }
  const header = getHeader(event, "authorization") || "";
  if (!header.startsWith("Basic ")) return;
  const decoded = Buffer.from(header.slice(6), "base64").toString("utf8");
  const colon = decoded.indexOf(":");
  if (colon < 0) return;
  const user = db()
    .prepare("SELECT * FROM users WHERE username=? AND is_active=1")
    .get(decoded.slice(0, colon)) as unknown as User | undefined;
  if (user && compareSync(decoded.slice(colon + 1), user.password_hash))
    return user;
}
export function requireUser(event: H3Event, admin = false) {
  const user = currentUser(event);
  if (!user) throw createError({ statusCode: 401, statusMessage: "请先登录" });
  if (admin && !user.is_admin)
    throw createError({ statusCode: 403, statusMessage: "需要管理员权限" });
  return user;
}
export function checkOrigin(event: H3Event) {
  if (["GET", "HEAD", "OPTIONS"].includes(event.method)) return;
  const origin = getHeader(event, "origin");
  if (origin && new URL(origin).host !== getHeader(event, "host"))
    throw createError({ statusCode: 403, statusMessage: "请求来源无效" });
}
export function publicUser(user: User) {
  return {
    username: user.username,
    is_admin: !!user.is_admin,
    created_at: user.created_at,
  };
}
