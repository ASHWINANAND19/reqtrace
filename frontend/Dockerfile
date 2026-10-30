# Build stage: compile the React app
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# Runtime stage: nginx serves the SPA, terminates TLS and proxies /api to the back end
FROM nginx:1.27-alpine
RUN apk add --no-cache openssl && rm -f /etc/nginx/conf.d/default.conf
ENV BACKEND_URL=http://backend:8000
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY nginx/05-selfsigned-cert.sh /docker-entrypoint.d/05-selfsigned-cert.sh
RUN chmod +x /docker-entrypoint.d/05-selfsigned-cert.sh
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80 443
