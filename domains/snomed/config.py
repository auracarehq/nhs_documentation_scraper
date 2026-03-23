"""SNOMED CT Snowstorm API configuration."""

# Public IHTSDO Snowstorm browser instance — suitable for testing/development.
# For production, point at the NHS ontology server or a self-hosted Snowstorm.
SNOWSTORM_BASE = "https://browser.ihtsdotools.org/snowstorm/snomed-ct"

# SNOMED CT UK Clinical Edition branch
UK_BRANCH = "MAIN/SNOMEDCT-UK"
UK_BRANCH_ENCODED = "MAIN%2FSNOMEDCT-UK"

DEFAULT_LIMIT = 25
MAX_LIMIT = 200
