FROM node:20.18.1-alpine3.20 AS build

WORKDIR /home/node/app

RUN chown node:node /home/node/app

USER node

COPY --chown=node:node package*.json ./

RUN npm ci --omit=dev --ignore-scripts && npm cache clean --force

FROM node:20.18.1-alpine3.20 AS runner

RUN apk update && apk upgrade && \
    apk add --no-cache tini && \
    rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx /opt/yarn* /usr/local/bin/yarn /usr/local/bin/yarnpkg

WORKDIR /home/node/app

RUN chown node:node /home/node/app

USER node

ENV NODE_ENV=production
ENV PORT=3000

COPY --chown=node:node . .
COPY --chown=node:node --from=build /home/node/app/node_modules ./node_modules

EXPOSE 3000

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["node", "."]