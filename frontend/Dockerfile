# frontend/Dockerfile

FROM node:24-alpine

# Set working directory
WORKDIR /app

# Copy package.json and lockfile first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app
COPY . .

# Expose port for dev server
EXPOSE 3000

# Run dev server (hot reload, etc.)
CMD ["npm", "run", "dev"]
