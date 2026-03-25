"""dm+d domain configuration."""

import os

# Snowstorm (SNOMED CT UK Drug Extension) — same base used by snomed domain
SNOWSTORM_BASE = os.environ.get(
    "SNOWSTORM_BASE",
    "https://snowstorm.platform.auracare.org.uk/snowstorm/snomed-ct",
)
UK_BRANCH_ENCODED = os.environ.get("SNOWSTORM_BRANCH", "MAIN").replace("/", "%2F")

# ECL expression for all medicinal products
MEDICINAL_PRODUCT_ECL = "<763158003"

# NHS Terminology Server FHIR endpoint (public read, no auth)
NHS_TS_FHIR_BASE = "https://ontology.nhs.uk/production1/fhir"
DMD_SYSTEM = "https://dmd.nhs.uk"
