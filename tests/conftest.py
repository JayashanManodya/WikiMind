import sys
import types
from pathlib import Path

# Add project root and backend to sys.path so modules like backend can be imported cleanly
root_dir = Path(__file__).parent.parent
backend_dir = root_dir / "backend"

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Create BackEnd module alias pointing to backend.app.api app
try:
    from backend.app.api import app
    backend_pkg = types.ModuleType("BackEnd")
    main_mod = types.ModuleType("BackEnd.main")
    main_mod.app = app
    backend_pkg.main = main_mod
    sys.modules["BackEnd"] = backend_pkg
    sys.modules["BackEnd.main"] = main_mod
except Exception as e:
    print(f"conftest setup note: {e}")
