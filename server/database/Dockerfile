FROM node:24-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY --chown=node:node app.js dealership.js review.js ./
COPY --chown=node:node data ./data
USER node
EXPOSE 3030
CMD ["node", "app.js"]
