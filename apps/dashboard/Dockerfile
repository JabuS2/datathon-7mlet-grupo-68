FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ARG NEXT_PUBLIC_API_SERVICE_URL
ARG NEXT_PUBLIC_AGENT_NAME
ENV NEXT_PUBLIC_API_SERVICE_URL=$NEXT_PUBLIC_API_SERVICE_URL \
    NEXT_PUBLIC_AGENT_NAME=$NEXT_PUBLIC_AGENT_NAME
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/package.json /app/package-lock.json* ./
RUN npm install --omit=dev
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/next.config.mjs ./next.config.mjs
EXPOSE 3000
CMD ["npm", "run", "start"]
