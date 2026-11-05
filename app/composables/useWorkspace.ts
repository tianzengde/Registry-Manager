export function createWorkspace() {
  const route = useRoute();
  const runtime = useRuntimeConfig();
  const { user, logout } = useSession();
  const section = computed(
    () =>
      ({
        "/overview": "overview",
        "/activity": "activity",
        "/settings": "settings",
      })[route.path] || "repositories",
  );
  const nav = computed(() => [
    { path: "/", label: "镜像仓库", icon: "Boxes", key: "repositories" },
    ...(user.value?.is_admin
      ? [
          {
            path: "/overview",
            label: "运行概览",
            icon: "LayoutDashboard",
            key: "overview",
          },
          {
            path: "/activity",
            label: "操作记录",
            icon: "Activity",
            key: "activity",
          },
          {
            path: "/settings",
            label: "设置",
            icon: "Settings2",
            key: "settings",
          },
        ]
      : []),
  ]);
  const title = computed(
    () => nav.value.find((n) => n.key === section.value)?.label || "镜像仓库",
  );
  const {
    data: repos,
    error: repoError,
    status,
    refresh,
  } = useFetch<any[]>("/api/repositories", { default: () => [] });
  const { data: health, refresh: refreshHealth } = useFetch<any>("/api/health");
  const settings = ref<any>(null),
    overview = ref<any>(null),
    logs = ref<any>({ items: [], total: 0 });
  const search = ref(""),
    filter = ref("all"),
    sort = ref("name"),
    selected = ref<any>(null),
    detail = ref<any>(null),
    detailLoading = ref(false),
    detailError = ref(""),
    activeTab = ref("tags"),
    drawerSearch = ref("");
  const showConnect = ref(false),
    showDelete = ref(false),
    deleting = ref(false),
    notice = ref(""),
    copied = ref(""),
    mobile = ref(false),
    activitySearch = ref(""),
    logPage = ref(0),
    pageError = ref(""),
    pageBusy = ref(false);
  const password = reactive({ current_password: "", new_password: "" }),
    passwordBusy = ref(false);
  const totalTags = computed(() =>
    repos.value.reduce((n, r) => n + (r.tags_count || 0), 0),
  );
  const namespaces = computed(
    () =>
      new Set(
        repos.value.map((r) =>
          r.name.includes("/") ? r.name.split("/")[0] : "library",
        ),
      ).size,
  );
  const visible = computed(() =>
    repos.value
      .filter(
        (r) =>
          r.name.toLowerCase().includes(search.value.toLowerCase()) &&
          (filter.value === "all" ||
            (filter.value === "public" ? r.is_public : !r.is_public)),
      )
      .sort((a, b) =>
        sort.value === "tags"
          ? (b.tags_count || 0) - (a.tags_count || 0)
          : a.name.localeCompare(b.name),
      ),
  );
  const host = computed(
    () =>
      settings.value?.registry_public_url
        ?.replace(/^https?:\/\//, "")
        .replace(/\/$/, "") || (import.meta.client ? location.host : ""),
  );
  const tags = computed(() =>
    (selected.value?.tags || []).filter((t: string) =>
      t.includes(drawerSearch.value),
    ),
  );
  const pullCommand = computed(
    () =>
      `docker pull ${host.value}/${selected.value?.name}:${detail.value?.reference || selected.value?.tags?.[0] || "latest"}`,
  );
  const color = (name: string) =>
    ["teal", "violet", "blue", "amber"][
      [...name].reduce((n, c) => n + c.charCodeAt(0), 0) % 4
    ];
  function size(n: number) {
    return n ? `${(n / 1024 / 1024).toFixed(1)} MB` : "—";
  }
  function date(value: string) {
    return value
      ? new Date(
          value.includes("T") ? value : `${value.replace(" ", "T")}Z`,
        ).toLocaleString("zh-CN", { hour12: false })
      : "—";
  }
  function message(e: any) {
    return e.data?.statusMessage || e.statusMessage || "请求失败，请重试";
  }
  async function copy(text: string, key: string) {
    try {
      await navigator.clipboard.writeText(text);
      copied.value = key;
      setTimeout(() => (copied.value = ""), 1800);
    } catch {
      notice.value = "无法访问剪贴板，请手动复制命令";
    }
  }
  async function reload() {
    await Promise.all([refresh(), refreshHealth()]);
  }
  async function openRepo(repo: any) {
    selected.value = repo;
    detail.value = null;
    detailError.value = "";
    activeTab.value = "tags";
    drawerSearch.value = "";
    if (repo.tags?.length) await loadDetail(repo.tags[0]);
  }
  let detailRequest = 0;
  async function loadDetail(tag: string) {
    const request = ++detailRequest;
    const repo = selected.value?.name;
    detailLoading.value = true;
    detailError.value = "";
    detail.value = null;
    try {
      const result = await $fetch(
        `/api/repositories/${repo}/manifests/${encodeURIComponent(tag)}`,
      );
      if (request === detailRequest && selected.value?.name === repo)
        detail.value = result;
    } catch (e) {
      if (request === detailRequest) detailError.value = message(e);
    } finally {
      if (request === detailRequest) detailLoading.value = false;
    }
  }
  async function loadPage() {
    pageBusy.value = true;
    pageError.value = "";
    try {
      if (user.value?.is_admin && !settings.value)
        settings.value = await $fetch("/api/settings");
      if (section.value === "overview")
        overview.value = await $fetch("/api/dashboard/overview");
      if (section.value === "activity")
        logs.value = await $fetch("/api/logs/operations", {
          query: {
            search: activitySearch.value,
            skip: logPage.value * 30,
            limit: 30,
          },
        });
    } catch (e) {
      pageError.value = message(e);
    } finally {
      pageBusy.value = false;
    }
  }
  watch(
    () => route.path,
    () => {
      mobile.value = false;
      selected.value = null;
      loadPage();
    },
  );
  onMounted(loadPage);
  async function visibilityChange() {
    try {
      const r: any = await $fetch(`/api/repositories/${selected.value.name}`, {
        method: "PUT",
        body: { is_public: !selected.value.is_public },
      });
      selected.value.is_public = r.is_public;
      await refresh();
      notice.value = "仓库可见性已更新";
    } catch (e) {
      notice.value = message(e);
    }
  }
  async function remove() {
    deleting.value = true;
    try {
      await $fetch(
        `/api/images/${selected.value.name}/manifests/${detail.value.digest}`,
        { method: "DELETE" },
      );
      showDelete.value = false;
      selected.value = null;
      await refresh();
      notice.value = "Manifest 已删除；磁盘回收需运行 Registry 垃圾回收";
    } catch (e) {
      notice.value = message(e);
    } finally {
      deleting.value = false;
    }
  }
  async function changePassword() {
    passwordBusy.value = true;
    try {
      await $fetch("/api/auth/password", { method: "POST", body: password });
      user.value = null;
      await navigateTo("/login");
    } catch (e) {
      notice.value = message(e);
    } finally {
      passwordBusy.value = false;
    }
  }
  let previousFocus: HTMLElement | null = null;
  const overlayOpen = computed(
    () => !!selected.value || showConnect.value || showDelete.value,
  );
  watch(
    [() => !!selected.value, showConnect, showDelete],
    async (state, previous) => {
      const open = state.some(Boolean);
      if (open) {
        if (!previous.some(Boolean))
          previousFocus = document.activeElement as HTMLElement;
        document.body.style.overflow = "hidden";
        await nextTick();
        const dialogs = document.querySelectorAll('[aria-modal="true"]');
        (
          dialogs[dialogs.length - 1]?.querySelector("button") as HTMLElement
        )?.focus();
      } else {
        document.body.style.overflow = "";
        previousFocus?.focus();
      }
    },
  );
  function onKey(e: KeyboardEvent) {
    if (
      e.key === "/" &&
      !["INPUT", "TEXTAREA", "SELECT"].includes(
        (e.target as HTMLElement)?.tagName,
      ) &&
      !overlayOpen.value
    ) {
      e.preventDefault();
      (
        document.querySelector('[aria-label="搜索仓库"]') as HTMLInputElement
      )?.focus();
    }
    if (e.key === "Escape") {
      if (showDelete.value) showDelete.value = false;
      else if (showConnect.value) showConnect.value = false;
      else selected.value = null;
    }
    if (e.key === "Tab" && overlayOpen.value) {
      const dialogs = document.querySelectorAll('[aria-modal="true"]');
      const focusable = dialogs[
        dialogs.length - 1
      ]?.querySelectorAll<HTMLElement>(
        'button:not(:disabled),input,select,a[href],[tabindex="0"]',
      );
      if (!focusable?.length) return;
      const first = focusable[0]!,
        last = focusable[focusable.length - 1]!;
      if (
        e.shiftKey &&
        (document.activeElement === first ||
          !dialogs[dialogs.length - 1]?.contains(document.activeElement))
      ) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }
  onMounted(() => window.addEventListener("keydown", onKey));
  onUnmounted(() => {
    window.removeEventListener("keydown", onKey);
    document.body.style.overflow = "";
  });
  return {
    route,
    runtime,
    user,
    logout,
    section,
    nav,
    title,
    repos,
    repoError,
    status,
    refresh,
    health,
    settings,
    overview,
    logs,
    search,
    filter,
    sort,
    selected,
    detail,
    detailLoading,
    detailError,
    activeTab,
    drawerSearch,
    showConnect,
    showDelete,
    deleting,
    notice,
    copied,
    mobile,
    activitySearch,
    logPage,
    pageError,
    pageBusy,
    password,
    passwordBusy,
    totalTags,
    namespaces,
    visible,
    host,
    tags,
    pullCommand,
    color,
    size,
    date,
    message,
    copy,
    reload,
    openRepo,
    loadDetail,
    loadPage,
    visibilityChange,
    remove,
    changePassword,
    overlayOpen,
  };
}
export function useWorkspace() {
  const workspace = inject<ReturnType<typeof createWorkspace>>("workspace");
  if (!workspace) throw new Error("Workspace layout is required");
  return workspace;
}
