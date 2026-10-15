"""source review statuses and per-use permissions

Adds the licence-review statuses candidate / pending_permission / restricted, and three
separate permissions (permanent storage, search indexing, answer-assistant retrieval).
An approved source must now have ALL of them set to 'allowed'.

No Islamic content exists yet, so no real rows are affected. If an 'approved' source did
exist it would be moved to 'under_review', because it cannot satisfy the stricter rule.

Revision ID: 0002
Revises: 0001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_STATUSES = ("draft", "under_review", "approved", "rejected", "archived")
NEW_STATUSES = (
    "draft", "candidate", "pending_permission", "restricted",
    "under_review", "approved", "rejected", "archived",
)
PERMISSIONS = ("allowed", "not_allowed", "requires_permission", "unknown")

# (table, column, constraint name)
STATUS_COLUMNS = (
    ("sources", "approval_status", "ck_sources_approval_status"),
    ("source_reviews", "from_status", "ck_source_reviews_review_from_status"),
    ("source_reviews", "to_status", "ck_source_reviews_review_to_status"),
)
OLD_RULE = (
    "approval_status <> 'approved' OR (commercial_use = 'allowed' AND license_verified_at IS NOT NULL "
    "AND license_name IS NOT NULL AND rights_holder IS NOT NULL)"
)
NEW_RULE = (
    "approval_status <> 'approved' OR (commercial_use = 'allowed' AND license_verified_at IS NOT NULL "
    "AND license_name IS NOT NULL AND rights_holder IS NOT NULL "
    "AND storage_permission = 'allowed' AND indexing_permission = 'allowed' "
    "AND rag_permission = 'allowed')"
)
RULE_NAME = "ck_sources_approved_requires_verified_commercial_licence"


def _in(column: str, values: Sequence[str]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def upgrade() -> None:
    # 1. Stop enforcing the rule while we reshape the data.
    op.drop_constraint(op.f(RULE_NAME), "sources", type_="check")

    # 2. New permission columns, all 'unknown' (the safe default).
    for col in ("storage_permission", "indexing_permission", "rag_permission"):
        op.add_column(
            "sources",
            sa.Column(
                col,
                sa.Enum(*PERMISSIONS, name=col, native_enum=False, create_constraint=False, length=40),
                nullable=False,
                server_default="unknown",
            ),
        )
        op.create_check_constraint(op.f(f"ck_sources_{col}"), "sources", _in(col, PERMISSIONS))

    # 3. Allow the new statuses.
    for table, column, name in STATUS_COLUMNS:
        op.drop_constraint(op.f(name), table, type_="check")
        op.create_check_constraint(op.f(name), table, _in(column, NEW_STATUSES))

    # 4. Anything already 'approved' cannot meet the stricter rule: send it back for review.
    op.execute("UPDATE sources SET approval_status = 'under_review' WHERE approval_status = 'approved'")

    # 5. The stricter approval rule.
    op.create_check_constraint(op.f(RULE_NAME), "sources", NEW_RULE)


def downgrade() -> None:
    op.drop_constraint(op.f(RULE_NAME), "sources", type_="check")

    # Map the new statuses back onto the old set (conservatively).
    mapping = {"candidate": "draft", "pending_permission": "under_review", "restricted": "rejected"}
    for table, column, name in STATUS_COLUMNS:
        for new, old in mapping.items():
            op.execute(f"UPDATE {table} SET {column} = '{old}' WHERE {column} = '{new}'")
        op.drop_constraint(op.f(name), table, type_="check")
        op.create_check_constraint(op.f(name), table, _in(column, OLD_STATUSES))

    for col in ("rag_permission", "indexing_permission", "storage_permission"):
        op.drop_constraint(op.f(f"ck_sources_{col}"), "sources", type_="check")
        op.drop_column("sources", col)

    op.create_check_constraint(op.f(RULE_NAME), "sources", OLD_RULE)
