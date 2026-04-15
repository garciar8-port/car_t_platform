# Stage 1 — build
FROM node:20-alpine AS build

RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || pnpm install

COPY . .
RUN pnpm build

# Stage 2 — serve with Express (handles SPA routing + access code API)
FROM node:20-alpine

WORKDIR /app

COPY --from=build /app/dist ./dist
COPY server.js package.json ./
RUN npm install --no-save express

EXPOSE 8080

CMD ["node", "server.js"]
