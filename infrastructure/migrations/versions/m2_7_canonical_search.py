"""M2.7_canonical_search

Revision ID: m2_7_canonical_search
Revises: m2_4_canonical_publishing
Create Date: 2026-08-26 08:58:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "m2_7_canonical_search"
down_revision = "m2_4_canonical_publishing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add search_vector column
    op.add_column(
        "events", sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True)
    )
    op.create_index(
        "idx_events_search_vector", "events", ["search_vector"], postgresql_using="gin"
    )

    # Trigger to update search_vector automatically based on canonical fields (type, subject_id, target_id, payload)
    # The actual weights A, A, B, C can be defined. We assume subject_id/target_id map to text in frontend but in DB they might be UUIDs.
    # For now we index the text representation of payload, type, etc.
    op.execute("""
    CREATE OR REPLACE FUNCTION events_search_vector_update() RETURNS trigger AS $$
    BEGIN
      NEW.search_vector := 
        setweight(to_tsvector('english', coalesce(NEW.type, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.subject_id::text, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.target_id::text, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(NEW.metadata::text, '')), 'D');
      RETURN NEW;
    END
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER trg_events_search_vector_update
    BEFORE INSERT OR UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION events_search_vector_update();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_events_search_vector_update ON events")
    op.execute("DROP FUNCTION IF EXISTS events_search_vector_update")
    op.drop_index("idx_events_search_vector", table_name="events")
    op.drop_column("events", "search_vector")
