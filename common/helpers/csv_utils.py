from typing import Optional
import pandas as pd
from datetime import date, datetime


def clean_string(value) -> Optional[str]:
    """Clean string values from CSV data"""
    if value is None or pd.isna(value):
        return None
    
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def parse_date(date_str) -> Optional[date]:
    """Parse date string to date object"""
    if not date_str or pd.isna(date_str):
        return None
    
    try:
        # Try common date formats
        for fmt in ['%Y%m%d', '%m/%d/%Y', '%Y-%m-%d']:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except ValueError:
                continue
        return None
    except Exception:
        return None


def parse_date_string(date_str) -> Optional[str]:
    """Parse date string and return as string for storage"""
    if not date_str or pd.isna(date_str):
        return None
    
    try:
        # Try common date formats
        for fmt in ['%Y%m%d', '%m/%d/%Y', '%Y-%m-%d']:
            try:
                dt = datetime.strptime(str(date_str), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        # If no format matches, return the cleaned string
        return clean_string(date_str)
    except Exception:
        return clean_string(date_str)
