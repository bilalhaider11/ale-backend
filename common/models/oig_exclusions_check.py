from dataclasses import dataclass
from typing import Optional
from datetime import date
from rococo.models.versioned_model import VersionedModel

@dataclass(kw_only=True)
class OigExclusionsCheck(VersionedModel):
    """
    Logs the execution of the OIG LEIE database update check.
    This is a VersionedModel to maintain a history of checks.
    """
    # Status of the check. Possible values:
    # 'imported', 'import_failed', 'no_update', 'check_failed'
    status: str = None

    # The 'Last Update' date found on the OIG webpage during the check.
    last_update_on_webpage: Optional[date] = None
