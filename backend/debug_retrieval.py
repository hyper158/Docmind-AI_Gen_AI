"""
Debug script – run from the backend/ directory:
  cd backend
  .\venv\Scripts\Activate.ps1
  python debug_retrieval.py
"""
import sys
import os

# Make sure Python can find the app package
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.database.initialization import init_db
from app.database.repository import Repository
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.services.retrieval_service import RetrievalService

print("=" * 60)
print("DocMind AI – Retrieval Diagnostic")
print("=" * 60)

# 1. Init DB
print("\n[1] Initialising database …")
init_db()
print("    OK")

# 2. List documents
print("\n[2] Documents in database:")
docs = Repository.list_documents()
if not docs:
    print("    !! NO DOCUMENTS FOUND – upload a PDF first")
    sys.exit(1)

for d in docs:
    print(f"    id={d.document_id}  status={d.processing_status}  chunks={d.chunk_count}  file={d.filename}")

# 3. Check FAISS indexes on disk
print("\n[3] FAISS index directories:")
indexes_dir = settings.INDEXES_DIR
for d in docs:
    idx_path = indexes_dir / d.document_id
    faiss_file = idx_path / "index.faiss"
    pkl_file   = idx_path / "index.pkl"
    exists = faiss_file.exists() and pkl_file.exists()
    print(f"    {d.document_id}: {'EXISTS' if exists else '!! MISSING'} ({idx_path})")

# 4. Load combined index
ready_ids = [d.document_id for d in docs if d.processing_status == "ready"]
print(f"\n[4] Ready document IDs: {ready_ids}")
if not ready_ids:
    print("    !! No ready documents – the backend may have failed during processing")
    sys.exit(1)

print("\n[5] Loading embeddings model (may take a minute on first run) …")
vs_svc = VectorStoreService()
print("    EmbeddingService initialised")

combined = vs_svc.load_combined_index(ready_ids)
if combined is None:
    print("    !! load_combined_index returned None – FAISS indexes are missing or corrupted")
    sys.exit(1)
print(f"    Combined FAISS store loaded OK (ntotal={combined.index.ntotal} vectors)")

# 5. Raw retrieval with threshold=0
TEST_QUERY = "what is this document about"
print(f"\n[6] Similarity search – query: '{TEST_QUERY}'")
docs_and_scores = combined.similarity_search_with_score(TEST_QUERY, k=10)
print(f"    Returned {len(docs_and_scores)} raw results:")
for doc, raw_score in docs_and_scores:
    sim = max(0.0, min(1.0, 1.0 - (raw_score / 2.0)))
    page = doc.metadata.get("page", "?")
    snippet = doc.page_content[:80].replace("\n", " ")
    print(f"      raw={raw_score:.4f}  sim={sim:.4f}  page={page}  text='{snippet}…'")

# 6. Threshold analysis
THRESHOLD = settings.RELEVANCE_SCORE_THRESHOLD
sims = [max(0.0, min(1.0, 1.0 - (s / 2.0))) for _, s in docs_and_scores]
passing = [s for s in sims if s >= THRESHOLD]
print(f"\n[7] Threshold analysis (RELEVANCE_SCORE_THRESHOLD={THRESHOLD}):")
print(f"    Chunks passing threshold: {len(passing)} / {len(sims)}")
if not passing:
    print(f"    !! ALL chunks rejected – lower RELEVANCE_SCORE_THRESHOLD in backend/.env")
    best = max(sims) if sims else 0
    print(f"    Best similarity score seen: {best:.4f}")
    print(f"    Suggested new threshold:    {max(0.0, best - 0.05):.2f}")

print("\n[8] RetrievalService end-to-end (threshold=0.0):")
ret = RetrievalService(threshold=0.0)
chunks = ret.retrieve_chunks(TEST_QUERY, ready_ids)
print(f"    Retrieved {len(chunks)} chunks (threshold=0.0, no filtering)")
if chunks:
    print(f"    Best:  sim={chunks[0].similarity_score}  raw={chunks[0].raw_distance:.4f}")
    print(f"    Worst: sim={chunks[-1].similarity_score}  raw={chunks[-1].raw_distance:.4f}")

print("\n" + "=" * 60)
print("Diagnostic complete.")
print("=" * 60)
