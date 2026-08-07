Here is the complete text formatted as raw Markdown in a single code block so you can easily copy it:

```markdown
# Surplus Food Management & AI Review System

An automated, command-line-based surplus food management application written in Python. Integrated with OpenAI GPT models, this tool allows food sellers to register surplus inventory, automatically evaluate items against strict quality rules, compute dynamic discounts, and track sales while supporting sustainability targets.

---

### 4.1 Purpose of the application

The **Surplus Food Management & AI Review System** was developed to minimize food waste, streamline seller registration, and automate quality control in surplus food distribution.

* **Automated Quality Control:** Leverages an AI Review Agent (`evaluator.py`) to validate registered items against strict validation rules (category matching, quantity checks, realistic pricing, expiry window, and cosmetic grading) before adding them to inventory.
* **Dynamic Pricing Engine:** Automatically computes tiered price discounts based on an item's remaining shelf life and cosmetic grade to encourage rapid sales of nearing-expiry food.
* **In-Memory Data Management:** Tracks active inventory and completed purchases using clean runtime Python list structures (`inventory = []` and `sales_history = []`) without requiring external database configuration.
* **Environmental Impact Tracking:** Generates real-time analytics aligned with **UN SDG 2 (Zero Hunger)**, calculating total food weight saved, revenue recovered, and estimated CO₂ emissions avoided.

---

### 4.2 Tech Stack

* **Programming Language:** Python 3.10+
* **External Libraries & APIs:** 
  * `openai`: Integration with OpenAI GPT models for structured quality evaluation.
  * `python-dotenv`: Management of environment variables and API keys.
* **Core Concepts & Architecture:**
  * **Modular Design:** Clear separation of concerns across dedicated modules (`main.py`, `inventory.py`, `evaluator.py`, `pricing.py`, `sales.py`, `advice.py`, and `analytics.py`).
  * **Structured JSON Validation:** Enforces OpenAI `response_format={"type": "json_object"}` to guarantee deterministic JSON responses for automated parse handling.
  * **In-Memory State Management:** Lightweight runtime list tracking for rapid lookup, real-time inventory updates, and transaction archiving.
  * **Environmental Analytics Logic:** Algorithmic calculation of food waste diversion metrics and CO₂ mitigation ratios.

---

### 4.3 How to use

* **1. Prerequisites**  
Ensure Python 3 is installed on your local system alongside an active OpenAI API Key. You can verify your Python installation by running:

```bash
python --version

```

* **2. Install Dependencies**
Install the required packages using `pip`:

```bash
pip install openai python-dotenv

```

* **3. Configure Environment Variables**
Create a `.env` file in the root directory and add your OpenAI API Key:

```env
gpt_API_KEY=your_openai_api_key_here

```

* **4. Run the Application**
Launch the interactive CLI menu:

```bash
python main.py

```

---

### 4.4 Demonstrate the application using screen recording (Video/GIF Format)

```

```