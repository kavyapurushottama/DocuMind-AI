"""
Tests for Knowledge Graph construction, LLM triple parsing, and multi-hop graph traversal.
"""

import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import pytest
from app.services.knowledge_graph import (
    DocumentKnowledgeGraph,
    KnowledgeGraphData,
    Entity,
    Relationship,
    extract_entities_and_relations,
    _heuristic_fallback_extraction
)


@pytest.fixture
def sample_graph():
    kg = DocumentKnowledgeGraph()
    data = KnowledgeGraphData(
        entities=[
            Entity(id="documind_ai", label="DocuMind AI", category="Product"),
            Entity(id="fastapi", label="FastAPI", category="Framework"),
            Entity(id="qdrant", label="Qdrant", category="Database"),
            Entity(id="postgresql", label="PostgreSQL", category="Database"),
            Entity(id="vector_embeddings", label="Vector Embeddings", category="Artifact"),
        ],
        relationships=[
            Relationship(source="documind_ai", target="fastapi", relation="built_with"),
            Relationship(source="fastapi", target="qdrant", relation="queries"),
            Relationship(source="fastapi", target="postgresql", relation="stores_users_in"),
            Relationship(source="qdrant", target="vector_embeddings", relation="indexes"),
        ]
    )
    kg.build_from_kg_data(data)
    return kg


def test_graph_node_and_edge_creation(sample_graph):
    assert sample_graph.graph.number_of_nodes() == 5
    assert sample_graph.graph.number_of_edges() == 4
    assert sample_graph.graph.has_node("documind_ai")
    assert sample_graph.graph.has_node("qdrant")


def test_single_hop_query(sample_graph):
    paths = sample_graph.find_multi_hop_path("documind_ai", "fastapi")
    assert len(paths) == 1
    assert paths[0]["path_length"] == 1
    assert paths[0]["hops"][0]["relation"] == "built_with"


def test_multi_hop_query_traversal(sample_graph):
    # documind_ai -> fastapi -> qdrant -> vector_embeddings (3 hops)
    paths = sample_graph.find_multi_hop_path("documind_ai", "vector_embeddings", cutoff=4)
    assert len(paths) == 1
    p = paths[0]
    assert p["path_length"] == 3
    assert p["node_sequence"] == ["DocuMind AI", "FastAPI", "Qdrant", "Vector Embeddings"]


def test_disconnected_node_path(sample_graph):
    # No path from vector_embeddings back to documind_ai (directed graph)
    paths = sample_graph.find_multi_hop_path("vector_embeddings", "documind_ai")
    assert len(paths) == 0


def test_entity_neighborhood(sample_graph):
    neighborhood = sample_graph.get_entity_neighborhood("fastapi", radius=1)
    assert neighborhood["found"] is True
    # fastapi has outgoing edges to qdrant and postgresql
    targets = [e["target"] for e in neighborhood["edges"]]
    assert "qdrant" in targets
    assert "postgresql" in targets


def test_heuristic_extraction_fallback():
    raw_text = "DocuMind AI utilizes FastAPI and Qdrant to power high-speed semantic search."
    kg_data = _heuristic_fallback_extraction(raw_text)
    assert isinstance(kg_data, KnowledgeGraphData)
    extracted_ids = [e.id for e in kg_data.entities]
    assert any("fastapi" in eid for eid in extracted_ids)
    assert any("qdrant" in eid for eid in extracted_ids)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
