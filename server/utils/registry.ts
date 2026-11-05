export const manifestAccept = [
  "application/vnd.oci.image.index.v1+json",
  "application/vnd.docker.distribution.manifest.list.v2+json",
  "application/vnd.oci.image.manifest.v1+json",
  "application/vnd.docker.distribution.manifest.v2+json",
].join(", ");
export function registryHeaders(): Record<string, string> {
  const c = useRuntimeConfig();
  return c.registryUsername
    ? {
        Authorization: `Basic ${Buffer.from(`${c.registryUsername}:${c.registryPassword}`).toString("base64")}`,
      }
    : {};
}
export async function registryRequest(path: string, options: RequestInit = {}) {
  const c = useRuntimeConfig();
  let response: Response;
  try {
    response = await fetch(`${c.registryUrl.replace(/\/$/, "")}/v2/${path}`, {
      ...options,
      headers: {
        ...registryHeaders(),
        Accept: manifestAccept,
        ...Object.fromEntries(new Headers(options.headers).entries()),
      },
      signal: AbortSignal.timeout(15000),
      redirect: "follow",
    });
  } catch {
    throw createError({
      statusCode: 502,
      statusMessage: "无法连接 Registry，请检查地址和服务状态",
    });
  }
  if (!response.ok)
    throw createError({
      statusCode: response.status === 404 ? 404 : 502,
      statusMessage: `Registry 返回 ${response.status}`,
    });
  return response;
}
export async function registryList(
  path: string,
  field: string,
): Promise<string[]> {
  const values: string[] = [];
  let last = "";
  for (let page = 0; page < 10000; page++) {
    const response = await registryRequest(
      `${path}?n=100&last=${encodeURIComponent(last)}`,
    );
    const result = await response.json();
    const rows: string[] = result[field] || [];
    values.push(...rows);
    if (!response.headers.get("link")?.includes('rel="next"'))
      return [...new Set(values)].sort();
    const next = response.headers.get("link")?.match(/<([^>]+)>/)?.[1];
    const cursor = next
      ? new URL(next, "http://registry").searchParams.get("last")
      : rows.at(-1);
    if (!cursor || cursor === last)
      throw createError({
        statusCode: 502,
        statusMessage: "Registry 分页游标异常",
      });
    last = cursor;
  }
  throw createError({
    statusCode: 502,
    statusMessage: "Registry 分页数量超出限制",
  });
}
export function repoPath(name: string) {
  if (
    !/^[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*(?:\/[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*)*$/.test(
      name,
    )
  )
    throw createError({ statusCode: 400, statusMessage: "仓库名称无效" });
  return name.split("/").map(encodeURIComponent).join("/");
}
// Registry 不提供标签推送时间，仅使用代理成功接收且摘要一致的推送记录。
export async function metadata(name: string, ref: string) {
  async function readManifest(reference: string) {
    const response = await registryRequest(
      `${repoPath(name)}/manifests/${encodeURIComponent(reference)}`,
    );
    return {
      manifest: await response.json(),
      digest: response.headers.get("docker-content-digest") || "",
    };
  }
  async function imageInfo(manifest: any) {
    if (!manifest.config?.digest) return { size_bytes: null, created_at: null };
    const config = await (
      await registryRequest(
        `${repoPath(name)}/blobs/${encodeURIComponent(manifest.config.digest)}`,
      )
    ).json();
    return {
      size_bytes: (manifest.layers || []).reduce(
        (n: number, l: any) => n + (l.size || 0),
        0,
      ),
      created_at: config.created || null,
      os: config.os,
      architecture: config.architecture,
      variant: config.variant,
    };
  }
  const { manifest, digest } = await readManifest(ref);
  const info = await imageInfo(manifest);
  const platforms: any[] = [];
  const descriptors = (manifest.manifests || []).filter(
    (m: any) =>
      m.platform?.os &&
      m.platform.os !== "unknown" &&
      m.platform?.architecture &&
      m.platform.architecture !== "unknown",
  );
  for (let i = 0; i < descriptors.length; i += 4) {
    platforms.push(
      ...(await Promise.all(
        descriptors.slice(i, i + 4).map(async (m: any) => {
          try {
            const child = await readManifest(m.digest);
            return {
              ...(await imageInfo(child.manifest)),
              ...m.platform,
              digest: m.digest,
            };
          } catch {
            return {
              ...m.platform,
              digest: m.digest,
              size_bytes: null,
              created_at: null,
              error: true,
            };
          }
        }),
      )),
    );
  }
  if (!descriptors.length && info.os && info.architecture)
    platforms.push({ ...info, digest });
  const pushed = db()
    .prepare(
      "SELECT pushed_at FROM tag_push_metadata WHERE repository=? AND tag=? AND digest=?",
    )
    .get(name, ref, digest) as any;
  return {
    repository: name,
    reference: ref,
    digest,
    media_type: manifest.mediaType,
    ...info,
    pushed_at: pushed?.pushed_at || null,
    platforms,
    manifest,
  };
}
