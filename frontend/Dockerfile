# Use a lightweight Node.js base image
FROM node:18-alpine

# Set working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json first for Docker layer caching
COPY package*.json ./

# Install dependencies without breaking due to peer deps
RUN npm install --legacy-peer-deps

# Copy the rest of the application source code
COPY . .

# Expose the port React dev server runs on
EXPOSE 3000

# Start the React development server
CMD ["npm", "start"]
