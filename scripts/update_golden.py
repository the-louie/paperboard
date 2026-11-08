"""Re-render every golden image: python scripts/update_golden.py [pytest args]."""

import os
import subprocess
import sys

os.environ["PAPERBOARD_UPDATE_GOLDEN"] = "1"
sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-q", *sys.argv[1:]]))
