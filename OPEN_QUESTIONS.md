# OPEN_QUESTIONS.md

This file lists questions and unresolved items for future consideration.

## Unverified Items (from Section 4.3)

The following items are marked as UNVERIFIED in the spec and should not be stated as facts in the application:

- Whether a Cryptographic Bill of Materials (CBOM) becomes a procurement mandate in India from FY 2027-28 (appears in a vendor whitepaper only).
- Whether education is a named priority sector in the DST roadmap (summaries seen list government, defence, power, telecom, transport, banking and finance).
- Any statement that the DPDP Act requires post-quantum cryptography or sets a migration deadline.
- Any market-size, adoption or breach statistics.
- Any statement about competitors' pricing or internal capabilities.

## Future Enhancements

### Potential v2 Features

- **Post-quantum key exchange detection**: The TLS check currently does not detect post-quantum key exchange algorithms. This would require deeper protocol analysis.
- **Signature/forgery risk modelling**: v1 covers confidentiality (HNDL) only. Future versions could assess signature risk.
- **CBOM integration**: Automated Cryptographic Bill of Materials scanning and import.
- **Multi-user support**: Authentication, user accounts, and team collaboration features.
- **Cloud deployment**: Containerization and cloud hosting options.
- **Advanced visualizations**: More sophisticated charts and visual risk dashboards.
- **Export formats**: Additional export formats (DOCX, Excel, etc.).
- **Import formats**: Support for importing data from various formats (JSON, Excel, etc.).

### Research Questions

- **Real-world validation**: How do the rankings compare with actual organizational migration priorities?
- **User feedback**: What do actual users find most valuable in the tool?
- **Accuracy of estimates**: How do user estimates compare with actual migration timelines?
- **Scenario calibration**: What scenario values are most useful for different industries?

## Technical Debt

- **PDF rendering**: The current PDF export is basic text rendering. Could be enhanced with proper HTML-to-PDF conversion.
- **Error handling**: Could add more granular error handling and user-friendly error messages.
- **Performance**: For large asset lists (>1000), the UI might need optimization.
- **Database migrations**: No migration system in place for schema changes.
- **Test coverage**: Could add integration tests for the UI and end-to-end tests.

## Clarifications Needed

None at this time. The specification was comprehensive and clear.
