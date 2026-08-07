# NetPulse frontend (React build) served by nginx, which also reverse-proxies /api
# to the backend so the SPA can call the API on the same origin (LAN-friendly).
# Build context = repository root.

FROM node:20-alpine AS build
WORKDIR /app
ENV NODE_OPTIONS=--max-old-space-size=2048

COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile

COPY frontend/ ./
# Same-origin API: empty REACT_APP_BACKEND_URL => the app calls "/api" (proxied by nginx).
# .env.production.local has the highest precedence in CRA, so this wins over any baked .env.
RUN printf "REACT_APP_BACKEND_URL=\n" > .env.production.local
RUN yarn build

FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
