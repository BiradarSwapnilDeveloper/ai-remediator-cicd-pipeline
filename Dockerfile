FROM node:20.18.1-alpine3.20 AS build

WORKDIR /usr/src/app

USER node

COPY --chown=node:node package*.json ./

RUN npm ci --omit=dev --ignore-scripts && npm cache clean --force

FROM node:20.18.1-alpine3.20 AS runner

ENV NODE_ENV=production
ENV PORT=3000

RUN apk update && apk upgrade --no-cache && \
    apk add --no-cache tini && \
    rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx /opt/yarn* /usr/local/bin/yarn /usr/local/bin/yarnpkg

WORKDIR /usr/src/app

COPY --chown=node:node --from=build /usr/src/app/node_modules ./node_modules
COPY --chown=node:node . .

USER node

EXPOSE 3000

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["node", "."]