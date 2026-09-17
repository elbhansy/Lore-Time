class RankComparisonService:
    @staticmethod
    def compare(
        char_a_id: str,
        char_a_sys: str,
        char_a_rank_id: str,
        char_a_order: int,
        char_b_id: str,
        char_b_sys: str,
        char_b_rank_id: str,
        char_b_order: int,
    ) -> str:
        if char_a_sys != char_b_sys:
            return "NOT_COMPARABLE"

        if char_a_order > char_b_order:
            return "A_HIGHER"
        elif char_b_order > char_a_order:
            return "B_HIGHER"
        else:
            return "EQUAL"

    @staticmethod
    def detect_breakthrough(from_rank_order: int, to_rank_order: int) -> str:
        if to_rank_order > from_rank_order:
            return "BREAKTHROUGH"
        elif to_rank_order < from_rank_order:
            return "REGRESSION"
        return "NO_CHANGE"
