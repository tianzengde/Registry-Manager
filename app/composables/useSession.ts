export function useSession() {
  const user = useState<{ username: string; is_admin: boolean } | null>(
    "user",
    () => null,
  );
  const checked = useState("session-checked", () => false);
  async function check() {
    try {
      user.value = (await $fetch("/api/auth/me")) as any;
    } catch {
      user.value = null;
    }
    checked.value = true;
    return user.value;
  }
  async function logout() {
    await $fetch("/api/auth/logout", { method: "POST" });
    user.value = null;
    await navigateTo("/login");
  }
  return { user, checked, check, logout };
}
