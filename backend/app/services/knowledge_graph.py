"""
Knowledge Graph Service for DocuMind AI
Extracts entities and relationships from text using structured LLM JSON generation,
constructs a directed graph with NetworkX, and enables multi-hop relational reasoning.
"""

import json
import logging
import re
from typing import Any
import networkx as nx
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class Entity(BaseModel):
    id: str
    label: str
    category: str = "Concept"  # e.g., "Service", "Database", "Person", "Policy", "Technology"
    description: str | None = None


class Relationship(BaseModel):
    source: str
    target: str
    relation: str  # e.g., "uses", "depends_on", "manages", "persists_to", "authorizes"
    confidence: float = 1.0


class KnowledgeGraphData(BaseModel):
    entities: list[Entity] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Extraction Prompt
# ---------------------------------------------------------------------------

KG_EXTRACTION_SYSTEM_PROMPT = """You are a knowledge graph extraction engine for DocuMind AI.
Analyze the provided document text and extract the key named entities and directed relationships.

Output STRICT JSON ONLY matching this exact schema:
{
  "entities": [
    {"id": "unique_snake_case_id", "label": "Human Readable Name", "category": "CategoryName", "description": "Short summary"}
  ],
  "relationships": [
    {"source": "source_entity_id", "target": "target_entity_id", "relation": "verb_or_predicate", "confidence": 0.95}
  ]
}

Rules:
1. Entity IDs must be normalized lowercase snake_case (e.g. "documind_ai", "postgresql", "jwt_auth").
2. Only include relationships explicitly stated or strongly implied by the text.
3. Output valid JSON with no markdown quotes, backticks, or explanatory text.
"""


# ---------------------------------------------------------------------------
# LLM & Heuristic Extraction
# ---------------------------------------------------------------------------

def _heuristic_fallback_extraction(text: str) -> KnowledgeGraphData:
    """Deterministic entity/relation extractor used when LLM API keys are unavailable."""
    entities: dict[str, Entity] = {}
    relationships: list[Relationship] = []

    # Common technology and architecture patterns
    patterns = [
        (r"(?i)\b(FastAPI|PostgreSQL|Qdrant|Docker|Redis|Ollama|Groq|Gemini|React|TanStack|NetworkX)\b", "Technology"),
        (r"(?i)\b(DocuMind AI|DocuMind)\b", "System"),
        (r"(?i)\b(JWT|HMAC-SHA256|AES-256-GCM|BGSAVE)\b", "Security/Protocol"),
        (r"(?i)\b(Incident Commander|Chief Legal Officer|SRE Lead|Platform Team)\b", "Role/Team"),
        (r"(?i)\b(PTO Allowance|Wellness Stipend|Parental Leave|Retention Policy)\b", "Policy"),
    ]

    found_ids = []
    for pattern, cat in patterns:
        for match in re.finditer(pattern, text):
            raw = match.group(1)
            eid = re.sub(r"[^a-z0-9_]+", "_", raw.lower().strip())
            if eid not in entities:
                entities[eid] = Entity(id=eid, label=raw, category=cat)
                found_ids.append(eid)

    # Heuristic relationships between co-occurring entities
    for i in range(len(found_ids) - 1):
        src = found_ids[i]
        tgt = found_ids[i + 1]
        if src != tgt:
            relationships.append(Relationship(
                source=src,
                target=tgt,
                relation="connected_to",
                confidence=0.85
            ))

    return KnowledgeGraphData(entities=list(entities.values()), relationships=relationships)


def extract_entities_and_relations(text: str) -> KnowledgeGraphData:
    """Extracts entities and relationships from text via Groq/Gemini or heuristic fallback."""
    if not text or not text.strip():
        return KnowledgeGraphData()

    user_prompt = f"Extract entities and directed relationships from this text:\n\n{text[:3000]}"

    raw_response = None

    # Try Groq if configured
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            res = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": KG_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"} if "llama-3" in settings.GROQ_MODEL else None
            )
            raw_response = res.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq KG extraction failed: {e}")

    # Try Gemini if configured
    if not raw_response and settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            res = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=KG_EXTRACTION_SYSTEM_PROMPT,
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )
            raw_response = res.text
        except Exception as e:
            logger.warning(f"Gemini KG extraction failed: {e}")

    # Parse LLM JSON output if available
    if raw_response:
        try:
            cleaned = re.sub(r"^```json\s*", "", raw_response.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
            data = json.loads(cleaned)
            return KnowledgeGraphData(**data)
        except Exception as e:
            logger.warning(f"Failed to parse LLM KG JSON response ({e}), using heuristic fallback.")

    return _heuristic_fallback_extraction(text)


# ---------------------------------------------------------------------------
# NetworkX Knowledge Graph Engine
# ---------------------------------------------------------------------------

class DocumentKnowledgeGraph:
    """Manages an in-memory NetworkX directed graph for entity traversal and multi-hop queries."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def build_from_kg_data(self, kg_data: KnowledgeGraphData) -> None:
        """Populates the NetworkX graph with entities (nodes) and relations (edges)."""
        for entity in kg_data.entities:
            self.graph.add_node(
                entity.id,
                label=entity.label,
                category=entity.category,
                description=entity.description or ""
            )

        for rel in kg_data.relationships:
            # Ensure endpoints exist
            if not self.graph.has_node(rel.source):
                self.graph.add_node(rel.source, label=rel.source, category="Unknown")
            if not self.graph.has_node(rel.target):
                self.graph.add_node(rel.target, label=rel.target, category="Unknown")

            self.graph.add_edge(
                rel.source,
                rel.target,
                relation=rel.relation,
                confidence=rel.confidence
            )

    def find_multi_hop_path(self, source_id: str, target_id: str, cutoff: int = 4) -> list[dict[str, Any]]:
        """Finds shortest and all simple paths between two entities across multiple hops."""
        source = source_id.lower().strip()
        target = target_id.lower().strip()

        if not self.graph.has_node(source) or not self.graph.has_node(target):
            return []

        try:
            all_paths = list(nx.all_simple_paths(self.graph, source=source, target=target, cutoff=cutoff))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

        formatted_paths = []
        for path in all_paths[:5]:  # Return up to 5 paths
            hops = []
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edge_data = self.graph.get_edge_data(u, v, default={})
                u_label = self.graph.nodes[u].get("label", u)
                v_label = self.graph.nodes[v].get("label", v)
                hops.append({
                    "from": u_label,
                    "relation": edge_data.get("relation", "relates_to"),
                    "to": v_label,
                    "confidence": edge_data.get("confidence", 1.0)
                })

            formatted_paths.append({
                "path_length": len(path) - 1,
                "node_sequence": [self.graph.nodes[n].get("label", n) for n in path],
                "hops": hops,
                "summary": " -> ".join(
                    [f"[{self.graph.nodes[path[i]].get('label', path[i])}] --({self.graph.get_edge_data(path[i], path[i+1]).get('relation', 'relates_to')})--> [{self.graph.nodes[path[i+1]].get('label', path[i+1])}]"
                     for i in range(len(path) - 1)]
                )
            })

        return formatted_paths

    def get_entity_neighborhood(self, entity_id: str, radius: int = 1) -> dict[str, Any]:
        """Returns 1-hop or 2-hop connected subgraph around an entity."""
        eid = entity_id.lower().strip()
        if not self.graph.has_node(eid):
            return {"entity": entity_id, "found": False, "neighbors": []}

        subgraph_nodes = nx.single_source_shortest_path_length(self.graph, eid, cutoff=radius).keys()
        subgraph = self.graph.subgraph(subgraph_nodes)

        nodes_data = [
            {"id": n, "label": subgraph.nodes[n].get("label", n), "category": subgraph.nodes[n].get("category", "")}
            for n in subgraph.nodes
        ]
        edges_data = [
            {"source": u, "target": v, "relation": d.get("relation", ""), "confidence": d.get("confidence", 1.0)}
            for u, v, d in subgraph.edges(data=True)
        ]

        return {
            "entity": self.graph.nodes[eid].get("label", eid),
            "found": True,
            "nodes_count": len(nodes_data),
            "edges_count": len(edges_data),
            "nodes": nodes_data,
            "edges": edges_data
        }

    def generate_graph_context_for_rag(self, query: str) -> str:
        """Finds entities mentioned in query and formats relational triples to augment RAG prompt."""
        query_lower = query.lower()
        matched_nodes = [
            n for n in self.graph.nodes
            if self.graph.nodes[n].get("label", "").lower() in query_lower or n in query_lower
        ]

        if not matched_nodes:
            return ""

        triples = []
        for n in matched_nodes[:3]:
            # Outgoing relations
            for successor in self.graph.successors(n):
                edge_data = self.graph.get_edge_data(n, successor, default={})
                n_lbl = self.graph.nodes[n].get("label", n)
                s_lbl = self.graph.nodes[successor].get("label", successor)
                rel = edge_data.get("relation", "relates to")
                triples.append(f"- ({n_lbl}) --[{rel}]--> ({s_lbl})")

            # Incoming relations
            for predecessor in self.graph.predecessors(n):
                edge_data = self.graph.get_edge_data(predecessor, n, default={})
                p_lbl = self.graph.nodes[predecessor].get("label", predecessor)
                n_lbl = self.graph.nodes[n].get("label", n)
                rel = edge_data.get("relation", "relates to")
                triples.append(f"- ({p_lbl}) --[{rel}]--> ({n_lbl})")

        if not triples:
            return ""

        return "Knowledge Graph Relational Context:\n" + "\n".join(triples[:8])

