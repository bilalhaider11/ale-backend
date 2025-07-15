from rococo.models import PersonOrganizationRole as BasePersonOrganizationRole
from enum import Enum


class PersonOrganizationRoleEnum(str, Enum):
    ADMIN = 'admin'
    INTAKE = 'intake'
    SCHEDULER = 'scheduler'
    BILLING = 'billing'
    PAYROLL = 'payroll'
    RN = 'rn'
    AUDITOR = 'auditor'
    CAREGIVER = 'caregiver'
    EMPLOYEE = 'employee'

    @classmethod
    def valid_values(cls):
        return [role.value for role in cls]


class PersonOrganizationRole(BasePersonOrganizationRole):
    pass
