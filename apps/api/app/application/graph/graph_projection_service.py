class GraphProjectionService:
    def __init__(self, repo):
        self.repo = repo

    def project_event(self, event_data: dict, event_id: str):
        """
        Projects a canonical event into the Graph DB synchronously within the same transaction.
        Raises an error if projection fails, which rolls back the entire event insertion.
        """
        series_id = event_data["series_id"]

        # 1. Ensure Subject Entity
        subject_id = event_data["subject_id"]
        # Basic parsing to extract a fallback name and type from metadata or assume generic
        subject_type = (
            event_data.get("metadata", {})
            .get("payload", {})
            .get("subject_type", "UNKNOWN")
        )
        subject_name = (
            event_data.get("metadata", {})
            .get("payload", {})
            .get("subject_name", subject_id)
        )

        self.repo.ensure_entity_exists(
            entity_id=subject_id,
            series_id=series_id,
            type=subject_type,
            name=subject_name,
        )

        # 2. Ensure Target Entity (if applicable)
        target_id = event_data.get("target_id")
        if target_id:
            target_type = (
                event_data.get("metadata", {})
                .get("payload", {})
                .get("target_type", "UNKNOWN")
            )
            target_name = (
                event_data.get("metadata", {})
                .get("payload", {})
                .get("target_name", target_id)
            )
            self.repo.ensure_entity_exists(
                entity_id=target_id,
                series_id=series_id,
                type=target_type,
                name=target_name,
            )

            # 3. Create Relationship
            # For simplicity in this M2.8 logic, the relationship type is the event type
            rel_type = event_data["type"]
            self.repo.create_relationship(
                series_id=series_id,
                source_id=subject_id,
                target_id=target_id,
                rel_type=rel_type,
                event_id=event_id,
                sequence=event_data.get("sequence", 0),
            )
