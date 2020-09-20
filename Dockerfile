FROM node:9-slim
WORKDIR /Backend
COPY package*.json /Backend/
RUN npm install
COPY . /Backend
EXPOSE 8080
 
CMD ["npm", "start"]