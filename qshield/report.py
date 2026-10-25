"""Report generation module for QShield."""

from datetime import datetime
from typing import Optional

from qshield.models import Asset
from qshield.risk import calculate_all_profiles, calculate_exposure_sum


# Approved reference text per Section 4.2
SCENARIO_DISCLAIMER = "Planning scenarios are hypothetical and are not predictions of when a cryptographically relevant quantum computer will exist."
GENERAL_DISCLAIMER = "QShield is a planning aid. Results depend on user-entered estimates and hypothetical scenarios. It does not determine legal compliance and is not a substitute for a qualified security assessment."
DPDP_NOTE = "The Digital Personal Data Protection Act, 2023 may be relevant to organizations that process personal data. QShield does not determine whether it applies to you and does not provide legal advice."
STANDARDS_NOTE = "NIST has standardized ML-KEM (FIPS 203) for key establishment, and ML-DSA (FIPS 204) and SLH-DSA (FIPS 205) for digital signatures. Consult a qualified professional before choosing a migration approach."


def generate_asset_explanation(asset: Asset, scenarios: tuple[float, float, float]) -> str:
    """Generate per-asset explanation per Section 8.1 template."""
    x = asset.confidentiality_years
    y = asset.migration_years
    exposure_sum = calculate_exposure_sum(asset)
    algorithm_class = asset.algorithm_class
    a, b, c = scenarios
    
    # Calculate exposure for each scenario
    exposed_a = "EXPOSED" if exposure_sum > a else "not exposed"
    margin_a = a - exposure_sum
    exposed_b = "EXPOSED" if exposure_sum > b else "not exposed"
    margin_b = b - exposure_sum
    exposed_c = "EXPOSED" if exposure_sum > c else "not exposed"
    margin_c = c - exposure_sum
    
    # Count exposed scenarios
    exposed_count = sum([exposure_sum > a, exposure_sum > b, exposure_sum > c])
    
    # Priority label
    if exposed_count == 3:
        label = "Critical"
    elif exposed_count == 2:
        label = "High"
    elif exposed_count == 1:
        label = "Medium"
    else:
        label = "Lower"
    
    # Reason sentence
    if exposed_count == 0:
        reason = f"The exposure sum ({exposure_sum} years) does not exceed any of the three scenario values."
    else:
        reason = f"The exposure sum ({exposure_sum} years) exceeds the scenario value in {exposed_count} of 3 scenarios, so early migration planning is advisable under those assumptions."
    
    if algorithm_class == "unknown_assumed_vulnerable":
        reason += " The algorithm is unknown and was treated as quantum-vulnerable."
    
    explanation = f"""{asset.asset_name} ({asset.data_category})
- Confidentiality requirement (X): {x} years [user estimate]
- Estimated migration duration (Y): {y} years [user estimate]
- Exposure sum (X + Y): {exposure_sum} years
- Algorithm: {asset.algorithm} - class: {algorithm_class} [{asset.algorithm_source}]
- Scenario A (Z = {a}): {exposed_a} (margin {margin_a})
- Scenario B (Z = {b}): {exposed_b} (margin {margin_b})
- Scenario C (Z = {c}): {exposed_c} (margin {margin_c})
- Priority: {label} (exposed in {exposed_count} of 3 scenarios)
- Why: {reason}"""
    
    return explanation


def generate_markdown_report(
    org_name: str,
    org_type: str,
    assets: list[Asset],
    scenarios: tuple[float, float, float],
    milestone: str,
) -> str:
    """Generate Markdown report per Section 8.3."""
    a, b, c = scenarios
    profiles = calculate_all_profiles(assets, a, b, c)
    
    # Separate ranked and not ranked
    ranked_profiles = [p for p in profiles if p.asset.is_ranked]
    not_ranked_profiles = [p for p in profiles if not p.asset.is_ranked]
    
    # Count by priority
    priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Lower": 0}
    for p in ranked_profiles:
        priority_counts[p.priority_label] += 1
    
    # Build report
    lines = []
    lines.append(f"# QShield Migration Planning Report - {org_name} ({org_type})")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Scenario table
    lines.append("\n## Planning Scenarios")
    lines.append("\n| Scenario | Years until hypothetical quantum computer |")
    lines.append("|----------|-------------------------------------------|")
    lines.append(f"| A | {a} |")
    lines.append(f"| B | {b} |")
    lines.append(f"| C | {c} |")
    lines.append(f"\n{SCENARIO_DISCLAIMER}")
    
    # Summary
    lines.append("\n## Summary")
    lines.append("\n| Priority | Count |")
    lines.append("|----------|-------|")
    lines.append(f"| Critical | {priority_counts['Critical']} |")
    lines.append(f"| High | {priority_counts['High']} |")
    lines.append(f"| Medium | {priority_counts['Medium']} |")
    lines.append(f"| Lower | {priority_counts['Lower']} |")
    
    # Ranked assets table
    lines.append("\n## Ranked Assets")
    lines.append("\n| Rank | Asset | Category | X | Y | X+Y | Algorithm | Exposed in | Priority |")
    lines.append("|------|-------|----------|---|---|-----|-----------|------------|----------|")
    
    for p in sorted(ranked_profiles, key=lambda x: x.rank or 0):
        lines.append(
            f"| {p.rank} | {p.asset.asset_name} | {p.asset.data_category} | "
            f"{p.asset.confidentiality_years} | {p.asset.migration_years} | "
            f"{p.results_a.exposure_sum} | {p.asset.algorithm} | "
            f"{p.exposed_count} of 3 | {p.priority_label} |"
        )
    
    # Not ranked assets
    if not_ranked_profiles:
        lines.append("\n## Not Ranked Assets")
        lines.append("\n| Asset | Category | Algorithm | Reason |")
        lines.append("|-------|----------|-----------|--------|")
        for p in not_ranked_profiles:
            lines.append(
                f"| {p.asset.asset_name} | {p.asset.data_category} | "
                f"{p.asset.algorithm} | {p.asset.not_ranked_reason} |"
            )
    
    # Assumptions
    lines.append("\n## Assumptions")
    lines.append("\nAll inputs are user estimates unless marked as confirmed.")
    lines.append("\n| Asset | Confidentiality (X) | Migration (Y) | Algorithm |")
    lines.append("|-------|-------------------|---------------|-----------|")
    for asset in assets:
        lines.append(
            f"| {asset.asset_name} | {asset.confidentiality_years} years [user estimate] | "
            f"{asset.migration_years} years [user estimate] | {asset.algorithm} [{asset.algorithm_source}] |"
        )
    
    # Per-asset explanations
    lines.append("\n## Per-Asset Explanations")
    for asset in assets:
        lines.append("\n### " + asset.asset_name)
        explanation = generate_asset_explanation(asset, scenarios)
        lines.append(explanation)
    
    # Roadmap placeholder (will be filled by roadmap module)
    lines.append("\n## Migration Roadmap")
    lines.append("\n*See Roadmap tab in the application for the detailed four-phase roadmap.*")
    
    # Reference notes
    lines.append("\n## Reference Notes")
    lines.append(f"\n{STANDARDS_NOTE}")
    lines.append(f"\n{DPDP_NOTE}")
    
    # India milestone (P1)
    if milestone != "none":
        lines.append(f"\n**India Milestone Overlay:** {milestone}")
        lines.append("\nMilestone years are taken from a DST summary of India's National Quantum Mission task force roadmap. They are national roadmap targets, not a verified legal obligation for your organization. Check the original report.")
    
    # Limitations
    lines.append("\n## Limitations")
    lines.append(f"\n{GENERAL_DISCLAIMER}")
    lines.append("\nv1 covers confidentiality (harvest-now-decrypt-later) only; it does not assess signature/forgery risk, symmetric-key weaknesses, or software defects.")
    
    return "\n".join(lines)


def generate_pdf_report(markdown_content: str, output_path: str) -> None:
    """Generate PDF report from Markdown content using fpdf2."""
    try:
        from fpdf import FPDF
        from markdown import markdown
    except ImportError:
        raise ImportError("fpdf2 and markdown packages required for PDF export. Install with: pip install fpdf2 markdown")
    
    # Convert Markdown to HTML
    html_content = markdown(markdown_content)
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Simple text extraction (for MVP - proper HTML rendering would be more complex)
    # For now, we'll write the markdown as plain text with basic formatting
    lines = markdown_content.split('\n')
    
    for line in lines:
        if line.startswith('# '):
            pdf.set_font("Arial", 'B', 16)
            pdf.ln(5)
            pdf.write(5, line[2:] + '\n')
            pdf.ln(5)
        elif line.startswith('## '):
            pdf.set_font("Arial", 'B', 14)
            pdf.ln(5)
            pdf.write(5, line[3:] + '\n')
            pdf.ln(3)
        elif line.startswith('### '):
            pdf.set_font("Arial", 'B', 12)
            pdf.ln(3)
            pdf.write(5, line[4:] + '\n')
            pdf.ln(2)
        elif line.startswith('|'):
            pdf.set_font("Arial", size=8)
            pdf.write(4, line + '\n')
        elif line.startswith('-'):
            pdf.set_font("Arial", size=10)
            pdf.write(5, line + '\n')
        elif line.strip():
            pdf.set_font("Arial", size=10)
            pdf.write(5, line + '\n')
        else:
            pdf.ln(2)
    
    pdf.output(output_path)
