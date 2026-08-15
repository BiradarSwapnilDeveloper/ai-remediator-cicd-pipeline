FROM node:20.18.1-alpine3.20 AS build

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm ci --omit=dev && npm cache clean --force

FROM node:20.18.1-alpine3.20

RUN apk update && apk upgrade && apk add --no-cache tini

WORKDIR /usr/src/app

ENV NODE_ENV=production

COPY --from=build /usr/src/app/node_modules ./node_modules
COPY . .

USER node

EXPOSE 3000

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["node", "."]