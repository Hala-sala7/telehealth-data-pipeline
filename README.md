# Telehealth Data Pipeline

**Author:** Hala Salah

## Overview

This project is an end-to-end data pipeline for a virtual health clinic. It takes messy raw data about patients, appointments, and lab results, cleans it, and turns it into analytics-ready tables that can answer business questions like appointment trends, no-show rates, revenue, and abnormal lab results.

The pipeline follows the **medallion architecture**:

**Raw CSV files → Bronze (raw) → Silver (clean) → Gold (analytics-ready)**

| Layer | Tool | What happens |
|---|---|---|
| **Bronze** | Python + DuckDB | Raw files are loaded as they are (all columns as text), with `_source_file` and `_ingested_at` columns to track where each row came from |
| **Silver** | dbt + SQL | Cleaning: fixing data types, parsing different date formats, standardizing categories, removing duplicates and orphan records, and adding lab reference ranges |
| **Gold** | dbt + SQL | Final tables for reporting: a patient table and monthly business metrics |

## Data

- **Source:** synthetic data created by `scripts/generate_data.py` (no real patient information)
- **Tables:** patients, appointments, lab results, and lab reference ranges
- **The data is messy on purpose**, to be close to real source systems:

| Problem in raw data | How it is handled in silver |
|---|---|
| Duplicate patients and appointments | Removed with the `row_number()` window function |
| Dates in `YYYY-MM-DD`, `DD/MM/YYYY`, and `YYYY/MM/DD` | Parsed into one date type with `try_strptime` |
| Gender as `M`, `male`, `MALE`, `f`, `Female`, or empty | Standardized to `male` / `female` / `unknown` |
| Status as `completed`, `COMPLETED`, `Canceled`, `No Show` ... | Standardized to `completed` / `cancelled` / `no_show` |
| Negative or empty appointment duration | Set to null |
| Lab values like `N/A`, `error`, or empty | Removed because they can not be analyzed |
| Appointments for patients that do not exist | Removed with an inner join |

## Data Quality Tests

The pipeline runs **27 automated tests** with dbt every time it is built:

- `unique` and `not_null` tests on all ID columns
- `accepted_values` tests on gender, status, age group, and lab result flag
- `relationships` test to make sure every appointment belongs to a real patient
- Custom SQL tests: revenue can never be negative, and percentages must be between 0 and 100

If any test fails, the build fails. The tests also run automatically on GitHub Actions with every push.

## Results

### 1. Cleaning

| Table | Bronze rows | Silver rows | Removed |
|---|---|---|---|
| Patients | 525 | 500 | 25 duplicates (4.8%) |
| Appointments | 2,076 | 2,036 | 30 duplicates + 10 orphan records (1.9%) |
| Lab results | 1,261 | 1,165 | 96 non-numeric values (7.6%) |

### 2. Gold tables

- **`dim_patients`**: one row per patient with age, age group, number of appointments, and lifetime revenue
- **`agg_monthly_appointments`**: appointments, cancellations, no-show rate, revenue, and active patients per month
- **`agg_lab_results_by_test`**: average value per lab test per month and the share of abnormal (low/high) results

### 3. Example analysis

The notebook `analysis.ipynb` uses the gold layer to answer questions such as:

- How do appointments and revenue change month by month?
- Which providers have the highest no-show rate?
- How does patient revenue differ by age group?
- Which lab tests have the most abnormal results?

> ⚠️ **Note:** because the data is synthetic, these numbers show how the pipeline works, not real business insights.

**Appointments and revenue per month**

<img width="1584" height="484" alt="download" src="https://github.com/user-attachments/assets/6b5d7e52-8145-40e3-ab9c-97c53f232925" />

**No-show rate by provider**

<img width="1062" height="479" alt="download (1)" src="https://github.com/user-attachments/assets/aae23088-75a9-4bed-bd40-0496d04d91dd" />

**Average revenue per patient by age group**

<img width="1015" height="479" alt="download (2)" src="https://github.com/user-attachments/assets/272bdec9-14ce-4b54-9087-aaca0993e9f1" />

**Abnormal lab results by test**

<img width="1106" height="479" alt="download (3)" src="https://github.com/user-attachments/assets/878babe9-39fe-466a-90d0-7b764011614f" />

More SQL examples (window functions like `lag()` and `rank()`) are in `queries/business_questions.sql`.

## Project Structure

```
├── scripts/
│   ├── generate_data.py        # creates the messy raw data
│   └── load_bronze.py          # loads the bronze layer
├── dbt/
│   ├── models/
│   │   ├── sources.yml
│   │   ├── silver/             # cleaning models + tests
│   │   └── gold/               # final models + tests
│   ├── tests/                  # custom SQL tests
│   └── macros/
├── queries/
│   └── business_questions.sql  # example SQL analysis
├── analysis.ipynb              # analysis of the gold layer
├── images/                     # charts from the notebook
├── run_pipeline.py             # runs everything
└── .github/workflows/          # GitHub Actions (CI)
```

## Tools

Python, pandas, NumPy, SQL, DuckDB, dbt, Matplotlib, Seaborn, GitHub Actions

## How to Run

```bash
pip install -r requirements.txt
python run_pipeline.py
```

This creates the data, loads the bronze layer, builds and tests the silver and gold layers with dbt, and prints the number of rows in each table. Run the commands from the main project folder.

To see the analysis, open `analysis.ipynb`, or open it in Google Colab using the badge at the top of the notebook.
