# AI Research Assistant

A full-stack AI-powered research assistant that takes any research question, breaks it into sub-queries, searches the web, analyzes results, and generates a comprehensive markdown report — all in real-time.

Built as a portfolio project demonstrating professional-grade architecture: **Django + DRF** backend, **Next.js 16** frontend, **LangGraph** AI agent pipeline, **Celery** task queue, **WebSocket** real-time updates, **Redis** caching, **PostgreSQL**, and **Docker Compose** orchestration with **Nginx** reverse proxy.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [File-by-File Explanation](#file-by-file-explanation)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Commands Reference](#commands-reference)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [How It Works](#how-it-works)
- [Production Deployment](#production-deployment)

---

## Features

- **AI Research Pipeline**: 4-stage LangGraph agent (Plan → Search → Analyze → Format) using GPT-4o and Tavily web search
- **Real-time Updates**: WebSocket-powered live progress tracking as the AI processes your query
- **Smart Caching**: Identical questions return instant cached results (24-hour TTL) via Redis
- **JWT Authentication**: Secure register/login/logout flow with auto-refresh tokens
- **Research History**: Browse, tag, and delete past research queries from your dashboard
- **Responsive UI**: Modern interface built with shadcn/ui components and Tailwind CSS v4
- **Dockerized**: One command (`docker compose up`) to run the entire stack

---

## Tech Stack

### Backend (Python 3.13)

| Package                        | Version | Purpose                                      |
| ------------------------------ | ------- | -------------------------------------------- |
| Django                         | 5.1.4   | Web framework                                |
| djangorestframework            | 3.15.2  | REST API toolkit                             |
| djangorestframework-simplejwt  | 5.4.0   | JWT authentication (access + refresh tokens) |
| django-cors-headers            | 4.6.0   | Cross-origin request handling                |
| channels                       | 4.2.0   | WebSocket support for Django                 |
| channels-redis                 | 4.2.1   | Redis backend for Django Channels            |
| daphne                         | 4.1.2   | ASGI server (HTTP + WebSocket)               |
| celery                         | 5.4.0   | Distributed task queue                       |
| redis                          | 5.2.1   | Redis Python client                          |
| psycopg2-binary                | 2.9.10  | PostgreSQL database adapter                  |
| langchain                      | 0.3.14  | LLM framework                               |
| langchain-openai               | 0.3.0   | OpenAI integration for LangChain             |
| langgraph                      | 0.2.60  | Graph-based AI workflow orchestration        |
| tavily-python                  | 0.5.0   | Web search API client                        |
| gunicorn                       | 23.0.0  | Production WSGI server                       |
| python-dotenv                  | 1.0.1   | Environment variable loading                 |

### Frontend (Node 20)

| Package                  | Version | Purpose                              |
| ------------------------ | ------- | ------------------------------------ |
| next                     | 16.1.6  | React meta-framework (App Router)    |
| react                    | 19.2.3  | UI library                           |
| react-dom                | 19.2.3  | React DOM renderer                   |
| axios                    | 1.13.6  | HTTP client with interceptors        |
| react-markdown           | 10.1.0  | Render markdown reports              |
| lucide-react             | 0.576.0 | Icon library                         |
| class-variance-authority | 0.7.1   | Component variant styling (shadcn)   |
| clsx                     | 2.1.1   | Conditional class name utility       |
| tailwind-merge           | 3.5.0   | Merge Tailwind classes intelligently |
| sonner                   | 2.0.7   | Toast notification system            |
| tailwindcss              | 4.x     | Utility-first CSS framework (v4)     |
| typescript               | 5.x     | Static type checking                 |

### Infrastructure

| Service    | Image/Version    | Purpose                     |
| ---------- | ---------------- | --------------------------- |
| PostgreSQL | 16-alpine        | Primary database             |
| Redis      | 7-alpine         | Cache, message broker, channel layer |
| Nginx      | 1.27-alpine      | Reverse proxy & load balancer |
| Docker Compose | v2           | Container orchestration      |

---

## Architecture Overview

```
                         ┌──────────────┐
                         │   Browser    │
                         └──────┬───────┘
                                │ :80
                         ┌──────▼───────┐
                         │    Nginx     │
                         │ reverse proxy│
                         └──┬───────┬───┘
                   /api/    │       │  /
                   /ws/     │       │
                   /admin/  │       │
              ┌─────────────▼─┐  ┌──▼──────────┐
              │    Django     │  │   Next.js    │
              │  Daphne:8000  │  │  Dev:3000    │
              │  HTTP + WS    │  │  Frontend    │
              └──┬────────┬───┘  └─────────────┘
                 │        │
          ┌──────▼──┐  ┌──▼──────────┐
          │PostgreSQL│  │    Redis    │
          │  :5432   │  │   :6379    │
          └─────────┘  └──────┬──────┘
                              │
                       ┌──────▼──────┐
                       │   Celery    │
                       │   Worker    │
                       │  (LangGraph │
                       │   Agent)    │
                       └─────────────┘
```

**Request flow for a research query:**

1. User submits question → **Next.js** sends POST to `/api/research/`
2. **Django** checks Redis cache → if cache miss, dispatches **Celery** task → returns 202
3. **Celery worker** runs the **LangGraph** agent pipeline:
   - **Plan**: GPT-4o breaks question into 3-5 sub-queries
   - **Search**: Tavily searches each sub-query (advanced depth, 5 results each)
   - **Analyze**: GPT-4o synthesizes all search results
   - **Format**: GPT-4o writes structured markdown report
4. At each stage, Celery sends updates via **Django Channels** → **Redis channel layer** → **WebSocket** to the browser
5. Final result is saved to **PostgreSQL** and cached in **Redis** (24h TTL)
6. User sees real-time progress, then the full rendered report

---

## Project Structure

```
py-project/
├── README.md                          # This file
├── .env                               # Environment variables (gitignored)
├── .env.example                       # Environment template
├── .gitignore                         # Git ignore rules
├── docker-compose.yml                 # Docker orchestration (6 services)
│
├── backend/                           # Django + DRF backend
│   ├── Dockerfile                     # Python 3.13-slim container
│   ├── manage.py                      # Django CLI entry point
│   ├── requirements.txt               # Pinned Python dependencies
│   ├── __init__.py
│   │
│   ├── config/                        # Django project configuration
│   │   ├── __init__.py                # Exports Celery app
│   │   ├── settings.py                # All Django settings
│   │   ├── urls.py                    # Root URL routing
│   │   ├── asgi.py                    # ASGI app (HTTP + WebSocket)
│   │   ├── wsgi.py                    # WSGI app (fallback)
│   │   └── celery.py                  # Celery configuration
│   │
│   ├── accounts/                      # User authentication app
│   │   ├── __init__.py
│   │   ├── apps.py                    # App config
│   │   ├── models.py                  # Custom User model
│   │   ├── serializers.py             # Register & User serializers
│   │   ├── views.py                   # Register & Me endpoints
│   │   ├── urls.py                    # Auth URL patterns
│   │   └── admin.py                   # Admin registration
│   │
│   ├── research/                      # Research management app
│   │   ├── __init__.py
│   │   ├── apps.py                    # App config
│   │   ├── models.py                  # Tag, ResearchQuery, ResearchResult
│   │   ├── serializers.py             # List, Detail, Create serializers
│   │   ├── views.py                   # CRUD API + cache check
│   │   ├── urls.py                    # Research URL patterns
│   │   ├── tasks.py                   # Celery task (runs agent + WS updates)
│   │   ├── consumers.py               # WebSocket consumer
│   │   ├── middleware.py               # JWT auth middleware for WebSocket
│   │   ├── routing.py                 # WebSocket URL routing
│   │   └── admin.py                   # Admin registration
│   │
│   └── agent/                         # LangGraph AI research agent
│       ├── __init__.py
│       ├── graph.py                   # StateGraph definition & runner
│       ├── nodes.py                   # 4 pipeline nodes (plan/search/analyze/format)
│       ├── prompts.py                 # GPT-4o prompt templates
│       └── tools.py                   # Tavily web search client
│
├── frontend/                          # Next.js 16 + TypeScript frontend
│   ├── Dockerfile                     # Node 20-alpine + pnpm container
│   ├── package.json                   # Node dependencies
│   ├── pnpm-lock.yaml                 # Lockfile
│   ├── pnpm-workspace.yaml            # pnpm workspace config
│   ├── tsconfig.json                  # TypeScript config (path aliases)
│   ├── next.config.ts                 # Next.js config (standalone output)
│   ├── postcss.config.mjs             # PostCSS + Tailwind
│   ├── eslint.config.mjs              # ESLint config
│   ├── components.json                # shadcn/ui configuration
│   │
│   ├── app/                           # Next.js App Router pages
│   │   ├── layout.tsx                 # Root layout (AuthProvider + Toaster)
│   │   ├── page.tsx                   # Landing page (/)
│   │   ├── globals.css                # Tailwind v4 + shadcn CSS variables
│   │   ├── favicon.ico
│   │   │
│   │   ├── (auth)/                    # Auth route group
│   │   │   ├── layout.tsx             # Centered auth layout
│   │   │   ├── login/page.tsx         # Login form page
│   │   │   └── register/page.tsx      # Register form page
│   │   │
│   │   ├── dashboard/page.tsx         # Dashboard (form + research grid)
│   │   │
│   │   └── research/
│   │       └── [id]/page.tsx          # Research detail page (WebSocket)
│   │
│   ├── components/                    # React components
│   │   ├── navbar.tsx                 # Top navigation with user dropdown
│   │   ├── research-form.tsx          # Question submission form
│   │   ├── research-card.tsx          # Research history card
│   │   ├── research-detail.tsx        # Full research view + WS progress
│   │   │
│   │   └── ui/                        # shadcn/ui components (13 total)
│   │       ├── alert.tsx
│   │       ├── avatar.tsx
│   │       ├── badge.tsx
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── dialog.tsx
│   │       ├── dropdown-menu.tsx
│   │       ├── input.tsx
│   │       ├── separator.tsx
│   │       ├── skeleton.tsx
│   │       ├── sonner.tsx
│   │       ├── tabs.tsx
│   │       └── textarea.tsx
│   │
│   ├── lib/                           # Shared utilities
│   │   ├── utils.ts                   # cn() class merge helper
│   │   ├── api.ts                     # Axios client + JWT interceptors
│   │   ├── auth.tsx                   # AuthContext + AuthProvider
│   │   └── websocket.ts              # WebSocket client with reconnect
│   │
│   ├── types/
│   │   └── index.ts                   # TypeScript interfaces
│   │
│   └── public/                        # Static assets
│       ├── file.svg, globe.svg, next.svg, vercel.svg, window.svg
│
└── nginx/                             # Nginx reverse proxy
    ├── Dockerfile                     # Nginx 1.27-alpine
    └── nginx.conf                     # Routing rules
```

---

## File-by-File Explanation

### Root Files

#### `docker-compose.yml`
Orchestrates 6 services:
- **db** (PostgreSQL 16): Primary database with health check (`pg_isready`). Data persisted in a Docker volume.
- **redis** (Redis 7): Used for 3 purposes — Celery message broker, Django cache backend, and Channels WebSocket layer. Health check via `redis-cli ping`.
- **backend** (Django/Daphne): Runs migrations on startup, then starts the Daphne ASGI server on port 8000. Mounts `./backend` as a volume for live reload.
- **celery_worker**: Same image as backend, but runs `celery -A config worker` with concurrency=2. Processes research tasks asynchronously.
- **frontend** (Next.js): Runs `pnpm dev` on port 3000 with hot module replacement. Mounts `./frontend` but preserves container's `node_modules`.
- **nginx**: Reverse proxy on port 80. Routes traffic to backend or frontend based on URL path.

#### `.env` / `.env.example`
Environment variables for all services. The `.env` file is gitignored; `.env.example` is the template. Contains database credentials, Django secret key, Redis URL, and API keys for OpenAI and Tavily.

#### `.gitignore`
Ignores `__pycache__`, `node_modules`, `.next`, `.env`, `.venv`, `*.sqlite3`, IDE files, OS files, and the `.claude` directory.

---

### Backend — `config/`

#### `config/settings.py`
Central Django configuration:
- **Database**: PostgreSQL connection via environment variables
- **Cache**: `django.core.cache.backends.redis.RedisCache` — Django's built-in Redis cache backend
- **Channel Layers**: `channels_redis.core.RedisChannelLayer` — enables WebSocket group messaging
- **Celery**: Redis as broker and result backend, JSON serialization
- **DRF**: JWT as default authentication, `IsAuthenticated` as default permission, pagination at 20 items/page
- **SimpleJWT**: 30-minute access tokens, 7-day refresh tokens, rotation enabled with blacklisting
- **CORS**: Allows `localhost:3000`, `localhost:80`, `localhost`

#### `config/urls.py`
Root URL configuration with 3 paths:
- `admin/` → Django admin interface
- `api/auth/` → includes `accounts.urls` (register, login, refresh, me)
- `api/research/` → includes `research.urls` (CRUD + tags)

#### `config/asgi.py`
ASGI application entry point. Uses `ProtocolTypeRouter` to split traffic:
- **HTTP** requests → standard Django ASGI handler
- **WebSocket** connections → `JWTAuthMiddleware` → `URLRouter` with research WebSocket patterns

#### `config/celery.py`
Creates a Celery app named "config", loads settings from Django's `CELERY_*` namespace, and auto-discovers tasks from all installed apps (finds `research/tasks.py` automatically).

#### `config/__init__.py`
Exports the Celery app so Django loads it on startup. This ensures Celery's `@shared_task` decorator works and tasks are registered when Django boots.

---

### Backend — `accounts/`

#### `accounts/models.py`
Custom User model extending Django's `AbstractUser`. Currently identical to the default, but allows future customization (profile fields, etc.) without needing a database migration later. Uses `db_table = "users"`.

#### `accounts/serializers.py`
Two serializers:
- **RegisterSerializer**: Accepts `username`, `email`, `password` (write-only, min 8 chars). Uses `create_user()` to properly hash the password.
- **UserSerializer**: Read-only serializer returning `id`, `username`, `email`, `date_joined`.

#### `accounts/views.py`
Two views:
- **RegisterView** (`POST /api/auth/register/`): `AllowAny` permission. Creates a new user.
- **MeView** (`GET /api/auth/me/`): Returns the authenticated user's profile.

Login and token refresh are handled by SimpleJWT's built-in views (`TokenObtainPairView`, `TokenRefreshView`).

#### `accounts/urls.py`
Maps 4 URL patterns:
- `register/` → RegisterView
- `login/` → TokenObtainPairView (returns `access` + `refresh` tokens)
- `refresh/` → TokenRefreshView (rotates refresh token)
- `me/` → MeView

---

### Backend — `research/`

#### `research/models.py`
Three models:

**Tag**: Simple label with `name` (max 50 chars) and `user` foreign key. `unique_together` prevents duplicate tag names per user.

**ResearchQuery**: The core model.
- `user` (FK) — who submitted it
- `question` (TextField) — the research question
- `query_hash` (CharField, indexed) — SHA-256 hash of `question.strip().lower()`, used for cache lookups
- `status` (enum) — `pending` → `processing` → `completed` or `failed`
- `tags` (M2M to Tag)
- `celery_task_id` — tracks the background task
- Auto-generates `query_hash` on save if not set

**ResearchResult**: OneToOne with ResearchQuery.
- `summary` — the formatted markdown report
- `sources` (JSONField) — list of `{title, url, snippet}` objects
- `sub_queries` (JSONField) — list of sub-query strings the AI generated
- `raw_data` (JSONField) — stores the intermediate analysis text

#### `research/serializers.py`
Five serializers:
- **TagSerializer**: `id`, `name`
- **ResearchResultSerializer**: `id`, `summary`, `sources`, `sub_queries`, `created_at`
- **ResearchQueryListSerializer**: Lightweight — `id`, `question`, `status`, `tags`, `created_at`, `updated_at` (no result)
- **ResearchQueryDetailSerializer**: Full — includes nested `result` and `query_hash`
- **ResearchQueryCreateSerializer**: Input validation — `question` (10-1000 chars)

#### `research/views.py`
Five views:

**ResearchQueryCreateView** (`POST /api/research/`): The main endpoint.
1. Validates the question
2. Computes SHA-256 hash of the normalized question
3. Checks Redis cache with key `research:<hash>`
4. **Cache hit**: Creates query + result from cached data, returns **201** immediately
5. **Cache miss**: Creates query, dispatches `run_research_task.delay(query.id)`, saves task ID, returns **202**

**ResearchQueryListView** (`GET /api/research/list/`): Paginated list of the user's queries with tags.

**ResearchQueryDetailView** (`GET/DELETE /api/research/:id/`): Full query details with nested result, or delete.

**TagListView** (`GET /api/research/tags/`): All of the user's tags.

**ResearchQueryTagView** (`POST /api/research/:id/tags/`): Adds a tag to a query. Uses `get_or_create` to reuse existing tags.

#### `research/tasks.py`
The Celery task `run_research_task(query_id)`:
1. Loads the `ResearchQuery` from the database
2. Sets status to `processing`, sends WebSocket update
3. Runs `agent.graph.run_research()` with a callback that sends WebSocket updates at each stage:
   - `planning` → "Breaking down your question into sub-queries..."
   - `searching` → "Searching the web for information..."
   - `analyzing` → "Analyzing search results..."
   - `formatting` → "Formatting the final report..."
4. Creates a `ResearchResult` with the agent's output
5. Caches the result in Redis with 24-hour TTL
6. Sends final WebSocket update with `type: "result"`
7. On failure: sets status to `failed`, sends error WebSocket update, retries up to 2 times with 30-second delay

The `send_ws_update()` helper uses `async_to_sync(channel_layer.group_send)` to push messages to WebSocket groups from synchronous Celery code.

#### `research/consumers.py`
`ResearchConsumer` (AsyncJsonWebSocketConsumer):
- **connect()**: Extracts `query_id` from URL, verifies user is authenticated and owns the query, joins the channel group `research_{query_id}`
- **disconnect()**: Leaves the channel group
- **research_update()**: Receives group messages and forwards them to the WebSocket client as JSON

#### `research/middleware.py`
`JWTAuthMiddleware`: Extracts JWT from `?token=<jwt>` query parameter, validates it using SimpleJWT's `AccessToken`, and sets `scope["user"]`. Falls back to `AnonymousUser` on failure.

#### `research/routing.py`
Single WebSocket URL pattern: `ws/research/<query_id>/` → `ResearchConsumer`

---

### Backend — `agent/`

#### `agent/graph.py`
Defines the LangGraph workflow:
- **ResearchState** (TypedDict): Carries `question`, `sub_queries`, `search_results`, `sources`, `analysis`, `report`, and `stage` through the pipeline
- **build_graph()**: Creates a `StateGraph` with 4 nodes in sequence: `plan` → `search` → `analyze` → `format` → END
- **run_research()**: Compiles and streams the graph, calling `status_callback` at each node to report progress

#### `agent/nodes.py`
Four node functions, each takes state dict and returns updated state:

**plan_node**: Sends the question to GPT-4o with `PLAN_PROMPT`. Parses the JSON array response to get 3-5 sub-queries.

**search_node**: Iterates over sub-queries, calls `search_web()` for each (Tavily advanced search, max 5 results). Collects all results and deduplicates sources.

**analyze_node**: Formats all search results into text, sends to GPT-4o with `ANALYZE_PROMPT` for synthesis.

**format_node**: Takes the analysis and source list, sends to GPT-4o with `FORMAT_PROMPT` to generate the final markdown report with sections: Executive Summary, Key Findings, Detailed Analysis, Conclusions, Limitations.

#### `agent/prompts.py`
Three prompt templates:
- **PLAN_PROMPT**: Instructs GPT-4o to break a question into 3-5 specific search sub-queries, returning a JSON array
- **ANALYZE_PROMPT**: Instructs GPT-4o to synthesize search results, focusing on patterns, agreements/disagreements, and data points
- **FORMAT_PROMPT**: Instructs GPT-4o to write a structured report with 5 sections, using `[Source Title](url)` citation format

#### `agent/tools.py`
Thin wrapper around `TavilyClient`. The `search_web()` function calls `client.search()` with `search_depth="advanced"` for higher-quality results and `max_results=5` per query.

---

### Frontend — `app/`

#### `app/layout.tsx`
Root layout that wraps the entire app:
- Loads Geist Sans and Geist Mono fonts from Google Fonts
- Wraps children in `<AuthProvider>` for global auth state
- Includes `<Toaster />` from sonner for toast notifications
- Sets page metadata (title: "AI Research Assistant")

#### `app/globals.css`
Tailwind CSS v4 configuration:
- Imports `tailwindcss`
- Defines custom variant `dark` using `.dark` class
- Maps all shadcn/ui CSS variables (`--background`, `--foreground`, `--primary`, etc.) to Tailwind theme using `@theme inline`
- Light mode: white background, dark text, neutral color palette (oklch color space)
- Dark mode: dark background, light text, matching palette

#### `app/page.tsx` (Landing Page `/`)
- Redirects authenticated users to `/dashboard`
- Hero section with "Research Anything with AI" headline
- 3 feature cards: Deep Web Search, Real-time Updates, Cached Results
- CTA buttons to register/login
- Footer with project description

#### `app/(auth)/layout.tsx`
Route group layout for auth pages. Centers content vertically and horizontally with a subtle muted background. Max width 448px.

#### `app/(auth)/login/page.tsx`
Login form with username/password fields inside a shadcn Card component. On submit, calls `auth.login()`, displays errors in an Alert component. Links to register page.

#### `app/(auth)/register/page.tsx`
Registration form with username/email/password fields. On submit, calls `auth.register()` which auto-logs in after success. Links to login page.

#### `app/dashboard/page.tsx`
Protected page (redirects to `/login` if not authenticated):
- **Navbar** with user dropdown
- **ResearchForm** for submitting new questions
- **Research History** grid showing all past queries as cards
- Loads queries from `GET /api/research/list/`
- Supports deleting queries with optimistic UI update
- Shows skeleton loading states

#### `app/research/[id]/page.tsx`
Protected dynamic route for viewing a single research query:
- Back button to dashboard
- Renders `<ResearchDetail>` component with the query ID from the URL

---

### Frontend — `components/`

#### `components/navbar.tsx`
Top navigation bar:
- Left: "AI Research Assistant" link to dashboard
- Right: User avatar with dropdown menu showing email and logout option
- Uses shadcn DropdownMenu and Avatar components

#### `components/research-form.tsx`
Question input form:
- Textarea for the research question (min 10 characters)
- Submit button with loading state
- On submit: POST to `/api/research/`, then navigates to `/research/:id`
- Shows toast with "Cache hit!" (201) or "Research started!" (202)

#### `components/research-card.tsx`
Card component for the dashboard grid:
- Displays question text (2-line clamp), date, status badge with icon, tags
- Status icons: Clock (pending), Loader2 with spin animation (processing), CheckCircle (completed), XCircle (failed)
- Delete button with click event that stops link propagation
- Entire card is clickable, links to `/research/:id`

#### `components/research-detail.tsx`
Full research view with real-time updates:
1. **Fetches** query data from `GET /api/research/:id/`
2. **WebSocket**: If status is pending/processing, connects to `ws/research/:id/` to receive live updates
3. **Progress display**: Shows spinner with current stage message (e.g., "Searching the web...")
4. **Completed display**:
   - Rendered markdown report using `react-markdown`
   - Sub-queries list with numbered badges
   - Sources list with clickable external links and snippets
5. **Tag management**: Inline input to add tags, supports Enter key
6. **Loading/error states**: Skeleton placeholders while loading, error message on failure

---

### Frontend — `lib/`

#### `lib/utils.ts`
The `cn()` utility function that combines `clsx` and `tailwind-merge`. Used throughout shadcn/ui components to merge Tailwind classes without conflicts (e.g., `cn("p-4", className)` where `className` might override padding).

#### `lib/api.ts`
Axios instance configured for the backend API:
- **Base URL**: From `NEXT_PUBLIC_API_URL` env var (defaults to `http://localhost/api`)
- **Request interceptor**: Reads `access_token` from localStorage and adds `Authorization: Bearer <token>` header
- **Response interceptor**: On 401 error, attempts to refresh the token using the stored `refresh_token`. If refresh succeeds, retries the original request. If refresh fails, clears tokens and redirects to `/login`. Uses `_retry` flag to prevent infinite loops.

#### `lib/auth.tsx`
React Context providing authentication state:
- **State**: `user` (User object or null), `loading` (boolean)
- **fetchUser()**: Called on mount. If `access_token` exists in localStorage, calls `GET /api/auth/me/` to load the user profile.
- **login(username, password)**: POST to `/api/auth/login/`, stores tokens, fetches user, redirects to `/dashboard`
- **register(username, email, password)**: POST to `/api/auth/register/`, then calls `login()` automatically
- **logout()**: Clears tokens from localStorage, resets user state, redirects to `/login`
- **useAuth() hook**: Convenience hook that throws if used outside `<AuthProvider>`

#### `lib/websocket.ts`
`ResearchWebSocket` class for real-time research tracking:
- **Constructor**: Takes `queryId`, `onMessage` callback, optional `onClose` callback. Builds WebSocket URL with JWT token as query parameter.
- **connect()**: Creates WebSocket connection. On message, parses JSON and calls `onMessage`. On close, reconnects with exponential backoff (1s, 2s, 4s, 8s, 16s, up to 5 attempts).
- **disconnect()**: Sets max reconnect attempts to 0 and closes the socket (prevents reconnection).

---

### Frontend — `types/`

#### `types/index.ts`
TypeScript interfaces matching the backend API:
- **User**: `id`, `username`, `email`, `date_joined`
- **Tag**: `id`, `name`
- **ResearchSource**: `title`, `url`, `snippet`
- **ResearchResult**: `id`, `summary`, `sources`, `sub_queries`, `created_at`
- **ResearchQuery**: `id`, `question`, `query_hash`, `status` (union type), `tags`, optional `result`, `created_at`, `updated_at`
- **WSMessage**: WebSocket message type with `type` ("status" | "result"), `status`, `detail`, optional `data`

---

### Frontend — `components/ui/`

13 shadcn/ui components installed via `pnpm dlx shadcn@latest add`:

| Component      | Purpose                                                 |
| -------------- | ------------------------------------------------------- |
| alert          | Error messages on auth forms                            |
| avatar         | User initial in navbar                                  |
| badge          | Status indicators and tags                              |
| button         | All buttons (variants: default, ghost, destructive)     |
| card           | Research cards, form containers, report sections        |
| dialog         | Modal dialogs (available for future use)                |
| dropdown-menu  | User profile dropdown in navbar                         |
| input          | Text inputs on auth forms, tag input                    |
| separator      | Dividers between sources in research detail             |
| skeleton       | Loading placeholders on dashboard and detail page       |
| sonner         | Toast notifications (success/error messages)            |
| tabs           | Tab navigation (available for future use)               |
| textarea       | Research question input                                 |

---

### Nginx

#### `nginx/nginx.conf`
Reverse proxy with 5 location blocks:
- `/api/` → `backend:8000` — REST API requests with standard proxy headers
- `/admin/` → `backend:8000` — Django admin interface
- `/static/` → `backend:8000` — Django static files (CSS/JS for admin)
- `/ws/` → `backend:8000` — WebSocket upgrade with `Connection: "upgrade"`, 86400s read timeout (24 hours)
- `/` → `frontend:3000` — Next.js pages, also supports WebSocket upgrade for HMR (Hot Module Replacement) during development

---

## Prerequisites

- **Docker Desktop** v28+ with Docker Compose v2
- **OpenAI API key** (for GPT-4o)
- **Tavily API key** (for web search — get one free at [tavily.com](https://tavily.com))

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd py-project
```

### 2. Configure environment variables

```bash
# Copy the example env file
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-your-actual-openai-api-key
TAVILY_API_KEY=tvly-your-actual-tavily-api-key
```

Leave the other values as defaults for local development.

### 3. Start the application

```bash
docker compose up --build
```

This will:
1. Build 3 Docker images (backend, frontend, nginx)
2. Pull 2 Docker images (PostgreSQL 16, Redis 7)
3. Start all 6 services
4. Run Django database migrations automatically
5. Start the Next.js dev server with hot reload

Wait until you see logs from all services (especially `backend` showing "Daphne running" and `frontend` showing "Ready").

### 4. Access the application

- **Application**: http://localhost (via Nginx)
- **Frontend direct**: http://localhost:3000
- **Backend API direct**: http://localhost:8000/api/
- **Django Admin**: http://localhost/admin/

### 5. Create an account and start researching

1. Go to http://localhost/register
2. Create an account (username, email, password with 8+ chars)
3. You'll be auto-redirected to the dashboard
4. Type a research question and click "Research"
5. Watch real-time progress on the research detail page
6. View the completed report with sources and sub-queries

### 6. Stop the application

```bash
docker compose down
```

To also remove the database volume (deletes all data):

```bash
docker compose down -v
```

---

## Commands Reference

### Commands Used During Setup

| Command | Where to Run | What It Does |
|---------|-------------|-------------|
| `git init` | `py-project/` | Initialize git repository |
| `mv my-app frontend` | `py-project/` | Rename Next.js app directory |
| `pnpm install` | `frontend/` | Install Node.js dependencies from lockfile |
| `pnpm add axios lucide-react clsx tailwind-merge react-markdown` | `frontend/` | Add runtime dependencies |
| `pnpm add class-variance-authority` | `frontend/` | Add shadcn/ui dependency |
| `pnpm dlx shadcn@latest init -y -d` | `frontend/` | Initialize shadcn/ui with default settings |
| `pnpm dlx shadcn@latest add button input card badge textarea tabs alert dialog dropdown-menu avatar separator skeleton` | `frontend/` | Install shadcn/ui components |
| `pnpm dlx shadcn@latest add sonner` | `frontend/` | Install toast notification component |
| `npx tsc --noEmit` | `frontend/` | TypeScript type-check (no output files) |

### Docker Commands

| Command | What It Does |
|---------|-------------|
| `docker compose up --build` | Build images and start all 6 services |
| `docker compose up -d` | Start all services in detached (background) mode |
| `docker compose down` | Stop and remove all containers |
| `docker compose down -v` | Stop containers AND delete database volume |
| `docker compose logs backend` | View backend service logs |
| `docker compose logs -f celery_worker` | Follow Celery worker logs in real-time |
| `docker compose exec backend python manage.py createsuperuser` | Create a Django admin superuser |
| `docker compose exec backend python manage.py shell` | Open Django Python shell |
| `docker compose restart backend` | Restart only the backend service |

### Development Commands (run from `frontend/`)

| Command | What It Does |
|---------|-------------|
| `pnpm dev` | Start Next.js dev server on port 3000 |
| `pnpm build` | Create production build |
| `pnpm lint` | Run ESLint |
| `npx tsc --noEmit` | Type-check without building |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `research_db` | PostgreSQL database name |
| `POSTGRES_USER` | `research_user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `devpassword123` | PostgreSQL password |
| `DJANGO_SECRET_KEY` | `django-insecure-...` | Django secret key (change in production!) |
| `DJANGO_DEBUG` | `True` | Enable Django debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `OPENAI_API_KEY` | — | **Required.** Your OpenAI API key for GPT-4o |
| `TAVILY_API_KEY` | — | **Required.** Your Tavily API key for web search |
| `NEXT_PUBLIC_API_URL` | `http://localhost/api` | Backend API URL (used by frontend) |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost/ws` | WebSocket URL (used by frontend) |

---

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | No | Create new account. Body: `{username, email, password}` |
| POST | `/api/auth/login/` | No | Get JWT tokens. Body: `{username, password}`. Returns: `{access, refresh}` |
| POST | `/api/auth/refresh/` | No | Refresh access token. Body: `{refresh}`. Returns: `{access, refresh}` |
| GET | `/api/auth/me/` | Yes | Get current user profile |

### Research (`/api/research/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/research/` | Yes | Submit research question. Body: `{question}`. Returns 201 (cached) or 202 (processing) |
| GET | `/api/research/list/` | Yes | List user's research queries (paginated, 20/page) |
| GET | `/api/research/:id/` | Yes | Get research detail with result |
| DELETE | `/api/research/:id/` | Yes | Delete a research query |
| POST | `/api/research/:id/tags/` | Yes | Add tag to query. Body: `{name}` |
| GET | `/api/research/tags/` | Yes | List user's tags |

### WebSocket

| URL | Auth | Description |
|-----|------|-------------|
| `ws://localhost/ws/research/:id/?token=<jwt>` | Yes (query param) | Real-time research progress updates |

WebSocket message format:
```json
// Status update (during processing)
{"type": "status", "status": "planning|searching|analyzing|formatting", "detail": "..."}

// Final result
{"type": "result", "status": "completed", "detail": "Research complete!", "data": {"summary": "...", "sources": [...], "sub_queries": [...]}}

// Error
{"type": "status", "status": "failed", "detail": "Error message"}
```

---

## How It Works

### Authentication Flow

1. User registers → backend creates user, frontend auto-calls login
2. Login → backend returns JWT `access` (30min) + `refresh` (7 days) tokens
3. Frontend stores both in `localStorage`
4. Every API request → Axios interceptor adds `Authorization: Bearer <access>` header
5. On 401 → interceptor automatically calls `/api/auth/refresh/` with the refresh token
6. If refresh succeeds → retries original request with new token
7. If refresh fails → clears tokens, redirects to `/login`

### Research Flow

1. **Submit**: User types question → `POST /api/research/` with JWT
2. **Cache Check**: Backend hashes `question.strip().lower()` with SHA-256, checks Redis key `research:<hash>`
3. **Cache Hit (201)**: Creates ResearchQuery + ResearchResult from cached data, returns immediately
4. **Cache Miss (202)**: Creates ResearchQuery with status `pending`, dispatches Celery task, returns task ID
5. **Frontend**: Navigates to `/research/:id`, connects WebSocket to `ws/research/:id/?token=<jwt>`
6. **Celery Task**:
   - Sets status to `processing`, sends WS update
   - **Plan node**: GPT-4o generates 3-5 sub-queries → WS: "Breaking down your question..."
   - **Search node**: Tavily searches each sub-query → WS: "Searching the web..."
   - **Analyze node**: GPT-4o synthesizes results → WS: "Analyzing search results..."
   - **Format node**: GPT-4o writes markdown report → WS: "Formatting the final report..."
7. **Save**: Creates ResearchResult in PostgreSQL
8. **Cache**: Stores result in Redis with 24-hour TTL
9. **Notify**: Sends final WS message with `type: "result"`
10. **Display**: Frontend receives result, re-fetches query, renders markdown report

### Caching Strategy

- **Key format**: `research:<sha256(question.strip().lower())>`
- **TTL**: 86400 seconds (24 hours)
- **On submit**: View checks cache before dispatching task
- **On complete**: Task caches the result after saving to database
- **Effect**: Same question from any user returns instant 201 response with cached data

---

## Production Deployment

### Environment Changes

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generate-a-strong-random-key>
POSTGRES_PASSWORD=<strong-random-password>
DJANGO_ALLOWED_HOSTS=yourdomain.com
```

### Steps

1. **Generate a Django secret key**:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Update CORS** in `backend/config/settings.py`:
   ```python
   CORS_ALLOWED_ORIGINS = ["https://yourdomain.com"]
   ```

3. **Update frontend env vars**:
   ```env
   NEXT_PUBLIC_API_URL=https://yourdomain.com/api
   NEXT_PUBLIC_WS_URL=wss://yourdomain.com/ws
   ```

4. **Add SSL to Nginx** — add an `ssl` server block to `nginx.conf` with your certificate, or use a service like Cloudflare or Let's Encrypt with certbot.

5. **Collect static files**:
   ```bash
   docker compose exec backend python manage.py collectstatic --noinput
   ```

6. **Build production frontend**: Update `frontend/Dockerfile` to run `pnpm build` and serve with `pnpm start` instead of `pnpm dev`.

7. **Deploy** on any Docker-compatible platform: AWS ECS, DigitalOcean App Platform, Railway, Fly.io, or a VPS with Docker installed.

---

## License

This project is a portfolio demonstration. Feel free to use it as a reference or starting point for your own projects.
