# SecondShelf — Discount & Sales Management System

SecondShelf is a surplus-food management application written in Python with an additional lightweight web interface. Integrated with OpenAI GPT models and Supabase, it allows food sellers to register imperfect and near-expiry inventory across multiple Malaysian locations, automatically evaluate items against quality rules, compute dynamic discounts, process sales in **Malaysian Ringgit (MYR)**, track seller KPIs, and measure sustainability impact aligned with **UN SDG 2 (Zero Hunger)**.

---

### 4.1 Purpose of the application

**SecondShelf** was developed to minimize food waste, streamline seller registration, and automate quality control in surplus food distribution.

* **Automated Quality Control:** Leverages an AI Review Agent (`evaluator.py`) to validate registered items against rules for category matching, quantity, realistic MYR pricing, expiry window, and cosmetic grading before adding them to inventory.
* **Dynamic Pricing Engine:** Automatically computes tiered discounts in `pricing.py` based on an item's remaining shelf life and cosmetic grade to encourage rapid sales of nearing-expiry food.
* **Cloud Database Persistence:** Stores inventory and sales records in **Supabase** via `database.py`, with location-scoped queries for Cyberjaya, Petaling Jaya, Putrajaya, and Puchong.
* **Sales & Seller Analytics:** Processes purchases in `sales.py`, updates stock levels, and the web seller dashboard visualizes revenue, transactions, average order value, quantity sold, revenue trends, and category performance.
* **Storage & Spoilage Alerts:** Generates category-specific preservation tips and urgency warnings in `advice.py` based on days remaining until expiry.
* **Environmental Impact Tracking:** Produces real-time analytics in `analytics.py` calculating total food weight saved, revenue recovered, and estimated CO₂ emissions avoided (~2.5 kg CO₂e per kg of food diverted).
* **AI Customer Service:** Provides an interactive GPT-powered chat in `CustomerService.py` to answer questions about discounts, storage, and SDG impact, and to capture follow-up interest from customers.
* **Web Interface:** `Ui/` contains the separate vanilla HTML/CSS/JavaScript presentation layer while Python remains the main backend and assignment implementation.

---

### 4.2 Tech Stack

* **Programming Language:** Python 3.10+
* **Web UI:** Vanilla HTML, CSS, and JavaScript
* **External Libraries & APIs:**
  * `openai` — GPT model integration for quality evaluation and customer service chat.
  * `python-dotenv` — Management of environment variables and API keys.
  * `supabase` — Cloud PostgreSQL backend for inventory and sales persistence.
* **Core Concepts & Architecture:**
  * **Modular Design:** Clear separation of concerns across dedicated Python modules.
  * **Structured JSON Validation:** Enforces OpenAI `response_format={"type": "json_object"}` in the evaluator to guarantee parseable approval/rejection responses.
  * **Location-Scoped Data:** Inventory and sales are filtered by selling location selected at runtime.
  * **Function-Calling Agent:** Customer service uses OpenAI tool calls to record interested customer details (email, location, category preference).
  * **Environmental Analytics Logic:** Algorithmic calculation of food waste diversion metrics and CO₂ mitigation ratios.

#### Project Structure

| Module | Responsibility |
|---|---|
| `main.py` | CLI menu loop and application entry point |
| `inventory.py` | Food item registration and inventory display |
| `evaluator.py` | AI review agent for item validation |
| `pricing.py` | Dynamic discount calculation engine |
| `sales.py` | Purchase workflow and sales ledger |
| `advice.py` | Storage recommendations and spoilage alerts |
| `analytics.py` | SDG 2 waste diversion and impact report |
| `database.py` | Supabase client and data access layer |
| `CustomerService.py` | AI customer service chat with tool calling |
| `CustomersUpdates.py` | Customer email notification helper (in progress) |
| `../api/index.py` | Thin Python web API adapter for Vercel |
| `../Ui/` | Separate HTML/CSS/JavaScript interface |

#### Discount Rules

Discounts are calculated from two factors and capped at **80%**:

| Days Left | Discount Added |
|---|---|
| 1 day | +45% |
| 2–3 days | +30% |
| 4–7 days | +15% |

| Cosmetic Grade | Discount Added |
|---|---|
| Grade A (minor flaw) | +5% |
| Grade B (moderate flaw) | +15% |
| Grade C (high flaw / near expiry) | +25% |

#### Food Categories

1. **Produce** — Fruits & Vegetables  
2. **Bakery** — Bakery & Grains  
3. **Dairy** — Dairy & Chilled Items  
4. **Prepared Food** — Prepared / Packaged Meals  

---

### 4.3 How to use

**1. Prerequisites**

Ensure Python 3 is installed on your local system, along with an active OpenAI API key and a configured Supabase project. Verify your Python installation:

```bash
python --version
```

**2. Install Dependencies**

```bash
pip install openai python-dotenv supabase requests
```

**3. Configure Environment Variables**

Create a `.env` file with the required keys:

```env
gpt_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_API=your_supabase_api_key
```

Additional notification credentials are required when using the Pushover/Gmail notification features.

**4. Run the Python CLI**

From the `Imperfect_Foods_Discount_Tool` directory:

```bash
python main.py
```

**5. Run the Web Interface Locally**

From the repository root:

```bash
python api/index.py
```

Then open `http://127.0.0.1:8000`.

**6. Main Features**

Seller features include registering imperfect / near-expiry food, managing inventory, viewing the sales ledger, viewing seller KPIs and charts in the web dashboard, and generating the SDG impact report. Customer features include browsing available food by location, purchasing items, viewing purchase history, and using the AI customer-service chat.

All application prices are treated and displayed as **Malaysian Ringgit (MYR / RM)**.

---

### 4.4 Demonstrate the application using screen recording (Video/GIF Format)
