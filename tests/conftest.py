import sys
from pathlib import Path

# Add project root to sys.path so modules like BackEnd can be imported cleanly
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
