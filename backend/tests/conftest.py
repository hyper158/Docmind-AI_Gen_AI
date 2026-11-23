import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "docmind_mpl_cache"))

try:
    import matplotlib
    matplotlib.use("Agg")
except Exception:
    pass

try:
    import faiss
except Exception:
    pass
