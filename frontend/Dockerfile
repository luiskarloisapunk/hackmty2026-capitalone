# --- Etapa 1: Build ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json .
RUN npm ci --silent

COPY . .

# Sin VITE_API_URL a propósito: el build de producción usa rutas relativas
# (nginx proxea /api en el mismo origen). Ponerle "/api" aquí duplicaba el
# prefijo y todas las peticiones salían a /api/api/... con 404.

RUN npm run build

# --- Etapa 2: Serve con nginx ---
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
# Como template: el entrypoint de nginx corre envsubst al arrancar y
# resuelve ${BACKEND_HOST}. Solo sustituye variables que existan en el
# entorno, así que las de nginx ($host, $request_uri) quedan intactas.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
ENV BACKEND_HOST=backend

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
