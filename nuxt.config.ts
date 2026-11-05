export default defineNuxtConfig({
  compatibilityDate: "2026-11-04",
  ssr: false,
  devtools: { enabled: false },
  css: ["~/assets/main.css"],
  app: {
    head: {
      title: "Registry Manager · 镜像控制台",
      htmlAttrs: { lang: "zh-CN" },
      meta: [
        { name: "description", content: "轻量、清晰的私有容器镜像管理控制台" },
      ],
    },
  },
  runtimeConfig: {
    registryUrl: process.env.REGISTRY_URL || "http://127.0.0.1:5000",
    registryPublicUrl: process.env.REGISTRY_PUBLIC_URL || "",
    registryUsername: process.env.REGISTRY_USERNAME || "",
    registryPassword: process.env.REGISTRY_PASSWORD || "",
    databasePath:
      process.env.DATABASE_PATH ||
      process.env.DATABASE_URL?.replace(/^sqlite:\/\//, "") ||
      "db/registry_manager.db",
    adminInitialPassword: process.env.ADMIN_INITIAL_PASSWORD || "",
    allowTagDelete: process.env.ALLOW_TAG_DELETE === "true",
    cookieSecure: process.env.COOKIE_SECURE === "true",
    public: { preview: false },
  },
  nitro: { preset: "node-server", externals: { external: ["node:sqlite"] } },
});
