"""SNOMED CT Snowstorm API configuration."""

import os

# Self-hosted Snowstorm instance (Azure Container Apps, UK South).
# Falls back to public IHTSDO browser instance if env var not set.
SNOWSTORM_BASE = os.environ.get(
    "SNOWSTORM_BASE",
    "https://snowstorm.platform.auracare.org.uk/snowstorm/snomed-ct",
)

# Branch where UK Edition data lives on our self-hosted Snowstorm
UK_BRANCH = os.environ.get("SNOWSTORM_BRANCH", "MAIN")
UK_BRANCH_ENCODED = UK_BRANCH.replace("/", "%2F")

DEFAULT_LIMIT = 25
MAX_LIMIT = 200
