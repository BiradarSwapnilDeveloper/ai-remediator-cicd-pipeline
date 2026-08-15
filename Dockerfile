FROM node:20.18.1-alpine3.20 AS build

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm ci --omit=dev && npm cache clean --force

FROM node:20.18.1-alpine3.20

RUN apk update && apk upgrade && apk add --no-cache tini

WORKDIR /usr/src/app

RUN chown node:node /usr/src/app

USER node

ENV NODE_ENV=production

COPY --chown=node:node . .
COPY --chown=node:node --from=build /usr/src/app/node_modules ./node_modules

EXPOSE 3000

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["node", "."]