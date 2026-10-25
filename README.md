# QShield: Quantum-Safe Migration Planner

A web app that takes a list of an organization's data assets, estimates how exposed each is to "harvest now, decrypt later" under hypothetical quantum-threat timelines, ranks them, and generates a plain-language migration roadmap and report.

## How to Run

```bash
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

## BUILT / SIMULATED / FUTURE

**BUILT:** asset inventory form, Mosca-based risk engine, scenario analysis, ranking, break-even chart, explanations, roadmap, Markdown report, SQLite persistence, source tags, India milestone overlay, TLS check, PDF export.

**SIMULATED:** the organizations and all asset data are fictional; the quantum-threat timelines are hypothetical scenarios.

**FUTURE (not built):** automated cryptographic discovery beyond the optional TLS check, source-code/CBOM scanning, post-quantum key-exchange detection, signature-risk modelling, validation with real organizations, multi-user deployment.
