# QueryWise — Text-to-SQL & BI Query System

**Powered by Mistral AI · Built for non-technical business users**

---

## What This Is

QueryWise lets anyone on your team ask data questions in plain English and get instant answers — no SQL knowledge needed. You type a question like *"Which region had the highest profit this year?"* and the system writes the SQL, runs it, draws a chart, and explains the result in plain language.

This project was built for the Generative AI Data Analysis assessment, addressing the real business problem of non-technical stakeholders being locked out of their own data.

---

## What You Need Before Starting

| Requirement | Where to get it |
|-------------|----------------|
| Python 3.9 or higher | [python.org](https://www.python.org/downloads/) |
| A Mistral API key | [console.mistral.ai](https://console.mistral.ai) |
| Your dataset | CSV or Excel file (.csv, .xlsx, .xls) |

> **Getting your Mistral API key:**  
> 1. Go to [console.mistral.ai](https://console.mistral.ai) and sign up or log in  
> 2. Click **API Keys** in the left sidebar  
> 3. Click **Create new key**, give it a name, and copy it  
> Keep it safe — you will paste it into the app sidebar when you launch.

---

## Setup & Installation

Open your terminal or command prompt inside the project folder and run these two commands:

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`.

> **Note:** There is no `mistralai` package in the requirements. The app talks to Mistral directly over the internet using `requests` — this avoids all SDK version conflicts.

---

## How to Use the App

**Step 1 — Enter your API key**  
Paste your Mistral API key into the sidebar. The app will validate it immediately and show a green confirmation.

**Step 2 — Upload your dataset**  
Click the file uploader in the sidebar and select your CSV or Excel file. The app will load it into an in-memory database and show you the row and column count.

**Step 3 — Generate business questions**  
Click **"✨ Generate 6 Business Questions from my Dataset"**. Mistral will read your column names and suggest 6 relevant questions a manager might ask. These are the questions you submit for your assignment.

**Step 4 — Run a query**  
Click any suggested question to load it into the input box, then hit **"🔍 Run Query"**. You can also type your own question at any time.

**Step 5 — Review your results**  
Each query returns three tabs:
- **Chart** — an automatically selected bar, line, or scatter chart
- **Table** — the raw data, downloadable as CSV
- **Insight** — a 2–4 sentence plain-English business takeaway written by Mistral

---

## Files in This Project

| File | Purpose |
|------|---------|
| `app.py` | The full application — this is your main submission file |
| `requirements.txt` | Python packages needed to run the app |
| `sample_sales_data.csv` | A ready-made 60-row dataset to test with |
| `README.md` | This guide |

---

## Assignment Submission Checklist

### The App (Person 1)
- [ ] Run the app and confirm it launches without errors
- [ ] Upload the dataset and generate 6 business questions
- [ ] Run each of the 6 questions and note the SQL shown on screen

### Formatting Queries (Person 1)
- [ ] Copy each SQL query
- [ ] Go to [carbon.now.sh](https://carbon.now.sh), paste the SQL, set language to **SQL**
- [ ] Take a clean screenshot of each formatted query

### Screenshots (Person 1 or 2)
- [ ] Screenshot each SQL query as it appears in the app
- [ ] Screenshot the chart or table result beneath each query

### Google Sheets Upload (Person 2)
- [ ] Create a new Google Sheet
- [ ] Add columns: `#` · `Business Question` · `SQL Query` · `Rows Returned`
- [ ] Paste all 6 queries into the sheet
- [ ] Set sharing to **"Anyone with the link can view"**
- [ ] Copy and include the link in your final submission

---

## How It Works (Architecture)

```
User types a plain-English question
           ↓
App sends question + table schema to Mistral API
           ↓
Mistral returns a raw SQL query
           ↓
App checks query is safe (SELECT only)
           ↓
SQLite runs the query on your uploaded data
           ↓
App picks the best chart type automatically
           ↓
Mistral writes a plain-English business insight
           ↓
Results shown: Chart · Table · Insight
```

---

## Safeguards & Limitations

**Safeguards built into the app:**
- Only `SELECT` queries are allowed to run. Any query containing `DROP`, `DELETE`, `INSERT`, `UPDATE`, `CREATE`, or `ALTER` is blocked before execution.
- Your raw data never leaves your machine. Only the question and column names are sent to Mistral.
- Results are capped at 500 rows to keep the interface fast.
- The API key is held in memory for the session only and is never written to disk.

**Known limitations:**
- SQL accuracy depends on column names being clear and descriptive. Rename vague columns like `col1` before uploading.
- Very complex questions involving multiple conditions may need rephrasing if the first result looks wrong.
- The app works with single-table datasets. Multi-table joins require uploading a pre-joined file.

---

## Sample Dataset

The included `sample_sales_data.csv` has 60 rows of sales data across regions, products, channels, and customer segments — with revenue, profit, budget, and sentiment score columns. It maps directly to the example business questions in the assignment brief and is a good dataset to demo the app with.

---

*Built for the Generative AI Data Analysis & Business Decision-Making Assessment.*