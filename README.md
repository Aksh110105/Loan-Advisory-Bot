# Loan Advisory Bot

An interactive agentic ai model designed to provide users with personalized loan advice using OpenAI-powered language models.


## Features & Flow

1. **Backend API (Python/FastAPI)**  
   - Users interact via `frontend` or curl to `/chat` endpoint.  
   - Incoming prompts are routed to OpenAIClient or Gemini services.  
   - Conversations stored using PostgreSQL via Alembic migrations.  
   - Loan Q&A dataset enhances responses.  

2. **Frontend Chat UI (React)**  
   - Interactive chat interface, consuming `/chat` backend.  
   - Displays responses and handles loading/error states.

3. **Database & Data Migration**  
   - PostgreSQL storage setup via Docker Compose.  
   - Alembic handles schema migrations and version control.

4. **Environment Management**  
   - `.env` holds sensitive keys and connection strings.  
   - `docker-compose.yml` orchestrates backend, frontend, and postgres services.

---

## 🛠️ Requirements

- **[DBeaver](https://dbeaver.io/)** (desktop client for inspecting Postgres database)
- **Docker & Docker Compose** (to launch services locally)
- **Node.js** (for frontend build and package installs)
- **Python 3.11+** (backend environment)

---

## ⚙️ Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Aksh110105/Loan‑Advisory‑Bot.git
   cd Loan‑Advisory‑Bot

In your .ENV FILE
OPENAI_API_KEY=...
DATABASE_URL=postgresql://postgres:password@db:5432/loan_advisory
