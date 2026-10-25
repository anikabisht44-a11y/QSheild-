"""SQLite database layer for QShield."""

import sqlite3
from pathlib import Path
from typing import List, Optional

from qshield.models import Asset, Settings, MIGRATION_COMPLEXITY_OPTIONS, ORG_TYPE_OPTIONS, MILESTONE_OPTIONS


DB_NAME = "qshield.db"


def get_db_path() -> Path:
    """Get the path to the database file."""
    return Path(__file__).parent.parent / DB_NAME


def init_db() -> None:
    """Initialize the database with required tables."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Assets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            data_category TEXT NOT NULL,
            confidentiality_years REAL NOT NULL,
            algorithm TEXT NOT NULL,
            migration_complexity TEXT NOT NULL CHECK (migration_complexity IN ('Low','Medium','High')),
            migration_years REAL NOT NULL,
            algorithm_source TEXT NOT NULL DEFAULT 'user_estimate' CHECK (algorithm_source IN ('user_estimate','confirmed')),
            notes TEXT DEFAULT ''
        )
    """)
    
    conn.commit()
    conn.close()


def get_settings() -> Settings:
    """Get settings from database, or return defaults if empty."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    
    settings_dict = {row[0]: row[1] for row in rows}
    
    conn.close()
    
    return Settings(
        org_name=settings_dict.get("org_name", "Example Organization"),
        org_type=settings_dict.get("org_type", "Education"),
        scenario_a=float(settings_dict.get("scenario_a", "5.0")),
        scenario_b=float(settings_dict.get("scenario_b", "10.0")),
        scenario_c=float(settings_dict.get("scenario_c", "15.0")),
        milestone=settings_dict.get("milestone", "none"),
    )


def save_settings(settings: Settings) -> None:
    """Save settings to database."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    settings_data = [
        ("org_name", settings.org_name),
        ("org_type", settings.org_type),
        ("scenario_a", str(settings.scenario_a)),
        ("scenario_b", str(settings.scenario_b)),
        ("scenario_c", str(settings.scenario_c)),
        ("milestone", settings.milestone),
    ]
    
    for key, value in settings_data:
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))
    
    conn.commit()
    conn.close()


def get_assets() -> List[Asset]:
    """Get all assets from database."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT asset_name, data_category, confidentiality_years, algorithm,
               migration_complexity, migration_years, algorithm_source, notes
        FROM assets
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    assets = []
    for row in rows:
        assets.append(Asset(
            asset_name=row[0],
            data_category=row[1],
            confidentiality_years=row[2],
            algorithm=row[3],
            migration_complexity=row[4],
            migration_years=row[5],
            algorithm_source=row[6],
            notes=row[7] if row[7] else "",
        ))
    
    return assets


def save_asset(asset: Asset) -> None:
    """Save or update an asset in the database."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO assets
        (asset_name, data_category, confidentiality_years, algorithm,
         migration_complexity, migration_years, algorithm_source, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        asset.asset_name,
        asset.data_category,
        asset.confidentiality_years,
        asset.algorithm,
        asset.migration_complexity,
        asset.migration_years,
        asset.algorithm_source,
        asset.notes,
    ))
    
    conn.commit()
    conn.close()


def delete_asset(asset_name: str) -> None:
    """Delete an asset from the database."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM assets WHERE asset_name = ?", (asset_name,))
    
    conn.commit()
    conn.close()


def save_assets(assets: List[Asset]) -> None:
    """Save all assets to database (replaces existing)."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing assets
    cursor.execute("DELETE FROM assets")
    
    # Insert new assets
    for asset in assets:
        cursor.execute("""
            INSERT INTO assets
            (asset_name, data_category, confidentiality_years, algorithm,
             migration_complexity, migration_years, algorithm_source, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset.asset_name,
            asset.data_category,
            asset.confidentiality_years,
            asset.algorithm,
            asset.migration_complexity,
            asset.migration_years,
            asset.algorithm_source,
            asset.notes,
        ))
    
    conn.commit()
    conn.close()


def reset_database() -> None:
    """Reset the database to empty state."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM assets")
    cursor.execute("DELETE FROM settings")
    
    conn.commit()
    conn.close()
