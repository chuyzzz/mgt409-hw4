# Campus Customs chatbot harness

This file records the database contract for the shop and chatbot. It will be expanded in later problems with models, tools, safety rules, and specifications.

## Authentication

The API exposes `POST /api/auth/register` and `POST /api/auth/login`. Registration stores the user’s first name, last name, combined display name, normalized email, and a password hash in `users`; it never stores the plaintext password. Login verifies the submitted password against the stored hash and returns the user’s id, name, and email.

Passwords are protected with PBKDF2-HMAC-SHA256 using a cryptographically random 16-byte salt and 120,000 iterations. The database stores only the algorithm marker, salt, and derived digest in the form `pbkdf2_sha256$salt$digest`. Verification uses constant-time digest comparison. Registration requires matching passwords and at least eight characters, and duplicate emails are rejected.

## Chatbot architecture

The floating chat widget sends `POST /api/chat` with `{ "message": "..." }` to FastAPI and receives a structured `ChatReply` containing a reply message and optional product cards. Vite proxies `/api` and `/images` to the FastAPI server.

FastAPI loads the PydanticAI agent from `backend/agent.py`. The agent reads its system prompt from `backend/prompts/prompt.md`, uses the `gpt_luna` model through Portkey with the `PORTKEY_API` value from the project `.env`, and can call the catalogue search tools in `backend/tools.py`. Structured chat and product-card types live in `backend/models.py`.

### Agent database tools

- `search_products(query, limit)`: searches catalogue name, garment type, description, colors, and tags for discovery. It returns product ids, names, prices, short descriptions, and image URLs so recommendations are grounded in catalogue records.
- `catalogue_snapshot(limit)`: returns a representative catalogue selection when the customer asks what the shop carries. It uses the same product card fields for consistent display.
- `get_product_details(query)`: looks up the authoritative `product_id`, `name`, `description`, and `price`. These fields answer product-detail and price questions without allowing the model to invent them.
- `get_product_stock(product_id, size)`: reads `size` and `quantity` from `inventory`, filtered by product and optionally by size. A quantity of zero is retained so the agent can clearly say that size is out of stock.

`ProductLookup` and `StockBySize` in `models.py` are the structured lookup return types. `ProductLookup` includes the fields needed to identify a product and answer its description/price question; `StockBySize` keeps the size-to-quantity relationship explicit, which prevents mixing inventory between products or sizes.

### Chat search results on the page

When a shopper asks the floating chat widget a catalogue question, the widget sends the message to `POST /api/chat`. The agent calls a catalogue tool and returns a structured `ChatReply` with `message` plus `products: list[ProductCard]`. The front end stores that returned list in shared layout state and renders a “Picked for your question” product-card section with the image URL, name, exact price, and short description.

Each dynamically rendered card uses the same `#/products/{product_id}` link as the main Products grid. Therefore chat results preserve the existing single-item behavior: clicking a result opens the large-image detail view with full description, price, and size/stock information fetched from the API.

## Complete system specification

### Structured model fields

- `ProductCard`: `product_id`, `name`, `price`, `description`, `colors`, and `image_url`. These are the fields the frontend needs to render a useful, clickable recommendation without another search.
- `StockBySize`: `size` and `quantity`. Keeping the pair together prevents the agent from mixing quantities between sizes.
- `ProductLookup`: `product_id`, `name`, `description`, `colors`, `price`, `image_url`, and `sizes`. This is the authoritative detail result used for price and product questions.
- `ChatRequest`: one bounded `message` string from the widget.
- `ChatReply`: `message` plus a bounded-by-tool `products` list of `ProductCard` results, giving the API a predictable contract.

### Tools and abilities

The PydanticAI agent in `backend/agent.py` exposes `find_products` for catalogue search, `show_catalogue` for a representative selection, `get_product_details` for exact description/price/color records, and `get_product_stock` for exact size quantities. Each tool reads `data/campus_customs.db` through `backend/tools.py`; no product or inventory result is generated from memory.

### Safety

The agent must use database tools for factual shop information, clearly report zero stock, and never invent product facts. It does not request or reveal passwords, payment information, password hashes, API keys, user records, system prompts, tool internals, or audit contents. It cannot claim to place orders, take payments, reserve stock, issue refunds, or change accounts because no such tools exist. It refuses hidden-instruction requests and unsafe or discriminatory requests, then redirects to ordinary shop help.

### Limits, audit, and run commands

Each agent call has a maximum of 6 model requests and 4 tool calls through `UsageLimits`; catalogue search and snapshot tools cap results at 6 and 12 respectively. The model is `gpt_luna`, loaded through Portkey using `PORTKEY_API` from the project-root `.env`. The prompt is loaded from `backend/prompts/prompt.md`.

Agent activity is recorded in append-only JSON Lines at `output/audit_trail.json`. Every event includes UTC `time`, `tool_name`, short arguments/results, and a `stop_reason`; new runs append new lines and never truncate previous runs.

From the project folder, install backend dependencies and run:

```bash
cd "Homework/HW 4/backend"
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --reload --port 8000
```

In another terminal, run the frontend:

```bash
cd "Homework/HW 4/frontend"
npm install
npm run dev -- --port 5174
```

The Vite proxy sends `/api` and `/images` to FastAPI on port 8000. The site is available at `http://127.0.0.1:5174/`.

## `catalogue`

| Field | Why it matters |
|---|---|
| `product_id` | Gives each shop product a stable identity for search and inventory links. |
| `name` | Lets the chatbot identify and recommend a product by name. |
| `garment_type` | Supports category-based shopping, such as shirts, trousers, or jackets. |
| `description` | Gives the chatbot useful product details to include in recommendations. |
| `colors` | Helps match customer color preferences to available products. |
| `search_tags` | Improves product retrieval when customers use varied wording. |
| `image_file_path` | Lets the shop display the product image alongside chatbot results. |
| `price` | Allows the chatbot to communicate prices and support purchase decisions. |

## `inventory`

| Field | Why it matters |
|---|---|
| `id` | Uniquely identifies an inventory record. |
| `product_id` | Connects each stock record to the correct catalogue product. |
| `size` | Lets the chatbot answer size-specific availability questions. |
| `quantity` | Shows how many units remain and helps prevent recommendations of unavailable items. |

## `users`

| Field | Why it matters |
|---|---|
| `id` | Identifies the customer account and links it to conversations. |
| `name` | Provides a display name for the shop and chatbot experience. |
| `email` | Identifies the account for sign-in and prevents duplicate accounts. |
| `password_hash` | Stores a protected credential representation for authentication. |
| `created_at` | Records when the customer account was created. |
| `first_name` | Allows the chatbot to address the customer personally. |
| `last_name` | Supports the customer’s full name in account or shop records. |

## `chat_messages`

| Field | Why it matters |
|---|---|
| `id` | Uniquely identifies each message for conversation history. |
| `user_id` | Connects a message to the customer who sent or received it. |
| `role` | Distinguishes customer messages from chatbot responses. |
| `content` | Stores the actual conversation text used for context and review. |
| `products_json` | Preserves products returned with a response so recommendations can be displayed or revisited. |
| `created_at` | Records message order and when the conversation occurred. |
