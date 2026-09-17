"""M2.8_graph_projection

Revision ID: m2_8_graph_projection
Revises: m2_7_canonical_search
Create Date: 2026-08-26 09:03:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "m2_8_graph_projection"
down_revision = "m2_7_canonical_search"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create canonical_entities table
    op.create_table(
        "canonical_entities",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("series_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("series_id", "id", name="uq_canonical_entity_series_id"),
    )

    # Create canonical_relationships table
    op.create_table(
        "canonical_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("series_id", sa.String(), nullable=False),
        sa.Column("source_entity_id", sa.String(), nullable=False),
        sa.Column("target_entity_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_rel_series_source",
        "canonical_relationships",
        ["series_id", "source_entity_id"],
        unique=False,
    )
    op.create_index(
        "idx_rel_series_target",
        "canonical_relationships",
        ["series_id", "target_entity_id"],
        unique=False,
    )
    op.create_index(
        "idx_rel_series_type",
        "canonical_relationships",
        ["series_id", "type"],
        unique=False,
    )
    op.create_index(
        "idx_rel_event", "canonical_relationships", ["event_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_rel_event", table_name="canonical_relationships")
    op.drop_index("idx_rel_series_type", table_name="canonical_relationships")
    op.drop_index("idx_rel_series_target", table_name="canonical_relationships")
    op.drop_index("idx_rel_series_source", table_name="canonical_relationships")
    op.drop_table("canonical_relationships")
    op.drop_table("canonical_entities")
