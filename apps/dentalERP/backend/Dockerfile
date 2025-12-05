FROM node:20-bullseye-slim AS builder

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 make g++ \
  && rm -rf /var/lib/apt/lists/*

COPY package*.json ./
RUN npm ci --include=dev

COPY tsconfig.json ./tsconfig.json
COPY drizzle.config.ts ./drizzle.config.ts
COPY src ./src
COPY docs ./docs

RUN npm run build \
  && npm prune --omit=dev

FROM node:20-bullseye-slim

ENV NODE_ENV=production
WORKDIR /app

COPY package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/docs ./docs

EXPOSE 3001
CMD ["node", "dist/server.js"]
