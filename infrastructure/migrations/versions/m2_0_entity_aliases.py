"""M2.0_entity_aliases

Revision ID: m2_0_entity_aliases
Revises: m0_9_power_systems
Create Date: 2026-08-26 08:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "m2_0_entity_aliases"
down_revision = "m0_9_power_systems"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("series_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("alias", sa.String(), nullable=False),
        sa.Column("normalized_alias", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["series_id"],
            ["series.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "series_id",
            "entity_type",
            "normalized_alias",
            name="uq_series_type_normalized_alias",
        ),
    )
    op.create_index(
        "idx_alias_series_normalized",
        "entity_aliases",
        ["series_id", "normalized_alias"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_alias_series_normalized", table_name="entity_aliases")
    op.drop_table("entity_aliases")
