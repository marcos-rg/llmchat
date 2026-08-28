# Dev-mode image: the container runs the Vite dev server, not a static build, so
# HMR works against the ./frontend bind mount declared in docker-compose.yml.
FROM node:22-alpine

# curl is only here for the Compose healthcheck (`curl -f localhost:5173`);
# busybox wget would work but reports a different exit code on HTTP errors.
RUN apk add --no-cache curl

WORKDIR /app

# Dependencies are installed into the image, and docker-compose.yml mounts an
# anonymous volume over /app/node_modules so the host bind mount cannot shadow
# them. Copying only the manifests first keeps this layer cached across source
# edits.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]
