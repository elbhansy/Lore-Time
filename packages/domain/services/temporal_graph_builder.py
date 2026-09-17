from packages.domain.graph.edge_type import EdgeType
from packages.domain.graph.graph_edge import GraphEdge
from packages.domain.graph.graph_entities import GraphEntities
from packages.domain.graph.graph_node import GraphNode
from packages.domain.graph.node_type import NodeType
from packages.domain.graph.temporal_graph import TemporalGraph
from packages.domain.state.world_state import WorldState


class TemporalGraphBuilder:
    @staticmethod
    def build(world_state: WorldState, entities: GraphEntities) -> TemporalGraph:
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        reader_chapter = world_state.chapter.value

        added_node_ids: set[str] = set()

        def add_node(n: GraphNode):
            if n.id not in added_node_ids:
                nodes.append(n)
                added_node_ids.add(n.id)

        def add_edge(e: GraphEdge):
            edges.append(e)

        # 1. Characters
        # A Character node is ONLY added if it exists in WorldState.
        # This completely hides future characters.
        for char_id, char_state in world_state.characters.items():
            if not char_state.exists:
                continue

            char_meta = entities.characters.get(char_id)
            label = char_meta.name if char_meta else char_id

            add_node(GraphNode(id=char_id, type=NodeType.CHARACTER, label=label))

            # Faction Membership
            if char_state.faction_id:
                fac_meta = entities.factions.get(char_state.faction_id)
                # Only add if the faction is introduced by readerChapter
                if (
                    fac_meta
                    and fac_meta.introduced_chapter
                    and fac_meta.introduced_chapter <= reader_chapter
                ):
                    # Also ensure the Faction node exists
                    add_node(
                        GraphNode(
                            id=char_state.faction_id,
                            type=NodeType.FACTION,
                            label=fac_meta.name,
                        )
                    )
                    add_edge(
                        GraphEdge(
                            source_id=char_id,
                            target_id=char_state.faction_id,
                            type=EdgeType.MEMBER_OF,
                        )
                    )

            # Ranks
            if char_state.rank:
                rank_id = char_state.rank
                rank_meta = entities.ranks.get(rank_id)
                # Strict spoiler firewall: Only show rank if introduced_chapter <= readerChapter
                if (
                    rank_meta
                    and rank_meta.introduced_chapter
                    and rank_meta.introduced_chapter <= reader_chapter
                ):
                    add_node(
                        GraphNode(id=rank_id, type=NodeType.RANK, label=rank_meta.name)
                    )
                    add_edge(
                        GraphEdge(
                            source_id=char_id, target_id=rank_id, type=EdgeType.HAS_RANK
                        )
                    )

                    # Tie rank to Power System
                    if rank_meta.system_id:
                        sys_meta = entities.power_systems.get(rank_meta.system_id)
                        if sys_meta:
                            add_node(
                                GraphNode(
                                    id=rank_meta.system_id,
                                    type=NodeType.POWER_SYSTEM,
                                    label=sys_meta.name,
                                )
                            )
                            add_edge(
                                GraphEdge(
                                    source_id=char_id,
                                    target_id=rank_meta.system_id,
                                    type=EdgeType.USES_POWER_SYSTEM,
                                )
                            )
                            add_edge(
                                GraphEdge(
                                    source_id=rank_id,
                                    target_id=rank_meta.system_id,
                                    type=EdgeType.BELONGS_TO,
                                )
                            )

            # Skills
            for skill_id in char_state.unlocked_skills:
                skill_meta = entities.skills.get(skill_id)
                label = skill_meta.name if skill_meta else skill_id
                # In WorldState, if a character has a skill, it means the character unlocked it <= readerChapter.
                add_node(GraphNode(id=skill_id, type=NodeType.SKILL, label=label))
                add_edge(
                    GraphEdge(
                        source_id=char_id,
                        target_id=skill_id,
                        type=EdgeType.UNLOCKED_SKILL,
                    )
                )

        # 2. Relationships
        # Reuses relationships proven at readerChapter
        for (source, target), rel_state in world_state.relationships.items():
            if not rel_state.active:
                continue

            # Both ends must be visible in graph (meaning they exist in WorldState)
            if source in added_node_ids and target in added_node_ids:
                try:
                    edge_type = EdgeType(rel_state.relationship_type.value)
                except ValueError:
                    # Fallback if somehow enum drifted
                    continue
                add_edge(GraphEdge(source_id=source, target_id=target, type=edge_type))

        # 3. Determinism
        nodes.sort(key=lambda n: (n.type.value, n.id))
        edges.sort(key=lambda e: (e.source_id, e.target_id, e.type.value))

        return TemporalGraph(reader_chapter=reader_chapter, nodes=nodes, edges=edges)
