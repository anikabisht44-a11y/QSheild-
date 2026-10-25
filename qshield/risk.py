"""Risk engine implementing Mosca's inequality and ranking logic."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from qshield.models import Asset, RANKED_CLASSES


@dataclass
class RiskResult:
    """Risk calculation result for a single asset under a single scenario."""
    exposure_sum: float  # X + Y
    exposed: bool  # (X + Y) > Z
    margin: float  # Z - (X + Y)
    required_completion_years: float  # Z - X
    gap_years: Optional[float]  # Y - required_completion_years (if required > 0)


@dataclass
class AssetRiskProfile:
    """Complete risk profile for an asset across all scenarios."""
    asset: Asset
    results_a: RiskResult
    results_b: RiskResult
    results_c: RiskResult
    priority_label: str  # Critical, High, Medium, Lower
    exposed_count: int  # Number of scenarios where exposed
    rank: Optional[int] = None  # Rank in the ordered list


def calculate_exposure_sum(asset: Asset) -> float:
    """Calculate X + Y (exposure sum)."""
    return asset.confidentiality_years + asset.migration_years


def is_exposed(exposure_sum: float, scenario_z: float) -> bool:
    """Check if asset is exposed under scenario Z.
    
    Strict greater-than: (X + Y) > Z
    """
    return exposure_sum > scenario_z


def calculate_margin(exposure_sum: float, scenario_z: float) -> float:
    """Calculate margin: Z - (X + Y).
    
    Negative = exposed, 0 = boundary (not exposed), positive = not exposed.
    """
    return scenario_z - exposure_sum


def calculate_required_completion(confidentiality_years: float, scenario_z: float) -> float:
    """Calculate required completion years: Z - X."""
    return scenario_z - confidentiality_years


def calculate_gap(migration_years: float, required_completion: float) -> Optional[float]:
    """Calculate gap: Y - required_completion.
    
    Returns None if required_completion <= 0.
    """
    if required_completion <= 0:
        return None
    return migration_years - required_completion


def calculate_risk_for_scenario(asset: Asset, scenario_z: float) -> RiskResult:
    """Calculate risk for a single asset under a single scenario."""
    exposure_sum = calculate_exposure_sum(asset)
    exposed = is_exposed(exposure_sum, scenario_z)
    margin = calculate_margin(exposure_sum, scenario_z)
    required_completion = calculate_required_completion(asset.confidentiality_years, scenario_z)
    gap = calculate_gap(asset.migration_years, required_completion)
    
    return RiskResult(
        exposure_sum=exposure_sum,
        exposed=exposed,
        margin=margin,
        required_completion_years=required_completion,
        gap_years=gap,
    )


def calculate_priority_label(exposed_count: int) -> str:
    """Get priority label based on number of scenarios where exposed.
    
    Section 5.6:
    - 3 scenarios exposed: Critical
    - 2 scenarios exposed: High
    - 1 scenario exposed: Medium
    - 0 scenarios exposed: Lower
    """
    if exposed_count == 3:
        return "Critical"
    elif exposed_count == 2:
        return "High"
    elif exposed_count == 1:
        return "Medium"
    else:
        return "Lower"


def calculate_asset_profile(asset: Asset, scenario_a: float, scenario_b: float, scenario_c: float) -> AssetRiskProfile:
    """Calculate complete risk profile for an asset across all scenarios."""
    results_a = calculate_risk_for_scenario(asset, scenario_a)
    results_b = calculate_risk_for_scenario(asset, scenario_b)
    results_c = calculate_risk_for_scenario(asset, scenario_c)
    
    exposed_count = sum([results_a.exposed, results_b.exposed, results_c.exposed])
    priority_label = calculate_priority_label(exposed_count)
    
    return AssetRiskProfile(
        asset=asset,
        results_a=results_a,
        results_b=results_b,
        results_c=results_c,
        priority_label=priority_label,
        exposed_count=exposed_count,
    )


def rank_assets(assets: list[Asset]) -> list[Asset]:
    """Rank assets according to Section 5.5.
    
    Only rank assets in RANKED_CLASSES.
    Sort by:
    1. X + Y descending
    2. Tie-break 1: higher X first
    3. Tie-break 2: asset_name ascending, case-insensitive
    """
    ranked = [a for a in assets if a.is_ranked]
    
    def sort_key(asset: Asset):
        exposure_sum = calculate_exposure_sum(asset)
        return (-exposure_sum, -asset.confidentiality_years, asset.asset_name.lower())
    
    return sorted(ranked, key=sort_key)


def calculate_all_profiles(assets: list[Asset], scenario_a: float, scenario_b: float, scenario_c: float) -> list[AssetRiskProfile]:
    """Calculate risk profiles for all assets and assign ranks."""
    ranked_assets = rank_assets(assets)
    
    # Create a mapping for quick lookup
    asset_rank = {asset.asset_name.lower(): i + 1 for i, asset in enumerate(ranked_assets)}
    
    profiles = []
    for asset in assets:
        profile = calculate_asset_profile(asset, scenario_a, scenario_b, scenario_c)
        if asset.is_ranked:
            profile.rank = asset_rank.get(asset.asset_name.lower())
        profiles.append(profile)
    
    return profiles


def validate_asset(asset: Asset) -> list[str]:
    """Validate an asset and return list of error messages.
    
    Returns empty list if valid.
    """
    errors = []
    
    try:
        if not (1 <= len(asset.asset_name) <= 80):
            errors.append("Asset name must be 1-80 characters")
    except Exception:
        errors.append("Invalid asset name")
    
    try:
        if not (1 <= len(asset.data_category) <= 60):
            errors.append("Data category must be 1-60 characters")
    except Exception:
        errors.append("Invalid data category")
    
    try:
        if not (0.5 <= asset.confidentiality_years <= 100):
            errors.append("Confidentiality years must be between 0.5 and 100")
    except Exception:
        errors.append("Invalid confidentiality years")
    
    try:
        if asset.algorithm not in ["RSA-2048", "RSA-3072", "RSA-4096", "ECC P-256", "ECC P-384", 
                                     "Diffie-Hellman", "Unknown", "ML-KEM (FIPS 203)", 
                                     "Hybrid (classical + ML-KEM)", "AES-128", "AES-256"]:
            errors.append("Invalid algorithm")
    except Exception:
        errors.append("Invalid algorithm")
    
    try:
        if asset.migration_complexity not in ["Low", "Medium", "High"]:
            errors.append("Migration complexity must be Low, Medium, or High")
    except Exception:
        errors.append("Invalid migration complexity")
    
    try:
        if not (0.5 <= asset.migration_years <= 30):
            errors.append("Migration years must be between 0.5 and 30")
    except Exception:
        errors.append("Invalid migration years")
    
    try:
        if asset.algorithm_source not in ["user_estimate", "confirmed"]:
            errors.append("Algorithm source must be user_estimate or confirmed")
    except Exception:
        errors.append("Invalid algorithm source")
    
    return errors


def validate_scenario(value: float) -> list[str]:
    """Validate a scenario value (Z)."""
    errors = []
    if not (1 <= value <= 50):
        errors.append("Scenario value must be between 1 and 50")
    return errors


def get_required_completion_text(required_completion: float, gap: Optional[float]) -> str:
    """Generate text for required completion per Section 5.3."""
    if required_completion <= 0:
        return "Under this scenario, the confidentiality requirement already extends past the assumed threat horizon even with immediate migration."
    
    if gap is None:
        gap = 0
    
    if gap > 0:
        return f"Migration estimate is {gap:.1f} years too slow."
    elif gap < 0:
        return f"Migration estimate is {abs(gap):.1f} years faster than required."
    else:
        return "Migration estimate meets the required timeline exactly."
