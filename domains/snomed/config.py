"""SNOMED CT Snowstorm API configuration."""

# Public IHTSDO Snowstorm browser instance.
# All requests go through scraper.client.fetch() which enforces MAX_CONCURRENT
# and REQUEST_DELAY, so the shared rate limiter already applies here.
# For a self-hosted or NHS ontology server, update SNOWSTORM_BASE only.
SNOWSTORM_BASE = "https://browser.ihtsdotools.org/snowstorm/snomed-ct"

# SNOMED CT UK Clinical Edition branch
UK_BRANCH = "MAIN/SNOMEDCT-UK"
UK_BRANCH_ENCODED = "MAIN%2FSNOMEDCT-UK"

DEFAULT_LIMIT = 25
MAX_LIMIT = 200
