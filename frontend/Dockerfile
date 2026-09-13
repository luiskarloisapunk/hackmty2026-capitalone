# --- Etapa 1: Build ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json .
RUN npm ci --silent

COPY . .

# Nginx proxea /api → backend, así que la URL base es relativa
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# --- Etapa 2: Serve con nginx ---
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
