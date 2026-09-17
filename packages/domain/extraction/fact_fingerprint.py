import hashlib
import json


class FactFingerprint:
    @staticmethod
    def generate(
        series_id: str,
        chapter_id: str,
        fact_type: str,
        subject_raw_norm: str,
        target_raw_norm: str,
        payload: dict,
    ) -> str:
        """
        Generates a deterministic hash for an extracted fact, relying on canonical/normalized inputs.
        Ignores confidence and location to allow deduplication of identical facts discovered by multiple extractors.
        """
        # Ensure payload is deterministically stringified
        payload_str = json.dumps(payload, sort_keys=True) if payload else ""

        components = [
            str(series_id),
            str(chapter_id),
            str(fact_type),
            str(subject_raw_norm),
            str(target_raw_norm) if target_raw_norm else "",
            payload_str,
        ]

        raw_fingerprint = "|".join(components)
        return hashlib.sha256(raw_fingerprint.encode("utf-8")).hexdigest()
