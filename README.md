# Zepto AI & ML Platform

An end-to-end AI/ML capstone project for Zepto's analytics guild, combining three connected capabilities:
1. **Data Engineering Pipeline** (`/data_pipeline`) — scrapes, cleans, and stores catalog data in a relational database.
2. **Analytics Pipeline** (`/analytics`) — profiles and models a customer-style dataset end to end.
3. **GenAI Support Assistant** (`/support_assistant`) — answers policy questions grounded in Zepto's documents.
---

## Setup

Each module has its own `requirements.txt`. Install dependencies per module before running it.

```bash
cd data_pipeline && pip install -r requirements.txt
cd ../analytics && pip install -r requirements.txt
cd ../support_assistant && pip install -r requirements.txt
```
---

## How to Run

### 1. Data Pipeline (`/data_pipeline`) 

Open `data_pipeline.ipynb` in Jupyter Notebook and run all cells top to bottom:

```bash
cd data_pipeline
jupyter notebook
```

This will:
- Scrape 70 books across 4 categories (Travel, Mystery, Historical Fiction, Classics) from books.toscrape.com
- Clean and type-convert the data (`price_gbp`, `rating`, `in_stock`)
- Convert prices to INR using a fixed baseline rate: **1 GBP = 105.50 INR**
- Build a normalized SQLite database (`books.db`) with two linked tables (`categories`, `books`)
- Run 5 required SQL queries (WHERE, ORDER BY + LIMIT, DISTINCT, BETWEEN, and a JOIN)
- Read back results using `pandas.read_sql` and reproduce the JOIN using `pandas.merge`, confirming both approaches match

All outputs are saved directly inside the notebook cells.

### 2. Analytics (`/analytics`) 

Will profile and model a customer/passenger-style dataset end to end, including:
- Exploratory data analysis (distributions, correlations, missing-value checks) with visualizations
- Feature engineering and preprocessing
- Training and evaluating at least one predictive model (classification or regression, depending on chosen dataset)
- Model evaluation metrics with written interpretation

### 3. Support Assistant (`/support_assistant`) 

Will build a GenAI assistant that answers policy questions grounded in Zepto's own documents, including:
- Document ingestion and chunking
- Retrieval-Augmented Generation (RAG) setup — embeddings + vector search
- A query interface that answers questions using retrieved context, not just the model's general knowledge

---

## Design Decisions

### Data Pipeline
- **Data source:** books.toscrape.com, a public sandbox site built for scraping practice — no login or API key required.
- **Fields scraped:** title, price, star rating, availability, and category, for each book across 4 categories (70 books total, exceeding the 60-book minimum).
- **Rating conversion:** star ratings are stored as CSS class names on the site (e.g., `"star-rating Two"`); these were mapped to integers 1–5 using a manual lookup dictionary.
- **Currency conversion:** used the required fixed project-defined rate of 1 GBP = 105.50 INR to compute `price_inr`. This is a fixed constant, not a live market rate, and required no external API call.
- **Missing/broken row handling:** the pipeline checks for any row where `price_gbp` or `rating` failed to parse, and falls back to median-imputation for numeric fields rather than dropping rows, to preserve dataset size. In this run, 0 rows required imputation; the scraped data parsed cleanly.
- **Database schema:** two SQLite tables, `categories` (category_id PK, category_name) and `books` (book_id PK, ..., category_id FK referencing categories) — a standard one-to-many relationship.
- **Re-run safety:** the notebook clears existing rows (`DELETE FROM`) before each insert, so re-running the notebook never creates duplicate rows.
- **SQL vs pandas JOIN comparison:** both methods agree on all books tied at the top rating (5 stars). Where ties exist at the cutoff of a `LIMIT`, the specific 10th-ranked book can differ between the SQL query and the `pandas.merge` reproduction, since neither specifies a secondary sort order.

### Analytics
*To be documented once built.*

### Support Assistant
*To be documented once built.*

---

## Git Workflow

This repository's commit history includes a feature branch created, committed to at least twice, and merged back into `main`, as required by the project guidelines.



## Author

[R. Archita Bharadwaj] — [B.E. AI & ML, Stanley College of Engineering and Technology for Women]
