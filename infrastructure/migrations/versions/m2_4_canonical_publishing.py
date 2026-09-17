"""M2.4_canonical_publishing

Revision ID: m2_4_canonical_publishing
Revises: m2_3_review_layer
Create Date: 2026-08-26 08:41:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "m2_4_canonical_publishing"
down_revision = "m2_3_review_layer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add publication_fingerprint to events
    op.add_column(
        "events", sa.Column("publication_fingerprint", sa.String(), nullable=True)
    )
    op.create_unique_constraint(
        "uq_event_publication_fingerprint", "events", ["publication_fingerprint"]
    )

    # Create publication_attempts table
    op.create_table(
        "publication_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("actor_id", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
        ),
        sa.ForeignKeyConstraint(
            ["review_item_id"],
            ["review_items.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("publication_attempts")
    op.drop_constraint("uq_event_publication_fingerprint", "events", type_="unique")
    op.drop_column("events", "publication_fingerprint")
