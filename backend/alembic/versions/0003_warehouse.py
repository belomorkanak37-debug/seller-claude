"""stage 7: warehouse params, competitor stock, notify_stock

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("daily_sales", sa.Numeric(10, 2), nullable=True)
    )
    op.add_column(
        "products",
        sa.Column(
            "lead_time_days", sa.Integer(), server_default="14", nullable=False
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "target_cover_days", sa.Integer(), server_default="30", nullable=False
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "low_stock_threshold_days",
            sa.Integer(),
            server_default="7",
            nullable=False,
        ),
    )
    op.add_column("competitors", sa.Column("stock", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "notify_stock", sa.Boolean(), server_default="true", nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "notify_stock")
    op.drop_column("competitors", "stock")
    op.drop_column("products", "low_stock_threshold_days")
    op.drop_column("products", "target_cover_days")
    op.drop_column("products", "lead_time_days")
    op.drop_column("products", "daily_sales")
