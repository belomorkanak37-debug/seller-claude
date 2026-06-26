"""stage 9: position snapshots + tracked queries

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("tracked_queries", sa.JSON(), nullable=True)
    )
    op.create_table(
        "position_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.String(length=512), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column(
            "captured_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_position_snapshots_product_id", "position_snapshots", ["product_id"]
    )
    op.create_index(
        "ix_position_snapshots_captured_at", "position_snapshots", ["captured_at"]
    )


def downgrade() -> None:
    op.drop_table("position_snapshots")
    op.drop_column("products", "tracked_queries")
