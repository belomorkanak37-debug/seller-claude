"""stage 8: repricer rule on products

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "repricer_enabled", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.add_column(
        "products", sa.Column("undercut_pct", sa.Numeric(6, 3), nullable=True)
    )
    op.add_column(
        "products", sa.Column("min_price", sa.Numeric(12, 2), nullable=True)
    )
    op.add_column(
        "products", sa.Column("max_price", sa.Numeric(12, 2), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("products", "max_price")
    op.drop_column("products", "min_price")
    op.drop_column("products", "undercut_pct")
    op.drop_column("products", "repricer_enabled")
