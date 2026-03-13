# CalorieTracker AI

CalorieTracker AI is a comprehensive nutrition assistant designed to simplify diet management through artificial intelligence. The application combines a mobile interface for daily tracking with a backend system capable of intelligent voice processing, photo-based meal recognition, and personalized meal planning.

## Application in Action

Experience the core AI capabilities directly through the mobile interface. Below are demonstrations of the primary tracking and planning modules:

<table align="center">
  <tr>
    <td align="center"><b>🎙️ Voice-First Tracking</b></td>
    <td align="center"><b>📸 Photo Recognition</b></td>
    <td align="center"><b>📅 AI Meal Planner</b></td>
  </tr>
  <tr>
    <td align="center">
      <video src="https://github.com/user-attachments/assets/7b1463b6-9bae-419c-b86f-3ee62139ed5d" width="220" autoplay loop muted playsinline></video>
    </td>
    <td align="center">
      <video src="https://github.com/user-attachments/assets/734a8607-3573-4ce0-989a-7797ea6ab54f" width="220" autoplay loop muted playsinline></video>
    </td>
    <td align="center">
      <video src="https://github.com/user-attachments/assets/be828c53-a737-4ea8-8019-0bbf2ac0f623" width="220" autoplay loop muted playsinline></video>
    </td>
  </tr>
  <tr>
    <td align="center"><i>Natural language processing using <b>Whisper STT</b> and <b>Bielik SLM</b> to extract ingredients and weights.</i></td>
    <td align="center"><i>Visual identification and portion estimation powered by <b>Gemini Flash</b>.</i></td>
    <td align="center"><i>Personalized daily plans generated via <b>RAG</b> and <b>pgvector</b> to match specific macros.</i></td>
  </tr>
</table>

## Project Purpose

The main goal of this project is to fix the common problem of tedious calorie counting. Instead of manually searching for products and weighing generic ingredients, users can simply describe their meals using natural language or take a photo. The system automatically identifies food items, estimates portion sizes based on context, and calculates nutritional values. Additionally, the application helps users stick to their diet by generating realistic daily meal plans tailored to their specific caloric and macronutrient goals.

## Key Features

**Voice-First Tracking**
Users can record voice notes describing their meals. The system transcribes the audio using Whisper STT, extracts ingredients with the Bielik SLM, and matches them to products in the database using hybrid semantic search.

**Photo Meal Recognition**
Users can take a photo of their meal and the system will identify the products and estimate portion sizes using Gemini Flash vision model.

**AI Meal Planner**
The application generates full-day meal plans based on user preferences and dietary restrictions (allergies, diets). It uses a Retrieval-Augmented Generation (RAG) approach to select recipes from a curated database that mathematically match the user's nutritional targets.

**Intelligent Product Search**
The search engine combines vector similarity (E5-small embeddings) with full-text search using Reciprocal Rank Fusion. It understands descriptive queries and typos, supports Polish language nuances, and works across all features.

**Progress Analytics**
A dedicated dashboard visualizes weight trends, daily calorie adherence, and macronutrient distribution over time, helping users stay motivated and track their long-term progress.

## Technology Stack

### Mobile Application (Frontend)
- **React Native** with **Expo SDK 54** and TypeScript
- **Styling**: NativeWind (TailwindCSS)
- **State Management**: Zustand (client) + TanStack Query v5 (server)
- **Testing**: Jest 30 + React Testing Library, Maestro (e2e)

### Server & AI (Backend)
- **Python 3.13** with **FastAPI**
- **Database**: PostgreSQL with pgvector and pg_trgm extensions
- **Speech-to-Text**: OpenAI Whisper (local, small variant)
- **NLU**: Bielik 4.5B SLM via llama-cpp-python (local, GGUF)
- **Embeddings**: multilingual-e5-small (384 dim, local)
- **Vision**: Google Gemini Flash API
- **Testing**: pytest + pytest-asyncio

## Requirements

### Production (Docker)
- Docker with Docker Compose
- NVIDIA GPU with CUDA 12.4+ support
- NVIDIA Driver 535+
- NVIDIA Container Toolkit

### Local Development
- Python 3.13 with [uv](https://github.com/astral-sh/uv)
- Node.js 18+
- Docker (for PostgreSQL)
- NVIDIA GPU with CUDA 12.4 drivers

## Quick Start

### Backend (Docker)

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your GEMINI_API_KEY and SECRET_KEY

docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_fineli.py
docker compose exec backend python scripts/seed_food_db.py
docker compose exec backend python scripts/generate_embeddings.py
```

API available at `http://localhost:8000/docs`

### Backend (Local Development)

```bash
docker compose up -d db
cd backend
cp .env.example .env
# Edit .env: set POSTGRES_HOST=localhost, POSTGRES_PORT=5433

uv sync
uv run alembic upgrade head
uv run python scripts/seed_fineli.py
uv run python scripts/seed_food_db.py
uv run python scripts/generate_embeddings.py
uv run uvicorn src.main:app --reload
```

### Frontend

```bash
cd app
npm install
echo "EXPO_PUBLIC_API_URL=http://10.0.2.2:8000" > .env
npm start
```

> `10.0.2.2` is the Android emulator alias for the host machine. For a physical device on the same Wi-Fi, use your computer's IP address.

## Testing

```bash
# Backend (from backend/)
uv run pytest tests/ -x -v

# Frontend (from app/)
npm test

# E2E (requires running emulator + backend)
uv run python scripts/seed_e2e_user.py   # seed test users first
npm run e2e
```

## Project Structure

```
CalorieTracker/
├── app/                          # React Native (Expo) frontend
│   ├── app/                      # Expo Router screens
│   ├── src/
│   │   ├── components/           # UI components
│   │   ├── hooks/                # Custom React hooks
│   │   ├── services/             # API service classes
│   │   ├── schemas/              # Zod validation schemas
│   │   └── __tests__/            # Jest test suites
│   └── .maestro/                 # Maestro e2e test flows
├── backend/
│   ├── src/
│   │   ├── ai/                   # Voice, vision, embeddings
│   │   ├── food_catalogue/       # Product search & database
│   │   ├── meal_planning/        # Meal plan generation (RAG)
│   │   ├── tracking/             # Daily food diary
│   │   └── users/                # Auth & user profiles
│   ├── scripts/                  # DB seeding & utilities
│   ├── seeds/                    # Seed data (Fineli products)
│   └── alembic/                  # Database migrations
└── docker-compose.yml
```

---
*Created by Ceendi*
