# Preload faiss first on Windows to ensure swigfaiss initializes cleanly before other C-extensions
import faiss
