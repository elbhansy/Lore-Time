import hashlib
import json


class PublicationFingerprint:
    @staticmethod
    def generate(
        series_id: str,
        chapter_id: str,
        event_type: str,
        subject_id: str,
        target_id: str | None,
        payload: dict,
    ) -> str:
        """
        Generates a deterministic SHA-256 fingerprint for a canonical event to prevent duplicates.
        This forms the basis of the UNIQUE(publication_fingerprint) constraint in the database.
        """
        payload_str = json.dumps(payload, sort_keys=True) if payload else ""
        target_str = str(target_id) if target_id else ""

        components = [
            str(series_id),
            str(chapter_id),
            str(event_type),
            str(subject_id),
            target_str,
            payload_str,
        ]

        raw_fingerprint = "|".join(components)
        return hashlib.sha256(raw_fingerprint.encode("utf-8")).hexdigest()
