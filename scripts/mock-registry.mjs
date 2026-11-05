import { createServer } from "node:http";
const names = [
  "acme/api",
  "acme/web",
  "infra/nginx",
  "infra/postgres",
  "public/alpine",
  "worker",
];
const digest = `sha256:${"a".repeat(64)}`;
const single = {
  schemaVersion: 2,
  mediaType: "application/vnd.oci.image.manifest.v1+json",
  config: {
    digest: `sha256:${"c".repeat(64)}`,
    size: 100,
    mediaType: "application/vnd.oci.image.config.v1+json",
  },
  layers: [
    {
      size: 28672000,
      digest: `sha256:${"b".repeat(64)}`,
      mediaType: "application/vnd.oci.image.layer.v1.tar+gzip",
    },
  ],
};
const deleted = new Set();
const server = createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  const path = decodeURIComponent(url.pathname);
  res.setHeader("Content-Type", "application/json");
  const json = (data, status = 200) => {
    res.statusCode = status;
    res.end(JSON.stringify(data));
  };
  if (path === "/v2/" || path === "/v2") return json({});
  if (path === "/v2/_catalog") {
    if (!url.searchParams.get("last")) {
      res.setHeader(
        "Link",
        '</v2/_catalog?n=3&last=infra%2Fnginx>; rel="next"',
      );
      return json({ repositories: names.slice(0, 3) });
    }
    return json({ repositories: names.slice(3) });
  }
  if (path.endsWith("/tags/list"))
    return json({
      tags: deleted.has(path.slice(4, -10))
        ? []
        : ["latest", "v1.4.0", "v1.3.2"],
    });
  if (path.includes("/blobs/uploads/")) {
    let bytes = 0;
    for await (const chunk of req) bytes += chunk.length;
    res.setHeader(
      "Location",
      "http://127.0.0.1:5101/v2/acme/api/blobs/uploads/test?state=ok",
    );
    return json(
      {
        bytes,
        cookie: req.headers.cookie || "",
        auth: req.headers.authorization || "",
      },
      req.method === "POST" ? 202 : 201,
    );
  }
  if (path.includes("/manifests/")) {
    if (req.method === "DELETE") {
      deleted.add(path.slice(4, path.indexOf("/manifests/")));
      return json({}, 202);
    }
    if (path.endsWith("/manifests/oci-required")) {
      if (
        !(req.headers.accept || "").includes(
          "application/vnd.oci.image.index.v1+json",
        )
      )
        return json(
          {
            errors: [
              { code: "MANIFEST_UNKNOWN", message: "OCI index not accepted" },
            ],
          },
          404,
        );
      res.setHeader("Docker-Content-Digest", digest);
      res.setHeader("Content-Type", "application/vnd.oci.image.index.v1+json");
      if (req.method === "HEAD") return res.end();
      return json({
        schemaVersion: 2,
        mediaType: "application/vnd.oci.image.index.v1+json",
        manifests: [],
        received_accept: req.headers.accept,
      });
    }
    res.setHeader("Docker-Content-Digest", digest);
    if (req.method === "HEAD") {
      res.setHeader(
        "Content-Length",
        String(Buffer.byteLength(JSON.stringify(single))),
      );
      return res.end();
    }
    if (path.includes("public/alpine") && !path.includes("/manifests/sha256:"))
      return json({
        schemaVersion: 2,
        mediaType: "application/vnd.oci.image.index.v1+json",
        manifests: [
          { digest, platform: { os: "linux", architecture: "arm64" } },
          { digest, platform: { os: "linux", architecture: "amd64" } },
          {
            digest,
            platform: { os: "unknown", architecture: "unknown" },
            annotations: {
              "vnd.docker.reference.type": "attestation-manifest",
            },
          },
        ],
      });
    return json(single);
  }
  if (path.includes("/blobs/"))
    return json({
      created: "2026-11-01T08:30:00Z",
      os: "linux",
      architecture: "arm64",
    });
  json({ errors: [{ code: "NAME_UNKNOWN" }] }, 404);
});
server.listen(Number(process.env.MOCK_PORT || 5101), "127.0.0.1", () =>
  console.log("Fixture Registry listening"),
);
