import os
import shutil
import re
from pathlib import Path

BASE_DIR = Path(r"c:\Users\marou\Desktop\universal-data-analyser\universal-data-analyser")

moves = {
    "models": "app/Models",
    "controllers": "app/Http/Controllers",
    "schemas": "app/Http/Requests",
    "services": "app/Services",
    "repositories": "app/Repositories",
    "api/routes": "routes/api",
    "api/dependencies.py": "app/Http/Middleware/dependencies.py",
    "api/main.py": "bootstrap/app.py",
    "views": "resources/views"
}

# Create __init__.py for all new dirs
def ensure_init(path):
    p = BASE_DIR / path
    p.mkdir(parents=True, exist_ok=True)
    init_file = p / "__init__.py"
    if p.is_dir() and not init_file.exists():
        init_file.write_text('"""Init file."""\n', encoding="utf-8")

# Create directories
for new_path in moves.values():
    if not new_path.endswith('.py'):
        ensure_init(new_path)
    else:
        ensure_init(str(Path(new_path).parent))

ensure_init("app")
ensure_init("app/Http")
ensure_init("routes")
ensure_init("resources")

# Perform moves
for old, new in moves.items():
    old_p = BASE_DIR / old
    new_p = BASE_DIR / new
    if old_p.exists():
        if old_p.is_dir():
            for item in old_p.iterdir():
                dst = Path(new_p) / item.name
                if dst.exists():
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()
                shutil.move(str(item), str(new_p))
            shutil.rmtree(old_p)
        else:
            dst = new_p
            if Path(dst).exists():
                Path(dst).unlink()
            shutil.move(str(old_p), str(new_p))

# Update imports
replacements = {
    r"\bfrom models\b": "from app.Models",
    r"\bimport models\b": "import app.Models",
    r"\bfrom controllers\b": "from app.Http.Controllers",
    r"\bimport controllers\b": "import app.Http.Controllers",
    r"\bfrom schemas\b": "from app.Http.Requests",
    r"\bimport schemas\b": "import app.Http.Requests",
    r"\bfrom services\b": "from app.Services",
    r"\bimport services\b": "import app.Services",
    r"\bfrom repositories\b": "from app.Repositories",
    r"\bimport repositories\b": "import app.Repositories",
    r"\bfrom api\.routes\b": "from routes.api",
    r"\bimport api\.routes\b": "import routes.api",
    r"\bfrom api\.dependencies\b": "from app.Http.Middleware.dependencies",
    r"\bimport api\.dependencies\b": "import app.Http.Middleware.dependencies",
    r"\bfrom views\b": "from resources.views",
    r"\bimport views\b": "import resources.views",
}

for root, dirs, files in os.walk(BASE_DIR):
    if "venv" in root or ".git" in root or "__pycache__" in root or "node_modules" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = Path(root) / file
            try:
                content = filepath.read_text(encoding="utf-8")
                new_content = content
                for old_pat, new_str in replacements.items():
                    new_content = re.sub(old_pat, new_str, new_content)
                if new_content != content:
                    filepath.write_text(new_content, encoding="utf-8")
                    print(f"Updated imports in {filepath}")
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

# Clean up empty api dir if it's there
api_dir = BASE_DIR / "api"
if api_dir.exists() and api_dir.is_dir() and not list(api_dir.iterdir()):
    api_dir.rmdir()

print("Refactoring complete.")
