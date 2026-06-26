# SPDX-License-Identifier: AGPL-3.0-or-later
FROM node:22-alpine AS base
WORKDIR /app
RUN npm install -g pnpm@9

# ── deps ──────────────────────────────────────────────────────────────────────
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# ── development ───────────────────────────────────────────────────────────────
FROM deps AS development
COPY . .
EXPOSE 3000
CMD ["pnpm", "dev"]

# ── builder ───────────────────────────────────────────────────────────────────
FROM deps AS builder
COPY . .
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL}
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

# ── production ────────────────────────────────────────────────────────────────
FROM node:22-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
