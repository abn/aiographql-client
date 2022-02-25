FROM docker.io/node:16-alpine

COPY package.json yarn.lock /app/

WORKDIR /app

RUN yarn install

COPY index.js /app/

ENTRYPOINT ["yarn", "run", "start"]

EXPOSE 4000/tcp
