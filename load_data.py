import sqlite3
import pandas as pd
import os

DB_PATH = "cell_counts.db"
CSV_PATH = "cell-count.csv"

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

def init_db(conn):
    conn.executescript("""
        DROP TABLE IF EXISTS cell_counts;
        DROP TABLE IF EXISTS samples;
        DROP TABLE IF EXISTS subjects;
        DROP TABLE IF EXISTS projects;

        CREATE TABLE projects (
            project_id  TEXT PRIMARY KEY
        );

        CREATE TABLE subjects (
            subject_id  TEXT PRIMARY KEY,
            project_id  TEXT REFERENCES projects(project_id),
            condition   TEXT,
            age         INTEGER,
            sex         TEXT
        );

        CREATE TABLE samples (
            sample_id                   TEXT PRIMARY KEY,
            subject_id                  TEXT REFERENCES subjects(subject_id),
            project_id                  TEXT REFERENCES projects(project_id),
            sample_type                 TEXT,
            treatment                   TEXT,
            time_from_treatment_start   INTEGER,
            response                    TEXT
        );

        CREATE TABLE cell_counts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id   TEXT REFERENCES samples(sample_id),
            population  TEXT,
            count       INTEGER
        );
    """)
    conn.commit()

def load_data(conn):
    df = pd.read_csv(CSV_PATH)

    # Projects
    projects = df[['project']].drop_duplicates().rename(columns={'project': 'project_id'})
    projects.to_sql('projects', conn, if_exists='append', index=False)

    # Subjects
    subjects = df[['subject', 'project', 'condition', 'age', 'sex']].drop_duplicates()
    subjects = subjects.rename(columns={'subject': 'subject_id', 'project': 'project_id'})
    subjects.to_sql('subjects', conn, if_exists='append', index=False)

    # Samples
    samples = df[['sample', 'subject', 'project', 'sample_type',
                  'treatment', 'time_from_treatment_start', 'response']].drop_duplicates()
    samples = samples.rename(columns={'sample': 'sample_id', 'subject': 'subject_id', 'project': 'project_id'})
    samples.to_sql('samples', conn, if_exists='append', index=False)

    # Cell counts
    cell_df = df[['sample'] + POPULATIONS].melt(
        id_vars='sample',
        value_vars=POPULATIONS,
        var_name='population',
        value_name='count'
    ).rename(columns={'sample': 'sample_id'})
    cell_df.to_sql('cell_counts', conn, if_exists='append', index=False)

    conn.commit()
    print(f"Loaded {len(df)} rows into {DB_PATH}")
    print(f"   Projects: {len(projects)}, Subjects: {len(subjects)}, Samples: {len(samples)}")

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    load_data(conn)
    conn.close()