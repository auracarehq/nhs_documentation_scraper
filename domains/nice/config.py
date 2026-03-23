"""NICE platform configuration: CKS, BNF, and BNFc."""

NICE_CKS_BASE = "https://cks.nice.org.uk"
NICE_BNF_BASE = "https://bnf.nice.org.uk"
NICE_BNFC_BASE = "https://bnfc.nice.org.uk"

DOMAINS: dict[str, dict[str, str]] = {
    "nice:cks": {
        "base_url": NICE_CKS_BASE,
        "index_url": f"{NICE_CKS_BASE}/topics/",
        "link_prefix": "/topics/",
        "item_path": "/topics/{slug}/",
        "label": "NICE Clinical Knowledge Summaries",
    },
    "nice:bnf": {
        "base_url": NICE_BNF_BASE,
        "index_url": f"{NICE_BNF_BASE}/drugs/",
        "link_prefix": "/drugs/",
        "item_path": "/drugs/{slug}/",
        "label": "British National Formulary",
    },
    "nice:bnfc": {
        "base_url": NICE_BNFC_BASE,
        "index_url": f"{NICE_BNFC_BASE}/drugs/",
        "link_prefix": "/drugs/",
        "item_path": "/drugs/{slug}/",
        "label": "BNF for Children",
    },
}
