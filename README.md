# Immune Cell Population Dashboard

> Analysis tool for Bob Loblaw's drug candidate study, examining immune cell population changes across patient samples.

## Dashboard Link
**[Live Dashboard](https://teiko-technical-assessment-rottn93urt55ejbpdzbgfz.streamlit.app/)** 
---

## Project Structure

```
loblaw-bio-assessment/
├── load_data.py          # Part 1: Data Management
├── analysis.py           # Parts 2–4: All analytical logic
├── dashboard.py          # Interactive Streamlit dashboard
├── cell-count.csv        # Input data
├── cell_counts.db        # Generated SQLite database (auto-created)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## How to Run (GitHub Codespaces)

### 1. Open in Codespaces
Click the green **Code** button on the GitHub repo → **Codespaces** → **Create codespace on main**

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Load data into the database
```bash
python load_data.py
```
This creates `cell_counts.db` in the root directory.

### 4. Run the analysis (prints all outputs to terminal)
```bash
python analysis.py
```

### 5. Launch the dashboard
```bash
streamlit run dashboard.py
```
Codespaces will show a popup — click **Open in Browser** to view the dashboard.

---

## Database Schema

### Tables

```sql
projects     (project_id)
subjects     (subject_id, project_id, condition, age, sex)
samples      (sample_id, subject_id, project_id, sample_type,
              treatment, time_from_treatment_start, response)
cell_counts  (id, sample_id, population, count)
```

### Entity Relationship

```
projects
   └── subjects (many subjects per project)
         └── samples (many samples per subject over time)
               └── cell_counts (one row per cell population per sample)
```

### Rationale

**Why four tables?**

- **`projects`** — Isolates project-level metadata. Adding hundreds of projects means one new row here, with no changes to other tables.
- **`subjects`** — Stores patient demographics once, regardless of how many samples they contribute. Eliminates redundancy across repeated measurements.
- **`samples`** — Captures sample-level clinical context (treatment, timepoint, response). One subject can have many samples (e.g., baseline, week 1, week 2), which is essential for longitudinal trial data.
- **`cell_counts`** — Stores data in **long format** (one row per population per sample). This is the most flexible design: adding a new cell population requires no schema changes just new rows.

### Scalability

| Scenario | How the schema handles it |
|---|---|
| Hundreds of projects | New rows in `projects`; no schema change |
| Thousands of samples | `samples` table scales linearly; index on `subject_id` keeps joins fast |
| New cell populations | New rows in `cell_counts`; no new columns needed |
| New analytics (survival, longitudinal) | Query across `time_from_treatment_start` with existing schema |
| Multi-omics data | Add a `data_type` column to `cell_counts` or create a sibling table |

**Recommended indexes for scale:**
```sql
CREATE INDEX idx_cell_counts_sample ON cell_counts(sample_id);
CREATE INDEX idx_cell_counts_population ON cell_counts(population);
CREATE INDEX idx_samples_subject ON samples(subject_id);
CREATE INDEX idx_samples_treatment ON samples(treatment);
```

---

## Code Structure & Design Decisions

### `load_data.py`
- Single entry point (`python load_data.py`)
- Drops and recreates all tables on each run 
- Melts wide CSV format → long format for `cell_counts` using pandas
- Designed to be run **once** before anything else

### `analysis.py`
- All analytical logic lives here as **importable functions** — not a script that runs everything
- Each part (2, 3, 4) is a separate function so the dashboard can call them independently
- Uses **SQLite queries** for filtering/aggregation to keep the logic database-driven and scalable
- Statistical test: **Mann-Whitney U** (non-parametric, appropriate for small/non-normal groups)
- Significance threshold: **α = 0.05** (standard in clinical biomarker research)

### `dashboard.py`
- Built with **Streamlit** for rapid interactive development
- Calls functions from `analysis.py` directly
- Uses **Plotly** for interactive charts
- Organized into three clear sections matching Parts 2, 3, 4

### Why this separation?
Keeping `load_data.py`, `analysis.py`, and `dashboard.py` as separate files means:
- You can re-run analysis without reloading the database
- You can test analysis logic independently of the UI
- The dashboard is purely a presentation layer

---

## Statistical Approach

- **Test used:** Mann-Whitney U 
- **Why:** Non-parametric; does not assume normality; appropriate for small clinical groups
- **Threshold:** p < 0.05


---

## requirements.txt

```
pandas
scipy
streamlit
plotly
```
