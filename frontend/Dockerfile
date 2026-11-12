# ==============================================================================
# Chatrio Frontend — Production Next.js Dockerfile
# ==============================================================================
# Multi-stage Docker build utilizing Node.js 20 Alpine for lightweight,
# secure, and fast containerized execution.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependency Installation (deps)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS deps

# libc6-compat is often needed for Alpine compatibility with certain native npm packages
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy dependency manifests first to leverage Docker layer caching
COPY package.json package-lock.json ./

# Install exact dependencies using npm clean install
RUN npm ci


# ------------------------------------------------------------------------------
# Stage 2: Production Build (builder)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy cached node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy full application source code
COPY . .

# Set build-time environment variable to optimize Next.js compilation
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

# Compile the Next.js production build (.next directory)
RUN npm run build


# ------------------------------------------------------------------------------
# Stage 3: Lean Production Runtime (runner)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS runner

WORKDIR /app

# Production environment variables
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Create unprivileged system user and group for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application assets and production dependencies
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next

# Switch to the unprivileged user
USER nextjs

# Expose Next.js server port
EXPOSE 3000

# Health check to ensure frontend is responding
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Launch the Next.js production server
CMD ["npm", "start"]

