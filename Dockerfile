# DELIBERATELY INSECURE DOCKERFILE FOR AI HEALING TEST
FROM node:latest

# Running as root is a huge security risk
USER root

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Exposing a privileged or risky port
EXPOSE 80

CMD ["npm", "start"]
