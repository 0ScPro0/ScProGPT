# ScProGPT — Multi-Provider AI Chat Platform

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Async-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ScProGPT** is a full-stack, multi-provider AI chat platform that unifies access to multiple large language model (LLM) providers — including **OpenAI**, **OpenRouter**, **Anthropic (Claude)**, and **Google (Gemini)** — under a single, modern web interface. Users can seamlessly switch between AI providers and models within a conversation, with support for both synchronous and streaming (SSE) text generation.

---

## Table of Contents

- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
  - [Backend](#backend)
  - [Frontend](#frontend)
  - [DevOps & Tooling](#devops--tooling)
- [Architecture Overview](#architecture-overview)
  - [Backend Architecture](#backend-architecture)
  - [Frontend Architecture](#frontend-architecture)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [License](#license)

---

## Key Features

- **🤖 Multi-Provider AI Integration** — Unified access to OpenAI, OpenRouter, Anthropic (Claude), and Google (Gemini) through a single API. Provider architecture is designed for easy extensibility.
- **🔄 Dynamic Provider & Model Switching** — Change the AI provider and model on the fly per chat conversation without losing context.
- **⚡ Streaming & Non-Streaming Generation** — Support for both real-time Server-Sent Events (SSE) streaming and traditional full-response generation.
- **🔐 JWT Authentication** — Secure sign-up, sign-in, and token refresh flow with access/refresh token pair and bcrypt password hashing.
- **💬 Full Chat Management** — Create, delete, rename chats with per-chat provider/model settings, system prompts, and token usage tracking.
- **🌗 Dark/Light Theme** — Client-side theme persistence with instant toggling.
- **📊 Token Usage & Cost Tracking** — Per-message tracking of prompt/completion tokens and estimated cost.
- **🧪 Comprehensive Test Suite** — Unit, integration, and mock-based tests for services, database CRUD, and security.

---

## Tech Stack

### Backend

| Category          | Technology                                                                 |
| ----------------- | -------------------------------------------------------------------------- |
| **Framework**     | [FastAPI](https://fastapi.tiangolo.com) 0.128                              |
| **Language**      | [Python](https://python.org) 3.13+                                         |
| **ORM**           | [SQLAlchemy](https://www.sqlalchemy.org) 2.0 (async)                       |
| **Migrations**    | [Alembic](https://alembic.sqlalchemy.org) 1.18                             |
| **Database**      | [PostgreSQL](https://www.postgresql.org) (async via `asyncpg`) / SQLite    |
| **Auth**          | [PyJWT](https://pyjwt.readthedocs.io) + [Passlib](https://passlib.readthedocs.io) (bcrypt) |
| **AI SDKs**       | [OpenAI Python SDK](https://pypi.org/project/openai/) 2.16, [Anthropic SDK](https://pypi.org/project/anthropic/) 0.77 |
| **Validation**    | [Pydantic](https://docs.pydantic.dev) 2.12 + Pydantic-Settings            |
| **Server**        | [Uvicorn](https://www.uvicorn.org) 0.40                                    |
| **Config**        | YAML-based model definitions, environment-based settings                   |
| **Testing**       | [pytest](https://docs.pytest.org) 9.0 + pytest-asyncio                     |
| **API Docs**      | Auto-generated Swagger UI (dark theme via `fastapi-swagger-dark`)          |

### Frontend

| Category          | Technology                                                                 |
| ----------------- | -------------------------------------------------------------------------- |
| **Framework**     | [React](https://react.dev) 19                                              |
| **Routing**       | [React Router](https://reactrouter.com) 7                                  |
| **State Mgmt**    | [Zustand](https://github.com/pmndrs/zustand) 5 (with `persist` middleware) |
| **HTTP Client**   | [Axios](https://axios-http.com) 1.13 (with interceptors for JWT refresh)   |
| **Styling**       | CSS Modules (`.module.css`)                                                |
| **Build Tool**    | Create React App (react-scripts 5)                                         |

### DevOps & Tooling

| Category          | Technology                                                                 |
| ----------------- | -------------------------------------------------------------------------- |
| **Package Mgmt**  | [Poetry](https://python-poetry.org) (Python) / npm (Node.js)               |
| **Formatting**    | [Black](https://github.com/psf/black) 26                                   |
| **Migrations**    | Alembic CLI with auto-generated revision scripts                           |

---

## Architecture Overview

### Backend Architecture

The backend follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Auth    │  │  Chats   │  │ Messages │  │  Users   │ │
│  │ Endpoint │  │ Endpoint │  │ Endpoint │  │ Endpoint │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │              │              │              │       │
│  ┌────▼──────────────▼──────────────▼──────────────▼─────┐ │
│  │                   Service Layer                        │ │
│  │  AuthService │ ChatService │ MessageService │ AIService│ │
│  └────┬──────────────┬──────────────┬────────────────────┘ │
│       │              │              │                       │
│  ┌────▼──────────────▼──────────────▼─────────────────────┐ │
│  │              Data Access Layer (CRUD)                   │ │
│  │         user_crud │ chat_crud │ message_crud            │ │
│  └──────────────────────┬─────────────────────────────────┘ │
│                         │                                    │
│  ┌──────────────────────▼─────────────────────────────────┐ │
│  │              Database (PostgreSQL / SQLite)              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              AI Provider Manager                         │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │ │
│  │  │  OpenAI  │ │OpenRouter│ │ Anthropic│ │  Google  │   │ │
│  │  │ Provider │ │ Provider │ │ Provider │ │ Provider │   │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**

- **Abstract Provider Pattern** — All AI providers extend [`BaseProvider`](backend/src/services/ai/providers/base_provider.py:12) which defines a common interface (`generate_text`, `generate_stream`). Adding a new provider requires only implementing this interface.
- **Provider Manager** — [`ProviderManager`](backend/src/services/ai/manager.py:41) handles provider/model resolution, validation, and switching. It acts as a registry and routing layer.
- **Service Layer** — Business logic is encapsulated in service classes ([`AIService`](backend/src/services/ai/service.py:25), [`AuthService`](backend/src/services/auth.py), [`ChatService`](backend/src/services/chat.py), [`MessageService`](backend/src/services/message.py)), keeping endpoints thin.
- **Async-First** — The entire stack is asynchronous: `asyncpg` for PostgreSQL, `AsyncOpenAI` for AI clients, and async SQLAlchemy sessions.
- **JWT Dual-Token Auth** — Short-lived access tokens (30 min) + long-lived refresh tokens (30 days) with automatic token refresh on the frontend via Axios interceptors.

### Frontend Architecture

The frontend is a **single-page application (SPA)** built with React 19:

```
┌─────────────────────────────────────────────────────────┐
│                    React Application                      │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                  Pages                                │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │ │
│  │  │   Home   │  │   Auth   │  │ ChatPage │           │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘           │ │
│  └───────┼──────────────┼─────────────┼─────────────────┘ │
│          │              │              │                   │
│  ┌───────▼──────────────▼──────────────▼─────────────────┐ │
│  │              Components                                │ │
│  │  Sidebar │ Header │ Chat │ InputField │ Message        │ │
│  │  Topbar  │ Button │ Field │ Logo │ SVGIcon             │ │
│  └──────────────────────┬────────────────────────────────┘ │
│                         │                                   │
│  ┌──────────────────────▼────────────────────────────────┐ │
│  │              State Management (Zustand)                │ │
│  │  ┌──────────────┐  ┌──────────────┐                   │ │
│  │  │  authStore   │  │  themeStore  │                   │ │
│  │  └──────┬───────┘  └──────┬───────┘                   │ │
│  └─────────┼─────────────────┼───────────────────────────┘ │
│            │                 │                              │
│  ┌─────────▼─────────────────▼───────────────────────────┐ │
│  │              API Layer (Axios)                         │ │
│  │  auth.js │ chat.js │ message.js │ models.js │ user.js  │ │
│  │  client.js (base config + interceptors)                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**

- **Zustand for State** — Lightweight state management with `persist` middleware for auth tokens and theme preference.
- **Axios Interceptors** — Automatic `Authorization` header injection and transparent 401 → token refresh → retry flow.
- **CSS Modules** — Scoped styling per component to avoid class name collisions.
- **Custom Hooks** — [`useChat`](frontend/src/hooks/useChat.js) encapsulates chat logic (message list, typing simulation, input handling). [`useAuth`](frontend/src/hooks/useAuth.js) handles auth initialization and redirect.

---

## API Endpoints

| Method | Endpoint                                    | Description                        |
| ------ | ------------------------------------------- | ---------------------------------- |
| POST   | `/api/v1/auth/signup`                       | Register a new user                |
| POST   | `/api/v1/auth/signin`                       | Authenticate user                  |
| POST   | `/api/v1/auth/refresh`                      | Refresh access token               |
| POST   | `/api/v1/auth/logout`                       | Logout user                        |
| POST   | `/api/v1/chats/create`                      | Create a new chat                  |
| GET    | `/api/v1/chats/user`                        | Get all user chats                 |
| GET    | `/api/v1/chats/{chat_id}`                   | Get chat by ID                     |
| DELETE | `/api/v1/chats/{chat_id}/delete`            | Delete chat                        |
| PATCH  | `/api/v1/chats/{chat_id}/update/provider`   | Update chat AI provider            |
| PATCH  | `/api/v1/chats/{chat_id}/update/model`      | Update chat AI model               |
| PATCH  | `/api/v1/chats/{chat_id}/update/title`      | Update chat title                  |
| GET    | `/api/v1/chats/{chat_id}/provider`          | Get provider status                |
| POST   | `/api/v1/assistant/create/text`             | Generate text (non-streaming)      |
| POST   | `/api/v1/assistant/create/text/stream`      | Generate text (SSE streaming)      |
| GET    | `/api/v1/users/me`                          | Get current user profile           |
| PATCH  | `/api/v1/users/me`                          | Update current user profile        |

Full interactive API documentation is available at `/docs` (Swagger UI with dark theme).

---

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL 15+ (or SQLite for development)
- Poetry (`pip install poetry`)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/scprogpt.git
cd scprogpt

# 2. Backend setup
cd backend
poetry install
poetry run alembic upgrade head
poetry run python src/main.py

# 3. Frontend setup (in a new terminal)
cd frontend
npm install
npm start
```

### Configuration

Backend configuration is managed via environment variables or a `.env` file in the `backend/` directory:

| Variable                          | Description                          | Default                        |
| --------------------------------- | ------------------------------------ | ------------------------------ |
| `SERVER__HOST`                    | Server host                          | `0.0.0.0`                     |
| `SERVER__PORT`                    | Server port                          | `8000`                        |
| `DATABASE__URL`                   | Database connection string           | `sqlite+aiosqlite:///./dev.db` |
| `SECURITY__SECRET_KEY`            | JWT signing secret                   | *(required)*                   |
| `SECURITY__ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL              | `30`                           |
| `SECURITY__REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token TTL             | `30`                           |
| `AI__API_KEY`                     | AI provider API key                  | *(required)*                   |
| `AI__BASE_URL`                    | AI provider base URL                 | `https://api.proxyapi.ru/`     |
| `AI__DEFAULT_PROVIDER`            | Default AI provider                  | `openai`                       |
| `AI__DEFAULT_MODEL`               | Default AI model                     | `gpt-4o-mini`                  |

---

## Project Structure

```
scprogpt/
├── backend/
│   ├── alembic/                  # Database migrations
│   │   └── versions/             # Migration revision scripts
│   ├── src/
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── api/
│   │   │   ├── dependencies.py   # FastAPI dependency injection
│   │   │   └── v1/
│   │   │       ├── router.py     # API v1 router aggregation
│   │   │       └── endpoints/    # Route handlers
│   │   │           ├── auth.py
│   │   │           ├── chats.py
│   │   │           ├── users.py
│   │   │           └── messages/
│   │   │               ├── assistant.py
│   │   │               ├── messages.py
│   │   │               └── user.py
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic-based settings
│   │   │   ├── exceptions.py     # Custom exception classes
│   │   │   ├── security.py       # JWT + password hashing
│   │   │   └── ai/
│   │   │       ├── models.py     # YAML model loader
│   │   │       ├── openai.yaml   # OpenAI model definitions
│   │   │       └── openrouter.yaml
│   │   ├── database/
│   │   │   ├── database.py       # Async engine + session factory
│   │   │   ├── models/           # SQLAlchemy ORM models
│   │   │   │   ├── base.py
│   │   │   │   ├── user.py
│   │   │   │   ├── chat.py
│   │   │   │   └── message.py
│   │   │   └── crud/             # Data access layer
│   │   │       ├── base.py
│   │   │       ├── chat.py
│   │   │       ├── message.py
│   │   │       └── user.py
│   │   ├── schemas/              # Pydantic request/response models
│   │   │   ├── ai.py
│   │   │   ├── auth.py
│   │   │   ├── base.py
│   │   │   ├── chat.py
│   │   │   ├── message.py
│   │   │   └── user.py
│   │   ├── services/             # Business logic layer
│   │   │   ├── auth.py
│   │   │   ├── base.py
│   │   │   ├── chat.py
│   │   │   ├── message.py
│   │   │   ├── user.py
│   │   │   └── ai/
│   │   │       ├── manager.py    # ProviderManager
│   │   │       ├── service.py    # AIService
│   │   │       └── providers/    # AI provider implementations
│   │   │           ├── base_provider.py
│   │   │           ├── openai_provider.py
│   │   │           ├── openrouter_provider.py
│   │   │           ├── anthropic_provider.py
│   │   │           └── google_provider.py
│   │   └── utils/
│   │       ├── logger.py
│   │       └── serializator.py
│   └── tests/                    # Test suite
│       ├── conftest.py
│       ├── fixtures/
│       ├── integration/
│       ├── mocks/
│       └── unit/
├── frontend/
│   ├── public/
│   └── src/
│       ├── App.js                # Root component with routing
│       ├── index.js              # Entry point
│       ├── components/
│       │   ├── chat/             # Chat UI components
│       │   │   ├── Chat/
│       │   │   ├── InputField/
│       │   │   └── Message/
│       │   ├── layout/           # Layout components
│       │   │   ├── Header/
│       │   │   └── Sidebar/
│       │   └── ui/common/        # Reusable UI primitives
│       │       ├── Button/
│       │       ├── Field/
│       │       ├── Logo/
│       │       └── SVGIcon/
│       ├── hooks/                # Custom React hooks
│       │   ├── useAuth.js
│       │   ├── useChat.js
│       │   └── useTheme.js
│       ├── pages/                # Page-level components
│       │   ├── Auth/
│       │   ├── ChatPage/
│       │   └── Home/
│       ├── services/api/         # API client layer
│       │   ├── client.js
│       │   ├── interceptors.js
│       │   ├── auth.js
│       │   ├── chat.js
│       │   ├── message.js
│       │   ├── models.js
│       │   └── user.js
│       ├── stores/               # Zustand state stores
│       │   ├── authStore.js
│       │   └── themeStore.js
│       └── styles/               # Global styles
│           ├── globals.css
│           └── themes.css
└── README.md
```

---

## Testing

The backend includes a comprehensive test suite using `pytest` and `pytest-asyncio`:

```bash
cd backend
poetry run pytest
```

**Test categories:**

- **Unit tests** — Security utilities (password hashing, JWT encode/decode)
- **Integration tests** — Database CRUD operations, auth service flow
- **Mock-based tests** — AI provider responses are mocked for deterministic testing

---

## Roadmap

- [ ] **Anthropic & Google Provider Implementation** — Currently stubbed as `NotImplementedProvider`
- [ ] **Cost Calculation** — Real-time token cost estimation per model
- [ ] **Chat History Export** — Export conversations as JSON/Markdown/PDF
- [ ] **Admin Dashboard** — User management, usage analytics
- [ ] **Docker Compose** — One-command deployment with PostgreSQL + backend + frontend
- [ ] **WebSocket Support** — Bidirectional streaming for lower latency
- [ ] **Rate Limiting & Usage Quotas** — Per-user API rate limits
- [ ] **CI/CD Pipeline** — GitHub Actions for automated testing and deployment

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/ScPro0">ScPro</a>
</p>