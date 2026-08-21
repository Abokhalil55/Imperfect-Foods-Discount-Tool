# JimatRasa — Surplus Food Marketplace

JimatRasa is a Python-based surplus-food marketplace aligned with **UN SDG 2: Zero Hunger**. It helps Malaysian food sellers list imperfect or near-expiry food, automatically validates submissions, applies dynamic rescue discounts, records purchases, tracks seller sales performance, and notifies customers when requested food categories become available.

The project includes both:

- a **Python CLI**, which demonstrates the fundamental programming requirements directly; and
- a lightweight **web interface** built with vanilla HTML, CSS and JavaScript, backed by the same Python business logic through `api/index.py`.

Python remains the core backend and computational implementation.

---

## Problem and purpose

Usable food is often discarded because of cosmetic imperfections, short remaining shelf life, or difficulty matching surplus stock with nearby buyers. JimatRasa addresses this by giving sellers a structured way to list these items and giving customers a location-based market for purchasing them at dynamically reduced prices.

The system aims to:

1. reduce avoidable food waste by connecting surplus inventory with customers;
2. automate consistent discount calculation using expiry and cosmetic grade;
3. provide sellers with inventory, sales and KPI visibility;
4. let customers browse and purchase available food by location;
5. provide customer support and stock-interest notifications; and
6. measure food-diversion impact related to SDG 2.

---

## Computational Thinking

JimatRasa demonstrates the four core computational-thinking concepts required by the project:

### Decomposition

The overall problem is separated into focused Python modules for authentication, inventory, evaluation, pricing, sales, analytics, notifications, customer support and database access.

### Pattern recognition

The system identifies recurring patterns such as:

- shorter shelf life requiring a larger discount;
- cosmetic grade affecting the discount level;
- repeated customer interest by food category and location;
- sales patterns by date, category and region; and
- inventory status changing when quantity reaches zero or shelf life expires.

### Abstraction

Reusable functions hide implementation details. For example, the UI and CLI call functions such as `calculate_dynamic_discount()`, `get_available_inventory()`, `record_sale()` and `generate_waste_report()` without needing to know the internal database or calculation steps.

### Algorithm design

Important algorithms include:

- dynamic discount calculation;
- purchase validation and stock reduction;
- automatic expiry/day-left synchronization;
- notification matching by category and location; and
- seller KPI and impact calculations from sales records.

---

## Main features

### Seller

- Register imperfect / near-expiry food
- AI-assisted item validation
- Automatic dynamic discount calculation
- Manage inventory and SOLD OUT status
- View sales ledger
- View web dashboard KPIs and sales graphs
- View category revenue contribution
- Generate food-diversion and SDG impact report

### Customer

- Browse available food by Malaysian location
- Purchase available inventory
- View purchase history
- Use AI customer support
- Ask about live inventory availability
- Register interest in unavailable categories
- Receive confirmation and matching-stock emails when configured

Supported locations:

- Cyberjaya
- Petaling Jaya
- Putrajaya
- Puchong

All prices are handled as **Malaysian Ringgit (MYR / RM)**.

---

## Dynamic discount algorithm

The discount combines remaining shelf life and cosmetic grade, with a maximum discount of **80%**.

| Days left | Discount added |
|---|---:|
| 1 day | 45% |
| 2–3 days | 30% |
| 4–7 days | 15% |

| Cosmetic grade | Discount added |
|---|---:|
| Grade A — minor flaw | 5% |
| Grade B — moderate flaw | 15% |
| Grade C — high flaw / near expiry | 25% |

Example:

```text
Original price = RM 10.00
Days left = 2       -> +30%
Grade B             -> +15%
Total discount      -> 45%
Sale price          -> RM 5.50
```

---

## Python concepts demonstrated

The source code demonstrates:

- variables and Python data types;
- arithmetic, comparison and logical operators;
- `if`, `elif`, and `else` conditions;
- `for` and `while` loops;
- extensive user-defined functions;
- menu-driven CLI interaction using `input()`;
- lists, dictionaries and structured records;
- input validation and `try` / `except` error handling;
- formatted output;
- modular programming across multiple Python files;
- external API and database integration.

---

## Project structure

| File / folder | Responsibility |
|---|---|
| `main.py` | Python CLI entry point, authentication menu and role-based menu loop |
| `inventory.py` | Item registration, inventory display and purchase-history output |
| `pricing.py` | Dynamic discount algorithm |
| `sales.py` | Purchase workflow and seller sales ledger |
| `evaluator.py` | AI-assisted validation of seller item submissions |
| `analytics.py` | Food-diversion, revenue and impact calculations |
| `database.py` | Supabase data-access functions |
| `userAuth.py` | Signup and login using Supabase Auth |
| `Update_del.py` | Seller inventory update and deletion workflow |
| `CustomerService.py` | AI customer support and live stock checks |
| `notifications.py` | Confirmation and matching-stock email delivery |
| `advice.py` | Reusable storage-advice logic |
| `../api/index.py` | Python HTTP adapter used by the web interface and Vercel |
| `../Ui/` | Vanilla HTML, CSS and JavaScript presentation layer |

---

## Technology stack

- **Python 3.12**
- **Supabase** for authentication and PostgreSQL-backed persistence
- **OpenAI API** for item evaluation and customer-support tool calling
- **Vanilla HTML/CSS/JavaScript** for the optional enhanced web interface
- **Vercel** for web deployment
- **Gmail SMTP** and **Pushover** for optional notifications

Python dependencies are listed in the repository-level `requirements.txt`.

---

## Run locally

### 1. Install dependencies

From the repository root:

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a local `.env` file. The file is ignored by Git and must not be committed.

Required for the core cloud application:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_API=your_supabase_key
gpt_API_KEY=your_openai_api_key
```

Optional notification features also use:

```env
PUSHOVER_USER=your_pushover_user
PUSHOVER_TOKEN=your_pushover_token
sender_email=your_sender_email
Google_app_pass=your_google_app_password
```

### 3. Run the Python CLI

```bash
cd Imperfect_Foods_Discount_Tool
python main.py
```

### 4. Run the web application locally

From the repository root:

```bash
python api/index.py
```

Then open:

```text
http://127.0.0.1:8000
```

---

## Submission note

The web interface extends the minimum console requirement, but the repository deliberately retains the complete Python CLI. This allows the project to demonstrate the course fundamentals directly while also presenting a more usable working application for the final demonstration.
