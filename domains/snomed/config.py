"""SNOMED CT Snowstorm API configuration."""

import os

# Self-hosted Snowstorm instance (Azure Container Apps, UK South).
# Falls back to public IHTSDO browser instance if env var not set.
SNOWSTORM_BASE = os.environ.get(
    "SNOWSTORM_BASE",
    "https://snowstorm.platform.auracare.org.uk/snowstorm/snomed-ct",
)

# SNOMED CT UK Clinical Edition branch
UK_BRANCH = "MAIN/SNOMEDCT-UK"
UK_BRANCH_ENCODED = "MAIN%2FSNOMEDCT-UK"

DEFAULT_LIMIT = 25
MAX_LIMIT = 200
