from pathlib import Path

# Helper function to ensure documents directory exists
def ensure_documents_dir_exists(documents_dir: Path):
    if not documents_dir.exists():
        documents_dir.mkdir(parents=True, exist_ok=True)
