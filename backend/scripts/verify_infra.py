"""
Verification script for DocuMind AI Infrastructure:
Tests Neon PostgreSQL and Qdrant Cloud connectivity.
"""
import sys
import os
import time

# Ensure backend root is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
from app.config import settings

NEON_URL = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
QDRANT_URL = os.environ.get("QDRANT_URL") or settings.QDRANT_URL
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY") or settings.QDRANT_API_KEY
COLLECTION_NAME = settings.QDRANT_COLLECTION


def test_neon():
    print("\n--- 1. Testing Neon PostgreSQL Connection ---")
    start = time.time()
    try:
        # Strip channel_binding if present as psycopg2 might not require it
        url = NEON_URL
        if "channel_binding" in url:
            # Clean URL for standard psycopg2
            parts = url.split("?")
            base = parts[0]
            params = [p for p in parts[1].split("&") if not p.startswith("channel_binding=")]
            url = base + ("?" + "&".join(params) if params else "")

        engine = create_engine(url, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).fetchone()
            latency = (time.time() - start) * 1000
            print(f"[SUCCESS] Connected to Neon PostgreSQL in {latency:.1f}ms!")
            print(f"Database version: {result[0][:80]}...")
            
            # Check existing tables
            tables_res = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' ORDER BY table_name;
            """)).fetchall()
            tables = [r[0] for r in tables_res]
            print(f"Tables present in database: {tables if tables else 'None (Clean DB)'}")
            return True, tables
    except Exception as e:
        print(f"[FAILED] Neon connection failed with error: {type(e).__name__}")
        return False, []


def test_qdrant():
    print("\n--- 2. Testing Qdrant Cloud Connection ---")
    start = time.time()
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=10)
        collections_resp = client.get_collections()
        latency = (time.time() - start) * 1000
        collection_names = [c.name for c in collections_resp.collections]
        print(f"[SUCCESS] Connected to Qdrant Cloud in {latency:.1f}ms!")
        print(f"Collections found: {collection_names}")
        
        if COLLECTION_NAME in collection_names:
            info = client.get_collection(collection_name=COLLECTION_NAME)
            size = info.config.params.vectors.size
            distance = info.config.params.vectors.distance
            print(f"Collection '{COLLECTION_NAME}' details: vector_size={size}, distance={distance}")
        else:
            print(f"Collection '{COLLECTION_NAME}' does not exist yet (will be auto-created on first upload).")
            
        return True
    except Exception as e:
        print(f"[FAILED] Qdrant Cloud connection failed with error: {type(e).__name__}")
        return False


if __name__ == "__main__":
    neon_ok, tables = test_neon()
    qdrant_ok = test_qdrant()
    
    print("\n" + "=" * 50)
    print("        INFRASTRUCTURE CONNECTIVITY SUMMARY")
    print("=" * 50)
    print(f"Neon PostgreSQL : {'PASS' if neon_ok else 'FAIL'}")
    print(f"Qdrant Cloud    : {'PASS' if qdrant_ok else 'FAIL'}")
    print("=" * 50)

    if neon_ok and qdrant_ok:
        print("\nAll production cloud infrastructure checks passed!")
        sys.exit(0)
    else:
        print("\nOne or more infrastructure checks failed.")
        sys.exit(1)

