# Sovereign AI Arsenal Frontend

A modern, production-ready Next.js 14 dashboard for the Sovereign AI Arsenal platform.

## Features

- 🚀 **Next.js 14** with App Router
- 🎨 **Modern UI** with Tailwind CSS and Framer Motion
- 📊 **Rich Visualizations** with Recharts
- 🔍 **Semantic Search** integration
- 🏗️ **Sandbox Results** display
- 📱 **Responsive Design** for all devices
- ⚡ **TypeScript** for type safety
- 🔧 **Production Ready** with optimized builds

## Quick Start

1. **Install dependencies**:
```bash
npm install
# or
yarn install
```

2. **Set up environment variables**:
```bash
cp .env.example.local .env.local
```

3. **Run development server**:
```bash
npm run dev
# or
yarn dev
```

4. **Open [http://localhost:3000](http://localhost:3000)**

## Environment Variables

Create a `.env.local` file in the root directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── globals.css        # Global styles
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   └── dashboard/         # Dashboard pages
│   ├── components/            # Reusable UI components
│   │   ├── ui/               # Base UI components
│   │   ├── search/           # Search components
│   │   ├── trending/         # Trending tools
│   │   ├── filters/          # Filter components
│   │   ├── stats/            # Statistics
│   │   ├── sandbox/          # Sandbox results
│   │   ├── charts/           # Chart components
│   │   └── providers/        # Context providers
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utility functions
│   ├── services/              # API services
│   └── types/                 # TypeScript types
├── public/                    # Static assets
├── package.json
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── README.md
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Components

### Core Components

- **SearchBar** - Semantic search with suggestions
- **TrendingTools** - Display trending AI repositories
- **CategoryFilter** - Filter by AI categories
- **StatsCards** - Platform statistics overview
- **SandboxResults** - Detailed sandbox analysis results

### Chart Components

- **TrendChart** - Repository trends over time
- **CategoryChart** - Category distribution visualization

### UI Components

- **Button** - Styled button with variants
- **Card** - Container component
- **Badge** - Status and category badges
- **Tabs** - Tabbed navigation

## API Integration

The frontend connects to the FastAPI backend through:

- **Repository API** - Fetch repositories, details, analysis
- **Search API** - Semantic and keyword search
- **Category API** - Category information
- **Trending API** - Trending repositories
- **Statistics API** - Platform statistics

## Styling

- **Tailwind CSS** for utility-first styling
- **Framer Motion** for animations
- **Dark mode** support
- **Responsive design** with mobile-first approach

## State Management

- **TanStack Query** for server state
- **React Query** for data fetching and caching
- **Zustand** for client state (when needed)

## Performance Optimizations

- **Image optimization** with Next.js Image component
- **Code splitting** with dynamic imports
- **Caching strategies** for API calls
- **Bundle optimization** for production builds

## Production Deployment

### Build for Production

```bash
npm run build
```

### Start Production Server

```bash
npm run start
```

### Docker Deployment

```dockerfile
FROM node:18-alpine AS base
WORKDIR /app

FROM base AS deps
COPY package.json package-lock.json* ./
RUN npm ci

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./.next/standalone
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.