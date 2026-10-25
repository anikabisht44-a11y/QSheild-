"""Data models and algorithm classification for QShield."""

from dataclasses import dataclass
from typing import Literal


# Algorithm classification per Section 5.4
ALGORITHM_CLASS_MAP = {
    # public_key_quantum_vulnerable
    "RSA-2048": "public_key_quantum_vulnerable",
    "RSA-3072": "public_key_quantum_vulnerable",
    "RSA-4096": "public_key_quantum_vulnerable",
    "ECC P-256": "public_key_quantum_vulnerable",
    "ECC P-384": "public_key_quantum_vulnerable",
    "Diffie-Hellman": "public_key_quantum_vulnerable",
    # unknown_assumed_vulnerable
    "Unknown": "unknown_assumed_vulnerable",
    # post_quantum_standardized
    "ML-KEM (FIPS 203)": "post_quantum_standardized",
    # post_quantum_hybrid
    "Hybrid (classical + ML-KEM)": "post_quantum_hybrid",
    # symmetric_out_of_scope
    "AES-128": "symmetric_out_of_scope",
    "AES-256": "symmetric_out_of_scope",
}

VALID_ALGORITHMS = list(ALGORITHM_CLASS_MAP.keys())

RANKED_CLASSES = {"public_key_quantum_vulnerable", "unknown_assumed_vulnerable"}

NOT_RANKED_REASONS = {
    "post_quantum_standardized": "Already uses a NIST-standardized post-quantum mechanism; verify the implementation.",
    "post_quantum_hybrid": "Uses a hybrid approach; verify the implementation.",
    "symmetric_out_of_scope": "Symmetric encryption is outside v1 scope. Review separately how its keys are established, since key establishment may use public-key cryptography.",
}

UNKNOWN_WARNING = "Algorithm unknown - treated as quantum-vulnerable until confirmed."

MIGRATION_COMPLEXITY_OPTIONS = ["Low", "Medium", "High"]

ORG_TYPE_OPTIONS = ["Healthcare", "Education", "Banking and finance", "Government services", "Small business"]

MILESTONE_OPTIONS = ["none", "2029 CII target", "2033 enterprise target"]

MILESTONE_YEARS = {
    "2029 CII target": 2029,
    "2033 enterprise target": 2033,
}


@dataclass
class Asset:
    """Represents a data asset with its cryptographic properties."""
    asset_name: str
    data_category: str
    confidentiality_years: float  # X
    algorithm: str
    migration_complexity: str
    migration_years: float  # Y
    algorithm_source: str = "user_estimate"  # "user_estimate" or "confirmed"
    notes: str = ""

    def __post_init__(self):
        """Validate asset fields."""
        if not (1 <= len(self.asset_name) <= 80):
            raise ValueError("asset_name must be 1-80 characters")
        if not (1 <= len(self.data_category) <= 60):
            raise ValueError("data_category must be 1-60 characters")
        if not (0.5 <= self.confidentiality_years <= 100):
            raise ValueError("confidentiality_years must be between 0.5 and 100")
        if self.algorithm not in VALID_ALGORITHMS:
            raise ValueError(f"algorithm must be one of {VALID_ALGORITHMS}")
        if self.migration_complexity not in MIGRATION_COMPLEXITY_OPTIONS:
            raise ValueError(f"migration_complexity must be one of {MIGRATION_COMPLEXITY_OPTIONS}")
        if not (0.5 <= self.migration_years <= 30):
            raise ValueError("migration_years must be between 0.5 and 30")
        if self.algorithm_source not in ["user_estimate", "confirmed"]:
            raise ValueError("algorithm_source must be 'user_estimate' or 'confirmed'")

    @property
    def algorithm_class(self) -> str:
        """Get the algorithm class."""
        return ALGORITHM_CLASS_MAP.get(self.algorithm, "unknown_assumed_vulnerable")

    @property
    def is_ranked(self) -> bool:
        """Check if this asset should be included in ranking."""
        return self.algorithm_class in RANKED_CLASSES

    @property
    def not_ranked_reason(self) -> str:
        """Get the reason why this asset is not ranked, if applicable."""
        if self.is_ranked:
            return ""
        return NOT_RANKED_REASONS.get(self.algorithm_class, "Unknown algorithm class")


@dataclass
class Settings:
    """Application settings."""
    org_name: str = "Example Organization"
    org_type: str = "Education"
    scenario_a: float = 5.0
    scenario_b: float = 10.0
    scenario_c: float = 15.0
    milestone: str = "none"

    def __post_init__(self):
        """Validate settings."""
        if not (1 <= self.scenario_a <= 50):
            raise ValueError("scenario_a must be between 1 and 50")
        if not (1 <= self.scenario_b <= 50):
            raise ValueError("scenario_b must be between 1 and 50")
        if not (1 <= self.scenario_c <= 50):
            raise ValueError("scenario_c must be between 1 and 50")
        if self.org_type not in ORG_TYPE_OPTIONS:
            raise ValueError(f"org_type must be one of {ORG_TYPE_OPTIONS}")
        if self.milestone not in MILESTONE_OPTIONS:
            raise ValueError(f"milestone must be one of {MILESTONE_OPTIONS}")

    @property
    def scenarios(self) -> tuple[float, float, float]:
        """Get scenarios as a tuple."""
        return (self.scenario_a, self.scenario_b, self.scenario_c)
