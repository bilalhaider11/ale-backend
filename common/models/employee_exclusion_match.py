from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, ClassVar
from rococo.models import VersionedModel


@dataclass
class EmployeeExclusionMatch(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    exclusion_type: Optional[str] = None
    exclusion_date: Optional[date] = None
    match_type: Optional[str] = None
    status: str = 'pending'
    matched_entity_type: Optional[str] = None
    matched_entity_id: Optional[str] = None
    oig_exclusion_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    review_date: Optional[date] = None
    organization_id: Optional[str] = None
    s3_key: Optional[str] = None
    verification_result: Optional[str] = None
