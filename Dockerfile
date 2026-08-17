FROM node:20.18.1-alpine3.20 AS build

USER node
WORKDIR /home/node/app

COPY --chown=node:node package*.json ./

RUN npm ci --omit=dev && npm cache clean --force

FROM node:20.18.1-alpine3.20

RUN apk update && apk upgrade && apk add --no-cache tini

USER node
WORKDIR /home/node/app

ENV NODE_ENV=production

COPY --chown=node:node . .
COPY --chown=node:node --from=build /home/node/app/node_modules ./node_modules

EXPOSE 3000

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["node", "."]