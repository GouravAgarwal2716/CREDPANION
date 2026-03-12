FROM node:18-alpine

WORKDIR /app

# Enable corepack for modern package manager support if needed
RUN corepack enable || true

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Build the Next.js app
RUN npm run build

# Expose Next.js port
EXPOSE 3000

# Start Next.js in production mode
CMD ["npm", "start"]
