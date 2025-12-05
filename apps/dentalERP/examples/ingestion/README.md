# Manual Ingestion Sample Data

This directory contains lightweight sample files that can be used with
`scripts/ingestion-demo.sh` to exercise the manual ingestion endpoints end-to-end.

## Files

- `patients.csv` — Dentrix-style patient export.
- `patients.json` — JSON payload mirroring the CSV headers.
- `patients_mapping.json` — canonical mapping for the patient dataset.
- `payroll.csv` — ADP-style payroll register for two associates.
- `payroll_mapping.json` — field map used when promoting payroll records.
- `financials.csv` — NetSuite monthly financial summaries for two locations.
- `financials_mapping.json` — field map for promoting financial period summaries.

All data is synthetic.
