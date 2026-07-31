# Analytical access without Dataset Viewer

The canonical analytical derivative is the verified Parquet file. Hugging Face
Dataset Viewer currently returns HTTP 500 for this project, including the
fresh CSV fallback repository, so Viewer availability is not treated as an
archive integrity requirement.

Local read-only query:

```powershell
uv run --locked python tools/query_treasury_derivative.py `
  --parquet build/derivatives/treasury/datasets.parquet `
  --sql "SELECT organization, count(*) AS datasets FROM treasury GROUP BY organization"
```

The command preloads the Parquet file into an in-memory `treasury` table,
disables external access, accepts exactly one `SELECT`, and bounds output to
1,000 rows. Source objects, provenance, and rights evidence remain
in the preservation archive and Zenodo snapshot.
