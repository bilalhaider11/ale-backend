from dataclasses import dataclass
from typing import Optional, ClassVar
from enum import StrEnum
from datetime import datetime
from rococo.models import VersionedModel


class OrganizationPartnershipStatusEnum(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DECLINED = "declined"
    REVOKED = "revoked"
    CANCELLED = "cancelled"

    def __repr__(self):
        return str(self.value)

    @classmethod
    def values(cls):
        return [v.value for v in cls.__members__.values() if isinstance(v, cls)]

@dataclass
class OrganizationPartnership(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    requesting_organization_id: Optional[str] = None
    organization_1_id: Optional[str] = None
    organization_2_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    requested_by_id: Optional[str] = None
    responded_by_id: Optional[str] = None
    created_at: Optional[datetime] = None

    # Override prepare_for_save
    def prepare_for_save(self, *args, **kwargs):
        super().prepare_for_save(*args, **kwargs)
        # Check if organization_1_id is less than organization_2_id canonically
        if self.organization_1_id and self.organization_2_id:
            if self.organization_1_id > self.organization_2_id:
                # Swap the IDs to maintain canonical order
                self.organization_1_id, self.organization_2_id = (
                    self.organization_2_id,
                    self.organization_1_id,
                )

    def validate_created_at(self):
        if not self.created_at or self.created_at is None:
            self.created_at = datetime.utcnow()

    def organization_can_transition_status(self, new_status: OrganizationPartnershipStatusEnum, acting_organization_id: str) -> bool:
        """Returns True if current status can transition to `new_status`."""

        if acting_organization_id not in (self.organization_1_id, self.organization_2_id):
            return False

        elif acting_organization_id == self.requesting_organization_id:
            # If acting organization is the requesting organization, it can only transition from PENDING to CANCELLED
            if self.status == OrganizationPartnershipStatusEnum.PENDING:
                return new_status in {OrganizationPartnershipStatusEnum.CANCELLED}
            elif self.status == OrganizationPartnershipStatusEnum.ACTIVE:
                return new_status in {OrganizationPartnershipStatusEnum.REVOKED}
            elif self.status == OrganizationPartnershipStatusEnum.DECLINED:
                return new_status in {OrganizationPartnershipStatusEnum.PENDING}
            elif self.status == OrganizationPartnershipStatusEnum.REVOKED:
                return new_status in {OrganizationPartnershipStatusEnum.PENDING}
            elif self.status == OrganizationPartnershipStatusEnum.CANCELLED:
                return new_status in {OrganizationPartnershipStatusEnum.PENDING}
        else:
            # If acting organization is the other organization, it can only transition from PENDING to ACTIVE or DECLINED
            if self.status == OrganizationPartnershipStatusEnum.PENDING:
                return new_status in {OrganizationPartnershipStatusEnum.ACTIVE, OrganizationPartnershipStatusEnum.DECLINED}
            elif self.status == OrganizationPartnershipStatusEnum.ACTIVE:
                return new_status in {OrganizationPartnershipStatusEnum.REVOKED}
            elif self.status == OrganizationPartnershipStatusEnum.DECLINED:
                return new_status in {OrganizationPartnershipStatusEnum.PENDING}
            elif self.status == OrganizationPartnershipStatusEnum.REVOKED:
                return new_status in {OrganizationPartnershipStatusEnum.PENDING}
            elif self.status == OrganizationPartnershipStatusEnum.CANCELLED:
                return new_status in {OrganizationPartnershipStatusEnum.PENDING}
        
        return False