# DECISIONS.md

This file records design and implementation decisions made during QShield development.

## Technology Stack Decisions

- **Streamlit**: Chosen for the web framework because it's Python-native, requires minimal frontend code, and is ideal for data-focused applications with live updates.
- **SQLite**: Chosen for persistence because it's built into Python standard library, requires no separate database server, and is perfect for single-user local applications.
- **Plotly**: Chosen for the break-even chart because it integrates well with Streamlit and provides interactive visualizations.
- **fpdf2**: Chosen for PDF export over reportlab because it has a simpler API for basic text-based reports.
- **cryptography**: Chosen for TLS certificate parsing because it's the standard Python library for cryptographic operations.

## Implementation Decisions

- **Asset validation in __post_init__**: Asset dataclass validates fields on instantiation to ensure data integrity at the object level.
- **Separate validate_asset function**: Additional validation function exists for UI-level validation that can handle invalid objects without raising exceptions.
- **Session storage for UI**: Streamlit session_state is used for in-memory state during the session, with SQLite as the persistent backing store.
- **Algorithm classification mapping**: Centralized in models.py with ALGORITHM_CLASS_MAP for easy maintenance and consistency.
- **Risk engine as pure functions**: All risk calculation functions in risk.py are pure functions with no I/O or Streamlit dependencies for testability.
- **Tests before UI**: Following the spec requirement, risk engine was implemented and tested before the UI was built.

## Scope Decisions

- **P0 (MVP) completed**: All core features implemented - asset management, scenarios, risk calculation, ranking, chart, explanations, roadmap, Markdown report.
- **P1 completed**: Source tags, organization type, India milestone overlay, DPDP note, SQLite persistence all implemented.
- **P2 completed**: TLS check and PDF export both implemented.
- **No AI/LLM integration**: Per spec, no external APIs or machine learning used. All logic is deterministic Python.
- **No authentication**: Per spec, no user accounts or multi-user support. Single-user local application.

## Data Design Decisions

- **Sample datasets**: Fictional data created for demonstration purposes only, as stated in the spec.
- **Default scenarios**: 5/10/15 years as specified in the spec.
- **Algorithm options**: Limited to the exact list in Section 5.4 of the spec.
- **Migration complexity**: Informational only (Low/Medium/High) - does not affect calculations per spec.

## Testing Decisions

- **pytest**: Chosen as the test runner as specified in the spec.
- **Test coverage**: All Section 13 test cases implemented and passing.
- **Validation test approach**: Uses __new__ to create invalid objects for testing validation function, bypassing __post_init__ validation.

## Future Considerations

- **Post-quantum key exchange detection**: Not implemented in v1 as noted in the spec (FUTURE).
- **Signature/forgery risk**: Not in scope for v1 (confidentiality only per spec).
- **CBOM scanning**: Not implemented (FUTURE per spec).
- **Multi-user deployment**: Not implemented (out of scope per spec).
