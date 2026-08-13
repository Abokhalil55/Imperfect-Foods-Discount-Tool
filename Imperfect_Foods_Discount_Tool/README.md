# Imperfect Foods Discount & Sales Management System

An automated, command-line surplus food management application written in Python. Integrated with OpenAI GPT models and Supabase, this tool allows food sellers to register imperfect and near-expiry inventory across multiple locations, automatically evaluate items against strict quality rules, compute dynamic discounts, process sales, and track sustainability impact aligned with **UN SDG 2 (Zero Hunger)**.

---

### 4.1 Purpose of the application

The **Imperfect Foods Discount & Sales Management System** was developed to minimize food waste, streamline seller registration, and automate quality control in surplus food distribution.

* **Automated Quality Control:** Leverages an AI Review Agent (`evaluator.py`) to validate registered items against strict rules (category matching, quantity checks, realistic pricing, expiry window, and cosmetic grading) before adding them to inventory.
* **Dynamic Pricing Engine:** Automatically computes tiered discounts in `pricing.py` based on an item's remaining shelf life and cosmetic grade to encourage rapid sales of nearing-expiry food.
* **Cloud Database Persistence:** Stores inventory and sales records in **Supabase** via `database.py`, with location-scoped queries for Cyberjaya, Petaling Jaya, Putrajaya, and Puchong.
* **Sales & Ledger Tracking:** Processes purchases in `sales.py`, updates stock levels, and displays a revenue summary ledger per location.
* **Storage & Spoilage Alerts:** Generates category-specific preservation tips and urgency warnings in `advice.py` based on days remaining until expiry.
* **Environmental Impact Tracking:** Produces real-time analytics in `analytics.py` calculating total food weight saved, revenue recovered, and estimated CO₂ emissions avoided (~2.5 kg CO₂e per kg of food diverted).
* **AI Customer Service:** Provides an interactive GPT-powered chat in `CustomerService.py` to answer questions about discounts, storage, and SDG impact, and to capture follow-up interest from customers.

---

### 4.2 Tech Stack

* **Programming Language:** Python 3.10+
* **External Libraries & APIs:**
  * `openai` — GPT model integration for quality evaluation and customer service chat.
  * `python-dotenv` — Management of environment variables and API keys.
  * `supabase` — Cloud PostgreSQL backend for inventory and sales persistence.
* **Core Concepts & Architecture:**
  * **Modular Design:** Clear separation of concerns across dedicated modules (see Project Structure below).
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
pip install openai python-dotenv supabase
```

**3. Configure Environment Variables**

Create a `.env` file in the project root (`python_project/`) with the following keys:

```env
gpt_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_API=your_supabase_api_key
```

**4. Run the Application**

From the `Imperfect_Foods_Discount_Tool` directory, launch the interactive CLI:

```bash
python main.py
```

**5. Main Menu Options**

| Option | Action |
|---|---|
| 1 | Register an imperfect / near-expiry food item |
| 2 | View all inventory and dynamic discounts (by location) |
| 3 | Buy a food item (process a sale) |
| 4 | View storage advice and spoilage alerts |
| 5 | View sales and revenue summary ledger |
| 6 | Generate food waste diversion and SDG impact report |
| 7 | Customer service chat (AI assistant) |
| 8 | Exit application |

When viewing inventory, buying, or generating reports, you will be prompted to select a selling location: Cyberjaya, Petaling Jaya, Putrajaya, or Puchong.

---

### 4.4 Demonstrate the application using screen recording (Video/GIF Format)

