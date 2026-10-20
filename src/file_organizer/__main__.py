"""Allow ``python -m file_organizer``."""

import sys

from .cli import main

sys.exit(main())
