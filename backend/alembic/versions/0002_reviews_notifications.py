"""stage 4: product.root_id + user.notify_new_reviews

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("root_id", sa.String(length=128), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "notify_new_reviews",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "notify_new_reviews")
    op.drop_column("products", "root_id")
