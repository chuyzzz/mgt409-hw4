# Campus Customs

Campus Customs is a Vite React TypeScript storefront backed by FastAPI, SQLite catalogue tools, and a PydanticAI shopping agent.

## Place the local data pack

The repository intentionally does not include private/local data. Before running, place the supplied data pack at:

```text
hw4/data/campus_customs.db
hw4/data/products/
```

The database must contain the `catalogue`, `inventory`, `users`, and `chat_messages` tables. Product image paths in the catalogue should point into `data/products/`.

## Configure and run

From the `hw4/` directory, create a local environment file from `.env.example` and add your Portkey key. The agent uses the `gpt_luna` model through Portkey.

Backend:

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --reload --port 8000
```

In a second terminal, run the frontend:

```bash
cd frontend
npm install
npm run dev -- --port 5174
```

Open `http://127.0.0.1:5174/`. Vite proxies `/api` and `/images` to FastAPI on port 8000. The backend serves products, images, authentication, and `POST /api/chat`.

## Submission evidence

Open [output/app_check.html](output/app_check.html) directly in a browser for the three live-site checks. The harness documents models, tools, safety, limits, audit logging, and the front/back run commands.
