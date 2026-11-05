export default defineNuxtRouteMiddleware(async (to) => {
  const legacy: Record<string, string> = {
    "/main/repos": "/",
    "/main/dashboard": "/overview",
    "/main/operations": "/activity",
    "/main/settings": "/settings",
    "/main": "/",
  };
  if (legacy[to.path]) return navigateTo(legacy[to.path]!);
  if (!["/", "/login", "/overview", "/activity", "/settings"].includes(to.path))
    return abortNavigation(
      createError({ statusCode: 404, statusMessage: "页面不存在" }),
    );
  const session = useSession();
  if (!session.checked.value) await session.check();
  if (!session.user.value && to.path !== "/login") return navigateTo("/login");
  if (session.user.value && to.path === "/login") return navigateTo("/");
  if (
    ["/activity", "/settings", "/overview"].includes(to.path) &&
    !session.user.value?.is_admin
  )
    return navigateTo("/");
});
