"""Roadmap generation module for QShield."""

from typing import List

from qshield.models import Asset
from qshield.risk import calculate_all_profiles, calculate_required_completion, calculate_gap


STANDARDS_NOTE = "NIST has standardized ML-KEM (FIPS 203) for key establishment, and ML-DSA (FIPS 204) and SLH-DSA (FIPS 205) for digital signatures. Consult a qualified professional before choosing a migration approach."


def generate_roadmap(
    assets: List[Asset],
    scenarios: tuple[float, float, float],
) -> dict[str, List[str]]:
    """Generate four-phase roadmap per Section 8.2."""
    a, b, c = scenarios
    profiles = calculate_all_profiles(assets, a, b, c)
    ranked_profiles = sorted([p for p in profiles if p.asset.is_ranked], key=lambda x: x.rank or 0)
    
    roadmap = {
        "Discover": [],
        "Prioritize": [],
        "Plan": [],
        "Migrate and validate": [],
    }
    
    # Phase 1: Discover
    for asset in assets:
        if asset.algorithm == "Unknown" or asset.algorithm_source == "user_estimate":
            roadmap["Discover"].append(f"Confirm the algorithm for {asset.asset_name}.")
    
    # Phase 2: Prioritize
    for profile in ranked_profiles:
        roadmap["Prioritize"].append(
            f"{profile.rank}. {profile.asset.asset_name} - Priority: {profile.priority_label}"
        )
    
    # Phase 3: Plan
    for profile in ranked_profiles:
        asset = profile.asset
        items = []
        items.append(f"Migration estimate: {asset.migration_years} years (user estimate). Complexity: {asset.migration_complexity}. Owner: ______ (to be assigned).")
        
        # Required completion for each scenario
        for scenario_name, scenario_z in [("A", a), ("B", b), ("C", c)]:
            required = calculate_required_completion(asset.confidentiality_years, scenario_z)
            if required <= 0:
                items.append(f"Scenario {scenario_name}: Under this scenario, the confidentiality requirement already extends past the assumed threat horizon even with immediate migration.")
            else:
                gap = calculate_gap(asset.migration_years, required)
                if gap > 0:
                    items.append(f"Scenario {scenario_name}: Must complete within {required:.1f} years. Current estimate is {gap:.1f} years too slow.")
                elif gap < 0:
                    items.append(f"Scenario {scenario_name}: Must complete within {required:.1f} years. Current estimate is {abs(gap):.1f} years faster than required.")
                else:
                    items.append(f"Scenario {scenario_name}: Must complete within {required:.1f} years. Current estimate meets the timeline exactly.")
        
        roadmap["Plan"].append(f"{asset.asset_name}:")
        roadmap["Plan"].extend([f"  - {item}" for item in items])
    
    # Phase 4: Migrate and validate
    for profile in ranked_profiles:
        roadmap["Migrate and validate"].append(
            f"Evaluate a migration path for {profile.asset.asset_name} using NIST-standardized mechanisms and validate after the change."
        )
    
    roadmap["Migrate and validate"].append(STANDARDS_NOTE)
    
    return roadmap


def format_roadmap_markdown(roadmap: dict[str, List[str]]) -> str:
    """Format roadmap as Markdown."""
    lines = []
    
    phase_descriptions = {
        "Discover": "Inventory systems, cryptographic algorithms, certificates and sensitive data.",
        "Prioritize": "Identify assets with long confidentiality requirements and quantum-vulnerable cryptographic dependencies.",
        "Plan": "Estimate migration effort, identify dependencies and assign responsibilities.",
        "Migrate and validate": "Plan the transition to appropriate post-quantum cryptographic standards and verify the new configuration works correctly.",
    }
    
    for phase_name, phase_descriptions in phase_descriptions.items():
        lines.append(f"## {phase_name}")
        lines.append(f"{phase_descriptions}")
        lines.append("")
        
        if roadmap[phase_name]:
            for item in roadmap[phase_name]:
                lines.append(f"- {item}")
        else:
            lines.append("- No items for this phase.")
        lines.append("")
    
    return "\n".join(lines)
