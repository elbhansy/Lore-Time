import re


class AliasNormalizer:
    @staticmethod
    def normalize(raw_name: str) -> str:
        """
        Normalizes a raw entity name deterministically:
        1. Convert to lowercase
        2. Remove leading/trailing whitespace
        3. Replace multiple spaces with a single space
        4. Remove punctuation that doesn't contribute to canonical naming (e.g., quotes, hyphens)
           (For this implementation, we will replace hyphens with spaces to handle Kim Dok-ja -> kim dok ja)
        """
        if not raw_name:
            return ""

        # Lowercase
        normalized = raw_name.lower()

        # Replace hyphens with spaces to treat "Dok-Ja" same as "Dok Ja"
        normalized = normalized.replace("-", " ")

        # Remove punctuation (keep alphanumeric and spaces)
        normalized = re.sub(r"[^\w\s]", "", normalized)

        # Replace multiple spaces with single space
        normalized = re.sub(r"\s+", " ", normalized)

        # Strip
        return normalized.strip()
