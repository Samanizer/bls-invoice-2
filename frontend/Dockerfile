## frontend/Dockerfile
## Multi-stage build:
##   Stage 1 (builder) — installs npm dependencies and builds the React app
##   Stage 2 (final)   — serves the static files via nginx
##
## The built files land in /usr/share/nginx/html.
## In production the Vite build writes to backend/static instead (see vite.config.js),
## so this Dockerfile is used when running the frontend as a standalone container.

FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
# Override outDir so build stays inside the container
RUN sed -i "s|'../backend/static'|'dist'|" vite.config.js
RUN npm run build

FROM nginx:stable-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
