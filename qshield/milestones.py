"""India milestone overlay module for QShield (P1)."""

from datetime import datetime
from typing import Optional

from qshield.models import MILESTONE_YEARS


MILESTONE_NOTE = "Milestone years are taken from a DST summary of India's National Quantum Mission task force roadmap. They are national roadmap targets, not a verified legal obligation for your organization. Check the original report."


def get_current_year() -> int:
    """Get the current year from system clock."""
    return datetime.now().year


def calculate_planned_completion_year(migration_years: float) -> int:
    """Calculate planned completion year.
    
    Rounds up to a whole year.
    """
    current_year = get_current_year()
    return current_year + int(migration_years) + (1 if migration_years % 1 > 0 else 0)


def compare_with_milestone(planned_year: int, milestone: str) -> str:
    """Compare planned completion year with milestone.
    
    Returns a descriptive string.
    """
    if milestone == "none":
        return ""
    
    target_year = MILESTONE_YEARS.get(milestone)
    if target_year is None:
        return ""
    
    if planned_year <= target_year:
        return f"Planned completion {planned_year} is on or before the {milestone} ({target_year})."
    else:
        return f"Planned completion {planned_year} is after the {milestone} ({target_year})."


def generate_milestone_overlay_text(asset_name: str, migration_years: float, milestone: str) -> Optional[str]:
    """Generate milestone overlay text for an asset."""
    if milestone == "none":
        return None
    
    planned_year = calculate_planned_completion_year(migration_years)
    comparison = compare_with_milestone(planned_year, milestone)
    
    if comparison:
        return f"{asset_name}: {comparison}"
    return None
