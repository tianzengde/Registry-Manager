# The Nuxt output contains JavaScript only; build it natively once for both runtimes.
FROM --platform=$BUILDPLATFORM node:24-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:24-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production HOST=0.0.0.0 PORT=8000 NUXT_DATABASE_PATH=/app/db/registry_manager.db
COPY --from=builder --chown=node:node /app/.output ./.output
RUN mkdir -p /app/db && chown node:node /app/db
USER node
EXPOSE 8000
CMD ["node", ".output/server/index.mjs"]
