"""Back up project source and bundled examples; never secrets or user datasets."""
from pathlib import Path
from datetime import datetime, timezone
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent
folder = root / "backups"
folder.mkdir(exist_ok=True)
target = folder / ("ai_data_assistant_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".zip")
allowed_files = {"app.py", "requirements.txt", "README_TR.md", "BASLA_BURADAN.txt", "VALIDATION.md", "smoke_test.py", "backup.py", ".env.example", ".gitignore"}
allowed_dirs = {"data_assistant", "sample_data", "tests", ".streamlit"}
with ZipFile(target, "x", ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_file() and "__pycache__" not in relative.parts and ".env" not in relative.parts:
            if (len(relative.parts) == 1 and path.name in allowed_files) or relative.parts[0] in allowed_dirs:
                if path.suffix not in (".pyc", ".pyo"):
                    archive.write(path, Path(root.name) / relative)
print("Kaynak kod yedeği:", target)
print(".env, kullanıcı verileri ve runs dahil edilmedi. Yedeği başka disk veya buluta da kopyala.")
