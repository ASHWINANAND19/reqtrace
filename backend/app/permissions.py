"""Which roles may perform which actions (FR-12). Enforced on the server by deps.require_roles."""
from app.models import Role

ALL_ROLES = tuple(Role)
ADMIN_ONLY = (Role.ADMIN,)

MANAGE_INPUT = (Role.ANALYST, Role.ADMIN)
EDIT_SRS = (Role.ANALYST, Role.ADMIN)
APPROVE_SRS = (Role.ANALYST, Role.ADMIN)
GENERATE_TESTS = (Role.QA, Role.ANALYST, Role.ADMIN)
EDIT_TESTS = (Role.QA, Role.ANALYST, Role.ADMIN)
GENERATE_DIAGRAMS = (Role.DEVELOPER, Role.ANALYST, Role.ADMIN)
