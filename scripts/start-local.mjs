import { loadEnvFile } from "node:process";
import { existsSync } from "node:fs";
if (existsSync(".env")) loadEnvFile(".env");
const mapping = {
  REGISTRY_URL: "NUXT_REGISTRY_URL",
  REGISTRY_PUBLIC_URL: "NUXT_REGISTRY_PUBLIC_URL",
  REGISTRY_USERNAME: "NUXT_REGISTRY_USERNAME",
  REGISTRY_PASSWORD: "NUXT_REGISTRY_PASSWORD",
  ADMIN_INITIAL_PASSWORD: "NUXT_ADMIN_INITIAL_PASSWORD",
  ALLOW_TAG_DELETE: "NUXT_ALLOW_TAG_DELETE",
  COOKIE_SECURE: "NUXT_COOKIE_SECURE",
};
for (const [source, target] of Object.entries(mapping)) {
  if (process.env[source] !== undefined && process.env[target] === undefined)
    process.env[target] = process.env[source];
}
process.env.NUXT_DATABASE_PATH ||=
  process.env.DATABASE_PATH ||
  process.env.DATABASE_URL?.replace(/^sqlite:\/\//, "") ||
  "db/registry_manager.db";
process.env.NUXT_PUBLIC_PREVIEW = "false";
await import("../.output/server/index.mjs");
