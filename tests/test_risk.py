"""Test cases for the risk engine per Section 13."""

import pytest
from qshield.models import Asset
from qshield.risk import (
    calculate_exposure_sum,
    is_exposed,
    calculate_margin,
    calculate_required_completion,
    calculate_gap,
    calculate_risk_for_scenario,
    calculate_priority_label,
    calculate_asset_profile,
    rank_assets,
    validate_asset,
    validate_scenario,
    get_required_completion_text,
)


def test_example_exposed():
    """Test: X=20, Y=3, Z=15 -> exposure_sum 23, exposed True, margin -8"""
    asset = Asset(
        asset_name="Test Asset",
        data_category="Test",
        confidentiality_years=20.0,
        algorithm="RSA-2048",
        migration_complexity="Medium",
        migration_years=3.0,
    )
    result = calculate_risk_for_scenario(asset, 15.0)
    
    assert result.exposure_sum == 23.0
    assert result.exposed is True
    assert result.margin == -8.0


def test_not_exposed():
    """Test: X=1, Y=1, Z=5 -> sum 2, exposed False, margin +3"""
    asset = Asset(
        asset_name="Test Asset",
        data_category="Test",
        confidentiality_years=1.0,
        algorithm="RSA-2048",
        migration_complexity="Low",
        migration_years=1.0,
    )
    result = calculate_risk_for_scenario(asset, 5.0)
    
    assert result.exposure_sum == 2.0
    assert result.exposed is False
    assert result.margin == 3.0


def test_boundary_not_exposed():
    """Test: X=7, Y=3, Z=10 -> sum 10, exposed False, margin 0"""
    asset = Asset(
        asset_name="Test Asset",
        data_category="Test",
        confidentiality_years=7.0,
        algorithm="RSA-2048",
        migration_complexity="Medium",
        migration_years=3.0,
    )
    result = calculate_risk_for_scenario(asset, 10.0)
    
    assert result.exposure_sum == 10.0
    assert result.exposed is False  # Strict greater-than
    assert result.margin == 0.0


def test_label_critical():
    """Test: X=30, Y=3, scenarios 5/10/15 -> exposed in 3 -> Critical"""
    asset = Asset(
        asset_name="Test Asset",
        data_category="Test",
        confidentiality_years=30.0,
        algorithm="RSA-2048",
        migration_complexity="High",
        migration_years=3.0,
    )
    profile = calculate_asset_profile(asset, 5.0, 10.0, 15.0)
    
    assert profile.exposed_count == 3
    assert profile.priority_label == "Critical"


def test_label_high():
    """Test: X=10, Y=2, scenarios 5/10/15 -> sum 12, exposed in 2 -> High"""
    asset = Asset(
        asset_name="Test Asset",
        data_category="Test",
        confidentiality_years=10.0,
        algorithm="RSA-2048",
        migration_complexity="Medium",
        migration_years=2.0,
    )
    profile = calculate_asset_profile(asset, 5.0, 10.0, 15.0)
    
    assert profile.exposure_sum == 12.0
    assert profile.exposed_count == 2
    assert profile.priority_label == "High"


def test_label_medium():
    """Test: X=4, Y=3, scenarios 5/10/15 -> sum 7, exposed in 1 -> Medium"""
    asset = Asset(
        asset_name="Test Asset",
        data_category="Test",
        confidentiality_years=4.0,
        algorithm="RSA-2048",
        migration_complexity="Medium",
        migration_years=3.0,
    )
    profile = calculate_asset_profile(asset, 5.0, 10.0, 15.0)
    
    assert profile.exposure_sum == 7.0
    assert profile.exposed_count == 1
    assert profile.priority_label == "Medium"


def test_label_lower():
    """Test: X=1, Y=1, scenarios 5/10/15 -> sum 2, exposed in 0 -> Lower"""
    asset = Asset(
        asset_name="Test Asset",
        data_category="Test",
        confidentiality_years=1.0,
        algorithm="RSA-2048",
        migration_complexity="Low",
        migration_years=1.0,
    )
    profile = calculate_asset_profile(asset, 5.0, 10.0, 15.0)
    
    assert profile.exposure_sum == 2.0
    assert profile.exposed_count == 0
    assert profile.priority_label == "Lower"


def test_required_completion():
    """Test: X=20, Z=15 -> required_completion_years -5 (<= 0 text rule applies)"""
    required = calculate_required_completion(20.0, 15.0)
    assert required == -5.0
    
    text = get_required_completion_text(required, None)
    assert "already extends past" in text.lower()


def test_required_completion_gap():
    """Test: X=5, Y=8, Z=10 -> required 5, gap 3"""
    required = calculate_required_completion(5.0, 10.0)
    assert required == 5.0
    
    gap = calculate_gap(8.0, required)
    assert gap == 3.0
    
    text = get_required_completion_text(required, gap)
    assert "3.0" in text
    assert "too slow" in text.lower()


def test_ranking_order_college():
    """Test: college sample -> order per Section 12.3"""
    assets = [
        Asset("Student academic records", "Student records", 40.0, "RSA-2048", "High", 3.0),
        Asset("Research data and IP", "Research", 20.0, "ECC P-256", "Medium", 2.0),
        Asset("Alumni contact database", "Personal data", 10.0, "ECC P-256", "Low", 1.0),
        Asset("Fee payment records", "Financial", 8.0, "RSA-2048", "Medium", 2.0),
        Asset("Exam question papers", "Academic confidential", 1.0, "RSA-2048", "Low", 1.0),
        Asset("Internal knowledge wiki", "Internal documents", 3.0, "AES-256", "Low", 1.0),
    ]
    
    ranked = rank_assets(assets)
    
    # Check order (excluding AES-256 which is not ranked)
    assert len(ranked) == 5
    assert ranked[0].asset_name == "Student academic records"
    assert ranked[1].asset_name == "Research data and IP"
    assert ranked[2].asset_name == "Alumni contact database"
    assert ranked[3].asset_name == "Fee payment records"
    assert ranked[4].asset_name == "Exam question papers"


def test_ranking_tiebreak():
    """Test: two assets, same X+Y, different X -> higher X ranks first"""
    assets = [
        Asset("Asset A", "Test", 10.0, "RSA-2048", "Medium", 5.0),  # X+Y = 15
        Asset("Asset B", "Test", 12.0, "RSA-2048", "Medium", 3.0),  # X+Y = 15, higher X
    ]
    
    ranked = rank_assets(assets)
    
    assert ranked[0].asset_name == "Asset B"  # Higher X wins
    assert ranked[1].asset_name == "Asset A"


def test_symmetric_not_ranked():
    """Test: algorithm AES-256 -> not in ranked list, reason text present"""
    asset = Asset(
        asset_name="Test Asset",
        data_category="Test",
        confidentiality_years=10.0,
        algorithm="AES-256",
        migration_complexity="Low",
        migration_years=1.0,
    )
    
    assert asset.is_ranked is False
    assert "symmetric" in asset.not_ranked_reason.lower()


def test_unknown_is_ranked():
    """Test: algorithm Unknown -> ranked with warning flag"""
    asset = Asset(
        asset_name="Test Asset",
        data_category="Test",
        confidentiality_years=10.0,
        algorithm="Unknown",
        migration_complexity="Medium",
        migration_years=2.0,
    )
    
    assert asset.is_ranked is True
    assert asset.algorithm_class == "unknown_assumed_vulnerable"


def test_validation_rejects():
    """Test: X=0, Y=0, duplicate name, bad algorithm -> each returns an error"""
    # X too small
    asset1 = Asset("Test", "Test", 0.0, "RSA-2048", "Low", 1.0)
    errors1 = validate_asset(asset1)
    assert len(errors1) > 0
    
    # Y too small
    asset2 = Asset("Test", "Test", 5.0, "RSA-2048", "Low", 0.0)
    errors2 = validate_asset(asset2)
    assert len(errors2) > 0
    
    # Bad algorithm
    asset3 = Asset("Test", "Test", 5.0, "BadAlgo", "Low", 1.0)
    errors3 = validate_asset(asset3)
    assert len(errors3) > 0


def test_report_has_disclaimers():
    """Test: any dataset -> report contains exact Section 4.2 scenario and general disclaimer strings"""
    from qshield.report import generate_markdown_report
    
    assets = [
        Asset("Test Asset", "Test", 10.0, "RSA-2048", "Medium", 2.0),
    ]
    
    report = generate_markdown_report(
        org_name="Test Org",
        org_type="Education",
        assets=assets,
        scenarios=(5.0, 10.0, 15.0),
        milestone="none",
    )
    
    # Scenario disclaimer
    assert "Planning scenarios are hypothetical" in report
    assert "not predictions" in report
    
    # General disclaimer
    assert "QShield is a planning aid" in report
    assert "not a substitute for a qualified security assessment" in report


def test_no_forbidden_phrases():
    """Test: generated report text -> contains none of the Section 4.4 phrases"""
    from qshield.report import generate_markdown_report
    
    assets = [
        Asset("Test Asset", "Test", 10.0, "RSA-2048", "Medium", 2.0),
    ]
    
    report = generate_markdown_report(
        org_name="Test Org",
        org_type="Education",
        assets=assets,
        scenarios=(5.0, 10.0, 15.0),
        milestone="none",
    )
    
    forbidden_phrases = [
        "quantum-safe",
        "quantum-proof",
        "unbreakable",
        "guaranteed secure",
        "First",
        "only",
        "novel",
        "no existing solution",
        "revolutionary",
        "Compliant with",
        "certified by",
    ]
    
    report_lower = report.lower()
    for phrase in forbidden_phrases:
        assert phrase.lower() not in report_lower, f"Found forbidden phrase: {phrase}"
