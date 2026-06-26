"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("photo_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "notifications_enabled",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "registered_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("marketplace", sa.String(length=32), nullable=False),
        sa.Column("article", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=1024), nullable=False),
        sa.Column("photo_url", sa.String(length=2048), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("reviews_count", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=True),
        sa.Column("cost_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_user_id", "products", ["user_id"])
    op.create_index("ix_products_article", "products", ["article"])

    op.create_table(
        "competitors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("marketplace", sa.String(length=32), nullable=False),
        sa.Column("article", sa.String(length=128), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("name", sa.String(length=1024), nullable=False),
        sa.Column("photo_url", sa.String(length=2048), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("reviews_count", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_competitors_product_id", "competitors", ["product_id"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("competitor_id", sa.Integer(), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("sentiment", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["competitor_id"], ["competitors.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reviews_product_id", "reviews", ["product_id"])
    op.create_index("ix_reviews_competitor_id", "reviews", ["competitor_id"])
    op.create_index("ix_reviews_external_id", "reviews", ["external_id"])

    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("competitor_id", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["competitor_id"], ["competitors.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_price_snapshots_product_id", "price_snapshots", ["product_id"]
    )
    op.create_index(
        "ix_price_snapshots_competitor_id", "price_snapshots", ["competitor_id"]
    )
    op.create_index(
        "ix_price_snapshots_captured_at", "price_snapshots", ["captured_at"]
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "sent_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "unit_economics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("commission_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("logistics_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("storage_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("acquiring_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("returns_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("tax_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("net_profit", sa.Numeric(12, 2), nullable=True),
        sa.Column("margin_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_unit_economics_product_id", "unit_economics", ["product_id"])


def downgrade() -> None:
    op.drop_table("unit_economics")
    op.drop_table("notifications")
    op.drop_table("price_snapshots")
    op.drop_table("reviews")
    op.drop_table("competitors")
    op.drop_table("products")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
