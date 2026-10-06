FROM node:24-alpine AS build
WORKDIR /app/frontend
ENV BACKEND_API_ORIGIN=http://backend:8000
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
COPY widget/src/bidachat-widget.js /app/widget/src/bidachat-widget.js
COPY widget/example/dashboard.html /app/widget/example/dashboard.html
RUN npm run lint && npm run test && npm run build

FROM node:24-alpine
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
WORKDIR /app/frontend
COPY --from=build --chown=node:node /app/frontend/.next/standalone ./
COPY --from=build --chown=node:node /app/frontend/.next/static ./.next/static
COPY --from=build --chown=node:node /app/frontend/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
