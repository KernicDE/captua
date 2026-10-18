"""`python -m captua` entry point (used by the self-updater to restart)."""

from .main import main

raise SystemExit(main())
