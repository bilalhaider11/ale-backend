from typing import Optional
from datetime import date, datetime


def clean_string(value) -> Optional[str]:
    """Clean string values from CSV data"""
    if value is None or value == '':
        return None
    
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def get_first_matching_column_value(row, column_headers) -> Optional[str]:
    """Get the first non-empty value from the row based on column headers matched case-insensitively"""
    for header in column_headers:
        # Check if the header exists in the row (case-insensitive)
        for key in row.keys():
            if key.lower().strip() == header.lower().strip():
                value = row.get(key)
                if value and str(value).strip():
                    return clean_string(value)
    return None

def parse_date(date_str) -> Optional[date]:
    """Parse date string to date object"""
    if not date_str or date_str == '':
        return None
    
    # Try common date formats
    for fmt in ['%Y%m%d', '%m/%d/%Y', '%Y-%m-%d']:
        try:
            return datetime.strptime(str(date_str), fmt).date()
        except ValueError:
            continue
    return None


def parse_date_string(date_str) -> Optional[str]:
    """Parse date string and return as string for storage"""
    if not date_str or date_str == '':
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
