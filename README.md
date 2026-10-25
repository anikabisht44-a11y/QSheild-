# QShield: Quantum-Safe Migration Planner

A web app that takes a list of an organization's data assets, estimates how exposed each is to "harvest now, decrypt later" under hypothetical quantum-threat timelines, ranks them, and generates a plain-language migration roadmap and report.

## How to Run

```bash
pip install -r requirements.txt
pip install -e .
pytest -q
streamlit run app.py
```

## Features

### Core (P0)
- Asset inventory management with validation
- Mosca's inequality-based risk calculation
- Three customizable planning scenarios
- Ranked results with priority labels (Critical, High, Medium, Lower)
- Interactive break-even chart
- Per-asset plain-language explanations
- Four-phase migration roadmap
- Markdown report export

### Enhanced (P1)
- Source tags (user estimate vs confirmed)
- Organization type selection
- India milestone overlay (2029 CII target, 2033 enterprise target)
- SQLite persistence
- DPDP Act reference note

### Advanced (P2)
- TLS certificate analysis for algorithm confirmation
- PDF report export

## BUILT / SIMULATED / FUTURE

**BUILT:** asset inventory form, Mosca-based risk engine, scenario analysis, ranking, break-even chart, explanations, roadmap, Markdown report, SQLite persistence, source tags, India milestone overlay, TLS check, PDF export.

**SIMULATED:** the organizations and all asset data are fictional; the quantum-threat timelines are hypothetical scenarios.

**FUTURE (not built):** automated cryptographic discovery beyond the optional TLS check, source-code/CBOM scanning, post-quantum key-exchange detection, signature-risk modelling, validation with real organizations, multi-user deployment.

## Differentiators

QShield differs from existing tools by:

1. **Ranking data assets by confidentiality + migration time** instead of listing technical findings per endpoint
2. **Transparent and reproducible** with deterministic rules, every result shows its inputs, assumptions, and source tags
3. **Scenario and break-even view** instead of a single yes/no assessment
4. **Plain-language roadmap and report** that non-specialists can hand to managers

## Project Structure

```
qshield/
  app.py                  # Streamlit UI
  qshield/
    __init__.py
    risk.py               # Risk engine (Mosca's inequality)
    models.py             # Data models and algorithm classification
    db.py                 # SQLite persistence
    roadmap.py            # Roadmap generation
    report.py             # Report generation (Markdown/PDF)
    milestones.py         # India milestone overlay
    discovery.py          # TLS certificate analysis
  data/
    sample_college.csv
    sample_hospital.csv
  tests/
    test_risk.py
```

## Testing

All tests must pass before the UI is considered done:

```bash
pytest -q
```

## Documentation

- `context.md` - Complete project specification (source of truth)
- `DECISIONS.md` - Design and implementation decisions
- `OPEN_QUESTIONS.md` - Unresolved items and future considerations
