import sqlite3
import pandas as pd
from scipy import stats

DB_PATH = "cell_counts.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

# Part 2: Initial Analysis
def get_frequency_table():
    conn = get_connection()
    query = """
        SELECT
            cc.sample_id        AS sample,
            cc.population,
            cc.count,
            totals.total_count
        FROM cell_counts cc
        JOIN (
            SELECT sample_id, SUM(count) AS total_count
            FROM cell_counts
            GROUP BY sample_id
        ) totals ON cc.sample_id = totals.sample_id
        ORDER BY cc.sample_id, cc.population
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['percentage'] = (df['count'] / df['total_count'] * 100).round(2)
    return df[['sample', 'total_count', 'population', 'count', 'percentage']]

#Part 3: Statistical Analysis
def get_responder_analysis():
    conn = get_connection()
    query = """
        SELECT
            cc.population,
            cc.count,
            totals.total_count,
            CAST(cc.count AS FLOAT) / totals.total_count * 100 AS percentage,
            s.response
        FROM cell_counts cc
        JOIN samples s ON cc.sample_id = s.sample_id
        JOIN subjects sub ON s.subject_id = sub.subject_id
        JOIN (
            SELECT sample_id, SUM(count) AS total_count
            FROM cell_counts GROUP BY sample_id
        ) totals ON cc.sample_id = totals.sample_id
        WHERE sub.condition = 'melanoma'
          AND s.treatment   = 'miraclib'
          AND s.sample_type = 'PBMC'
          AND s.response IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def run_statistics(df):
    results = []
    for pop in df['population'].unique():
        sub = df[df['population'] == pop]
        responders     = sub[sub['response'] == 'yes']['percentage']
        non_responders = sub[sub['response'] == 'no']['percentage']
        stat, p = stats.mannwhitneyu(responders, non_responders, alternative='two-sided')
        results.append({
            'population':           pop,
            'responder_mean_%':     round(responders.mean(), 2),
            'non_responder_mean_%': round(non_responders.mean(), 2),
            'p_value':              round(p, 4),
            'significant':          'Yes' if p < 0.05 else 'No'
        })
    return pd.DataFrame(results).sort_values('p_value')

# Part 4: Data Subset Analysis
def get_baseline_melanoma_miraclib():
    conn = get_connection()

    base_query = """
        SELECT 
            s.sample_id,
            s.subject_id,
            s.project_id,
            s.sample_type,
            s.treatment,
            s.time_from_treatment_start,
            s.response,
            sub.sex,
            sub.condition,
            sub.age
        FROM samples s
        JOIN subjects sub ON s.subject_id = sub.subject_id
        WHERE sub.condition = 'melanoma'
          AND s.sample_type = 'PBMC'
          AND s.time_from_treatment_start = 0
          AND s.treatment = 'miraclib'
    """
    df = pd.read_sql_query(base_query, conn)

    # Samples per project
    samples_per_project = (df.groupby('project_id')
                             .size()
                             .reset_index(name='sample_count'))

    # Responders/Non-responders
    response_counts = (df.drop_duplicates('subject_id')['response']
                         .value_counts()
                         .reset_index()
                         .rename(columns={'index': 'response', 'count': 'count'}))

    # Males/Females
    gender_counts = (df.drop_duplicates('subject_id')['sex']
                       .value_counts()
                       .reset_index()
                       .rename(columns={'index': 'sex', 'count': 'count'}))

    # Avg B cells of melanoma males for responder at time=0
    avg_bcell_query = """
        SELECT ROUND(AVG(cc.count), 2) AS avg_b_cells
        FROM cell_counts cc
        JOIN samples s    ON cc.sample_id  = s.sample_id
        JOIN subjects sub ON s.subject_id  = sub.subject_id
        WHERE sub.condition = 'melanoma'
          AND sub.sex       = 'M'
          AND s.sample_type = 'PBMC'
          AND s.time_from_treatment_start = 0
          AND s.treatment   = 'miraclib'
          AND s.response    = 'yes'
          AND cc.population = 'b_cell'
    """
    avg_b = pd.read_sql_query(avg_bcell_query, conn).iloc[0, 0]
    conn.close()

    return {
        'baseline_samples':          df,
        'samples_per_project':       samples_per_project,
        'response_counts':           response_counts,
        'gender_counts':             gender_counts,
        'avg_bcell_male_responders': avg_b
    }

if __name__ == "__main__":
    print("Part 2: Initial Analysis")
    freq = get_frequency_table()
    print(freq.head(10).to_string(index=False))

    print("\nPart 3: Statistical Analysis")
    resp_df = get_responder_analysis()
    stats_df = run_statistics(resp_df)
    print(stats_df.to_string(index=False))

    print("\nPart 4: Data Subset Analysis")
    results = get_baseline_melanoma_miraclib()
    print("\nSamples per project:")
    print(results['samples_per_project'].to_string(index=False))
    print("\nResponders/Non-responders:")
    print(results['response_counts'].to_string(index=False))
    print("\nMales/Females:")
    print(results['gender_counts'].to_string(index=False))
    print(f"\nAvg B cells (melanoma male responders at t=0): {results['avg_bcell_male_responders']:.2f}")