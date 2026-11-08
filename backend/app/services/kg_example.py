"""
DocuMind AI - Knowledge Graph Multi-Hop Query Example
Demonstrates extracting entities & relations from system documentation,
building a NetworkX directed graph, and resolving multi-hop dependency queries.
"""

from app.services.knowledge_graph import (
    DocumentKnowledgeGraph,
    KnowledgeGraphData,
    Entity,
    Relationship
)


def run_multi_hop_demo():
    print("=" * 65)
    print("      DOCUMIND AI - KNOWLEDGE GRAPH MULTI-HOP QUERY DEMO")
    print("=" * 65)

    # Sample architectural & domain relationships
    kg_data = KnowledgeGraphData(
        entities=[
            Entity(id="documind_backend", label="DocuMind Backend", category="System"),
            Entity(id="fastapi", label="FastAPI App", category="Framework"),
            Entity(id="qdrant", label="Qdrant Vector DB", category="Database"),
            Entity(id="postgresql", label="PostgreSQL DB", category="Database"),
            Entity(id="dense_vectors", label="384-d Dense Embeddings", category="Artifact"),
            Entity(id="fastembed", label="FastEmbed Local Model", category="Model"),
            Entity(id="jwt_security", label="JWT Auth Guard", category="Security"),
            Entity(id="user_tenant", label="Tenant Session", category="Domain")
        ],
        relationships=[
            Relationship(source="documind_backend", target="fastapi", relation="implements"),
            Relationship(source="fastapi", target="jwt_security", relation="enforces"),
            Relationship(source="jwt_security", target="user_tenant", relation="authenticates"),
            Relationship(source="documind_backend", target="fastembed", relation="invokes"),
            Relationship(source="fastembed", target="dense_vectors", relation="generates"),
            Relationship(source="dense_vectors", target="qdrant", relation="indexed_in"),
            Relationship(source="user_tenant", target="postgresql", relation="persisted_in"),
            Relationship(source="qdrant", target="postgresql", relation="coordinates_tenant_metadata_with"),
        ]
    )

    # 1. Initialize NetworkX Graph
    kg = DocumentKnowledgeGraph()
    kg.build_from_kg_data(kg_data)

    print(f"Graph initialized with {kg.graph.number_of_nodes()} entities and {kg.graph.number_of_edges()} directed relations.\n")

    # 2. Execute Multi-Hop Query:
    # Query: "How does the DocuMind Backend connect to Qdrant Vector DB?"
    source = "documind_backend"
    target = "qdrant"
    print(f"Executing Multi-Hop Path Search: '{source}' -> '{target}'...")
    paths = kg.find_multi_hop_path(source, target, cutoff=4)

    print(f"\nFound {len(paths)} path(s) between '{source}' and '{target}':")
    for i, p in enumerate(paths, start=1):
        print(f"\nPath #{i} ({p['path_length']} hops):")
        print(f"  {p['summary']}")
        for hop in p["hops"]:
            print(f"    - [{hop['from']}] --({hop['relation']})--> [{hop['to']}]")

    # 3. Test Entity Neighborhood Query:
    print("\n" + "-" * 65)
    print("Entity Neighborhood 1-Hop Expansion for 'jwt_security':")
    neighborhood = kg.get_entity_neighborhood("jwt_security", radius=1)
    for edge in neighborhood["edges"]:
        print(f"  - {edge['source']} --[{edge['relation']}]--> {edge['target']}")

    # 4. Generate RAG context augmentation:
    print("\n" + "-" * 65)
    rag_context = kg.generate_graph_context_for_rag("Tell me how FastEmbed relates to Qdrant")
    print("Graph Augmented RAG Context:\n" + rag_context)
    print("=" * 65)


if __name__ == "__main__":
    run_multi_hop_demo()

