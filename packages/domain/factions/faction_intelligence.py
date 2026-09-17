from packages.domain.factions.faction_relationship_state import FactionRelationshipState
from packages.domain.factions.leadership_state import LeadershipState
from packages.domain.factions.membership_state import MembershipState
from packages.domain.state.world_state import WorldState


class FactionIntelligence:
    @staticmethod
    def get_active_members(state: WorldState, faction_id: str) -> list[str]:
        active_members = []
        for (char_id, f_id), memberships in state.memberships.items():
            if f_id == faction_id:
                for ms in memberships:
                    if ms.active:
                        active_members.append(char_id)
        return active_members

    @staticmethod
    def get_membership_history(
        state: WorldState, faction_id: str
    ) -> list[MembershipState]:
        history = []
        for (char_id, f_id), memberships in state.memberships.items():
            if f_id == faction_id:
                history.extend(memberships)
        # Sort by joined_at desc
        history.sort(key=lambda m: m.joined_at, reverse=True)
        return history

    @staticmethod
    def get_current_leader(state: WorldState, faction_id: str) -> str | None:
        if faction_id in state.leaderships:
            for ls in state.leaderships[faction_id]:
                if ls.active:
                    return ls.leader_id
        return None

    @staticmethod
    def get_leadership_history(
        state: WorldState, faction_id: str
    ) -> list[LeadershipState]:
        if faction_id in state.leaderships:
            history = list(state.leaderships[faction_id])
            history.sort(key=lambda l: l.started_at, reverse=True)
            return history
        return []

    @staticmethod
    def get_faction_relationships(
        state: WorldState, faction_id: str
    ) -> list[FactionRelationshipState]:
        rels = []
        for (subj, targ), relations in state.faction_relationships.items():
            if subj == faction_id or targ == faction_id:
                for rel in relations:
                    if rel.active:
                        rels.append(rel)
        return rels
