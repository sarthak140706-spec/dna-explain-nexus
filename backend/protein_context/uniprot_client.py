import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


# ============================================================
# Make project root importable
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Imports
# ============================================================

from backend.protein_context.config import (
    HUMAN_TAXONOMY_ID,
    MAX_RETRIES,
    PROTEIN_CACHE_DIR,
    REQUEST_TIMEOUT_SECONDS,
    RETRY_BACKOFF_SECONDS,
    UNIPROT_ENTRY_URL,
    UNIPROT_SEARCH_URL,
)


# ============================================================
# Exceptions
# ============================================================

class UniProtClientError(RuntimeError):
    pass


class UniProtEntryNotFoundError(UniProtClientError):
    pass


# ============================================================
# Cache helpers
# ============================================================

def _cache_key(value: str) -> str:

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def _cache_path(prefix: str, key: str) -> Path:

    filename = (
        f"{prefix}_{_cache_key(key)}.json"
    )

    return (
        PROTEIN_CACHE_DIR
        / filename
    )


def _load_cache(
    path: Path,
) -> Optional[Dict[str, Any]]:

    if not path.exists():
        return None

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def _save_cache(
    path: Path,
    payload: Dict[str, Any],
) -> None:

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )


# ============================================================
# HTTP request helper
# ============================================================

def _request_json(
    url: str,
    params: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            response = requests.get(
                url,
                params=params,
                headers={
                    "Accept": (
                        "application/json"
                    )
                },
                timeout=(
                    REQUEST_TIMEOUT_SECONDS
                ),
            )

            response.raise_for_status()

            return response.json()

        except (
            requests.RequestException,
            ValueError,
        ) as error:

            last_error = error

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_BACKOFF_SECONDS
                    * attempt
                )

    raise UniProtClientError(
        "UniProt request failed after "
        f"{MAX_RETRIES} attempts: "
        f"{last_error}"
    )


# ============================================================
# Gene normalization
# ============================================================

def normalize_gene_symbol(
    gene_symbol: str,
) -> str:

    if gene_symbol is None:

        raise ValueError(
            "Gene symbol is required."
        )

    gene_symbol = str(
        gene_symbol
    ).strip().upper()

    if not gene_symbol:

        raise ValueError(
            "Gene symbol cannot be empty."
        )

    if len(gene_symbol) > 30:

        raise ValueError(
            "Gene symbol is unexpectedly long."
        )

    allowed = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789-_"
    )

    if not set(
        gene_symbol
    ).issubset(
        allowed
    ):

        raise ValueError(
            "Gene symbol contains "
            "unsupported characters."
        )

    return gene_symbol


# ============================================================
# Search reviewed human entries
# ============================================================

def search_reviewed_human_protein(
    gene_symbol: str,
    use_cache: bool = True,
) -> Dict[str, Any]:

    gene_symbol = (
        normalize_gene_symbol(
            gene_symbol
        )
    )

    cache_path = _cache_path(
        "gene_search",
        gene_symbol,
    )

    if use_cache:

        cached = _load_cache(
            cache_path
        )

        if cached is not None:

            return {
                "gene_symbol": (
                    gene_symbol
                ),
                "cache_hit": True,
                "response": cached,
            }

    query = (
        f"(gene_exact:{gene_symbol}) "
        f"AND (organism_id:"
        f"{HUMAN_TAXONOMY_ID}) "
        f"AND (reviewed:true)"
    )

    params = {
        "query": query,
        "format": "json",
        "size": 10,
    }

    response = _request_json(
        UNIPROT_SEARCH_URL,
        params=params,
    )

    _save_cache(
        cache_path,
        response,
    )

    return {
        "gene_symbol": (
            gene_symbol
        ),
        "cache_hit": False,
        "response": response,
    }


# ============================================================
# Select best UniProt entry
# ============================================================

def select_best_entry(
    search_response: Dict[
        str,
        Any,
    ],
    gene_symbol: str,
) -> Dict[str, Any]:

    gene_symbol = (
        normalize_gene_symbol(
            gene_symbol
        )
    )

    results = search_response.get(
        "results",
        [],
    )

    if not results:

        raise UniProtEntryNotFoundError(
            "No reviewed human UniProtKB "
            f"entry found for gene "
            f"{gene_symbol}."
        )

    exact_gene_matches = []

    for entry in results:

        genes = entry.get(
            "genes",
            [],
        )

        entry_symbols = []

        for gene in genes:

            primary_gene = (
                gene.get(
                    "geneName",
                    {}
                )
            )

            value = (
                primary_gene.get(
                    "value"
                )
            )

            if value:

                entry_symbols.append(
                    str(
                        value
                    ).upper()
                )

        if (
            gene_symbol
            in entry_symbols
        ):

            exact_gene_matches.append(
                entry
            )

    candidates = (
        exact_gene_matches
        if exact_gene_matches
        else results
    )

    # Search results are already relevance-ranked.
    # Prefer the first exact reviewed human match.
    selected = candidates[0]

    return selected


# ============================================================
# Retrieve UniProt entry
# ============================================================

def fetch_uniprot_entry(
    accession: str,
    use_cache: bool = True,
) -> Dict[str, Any]:

    accession = str(
        accession
    ).strip().upper()

    if not accession:

        raise ValueError(
            "UniProt accession is required."
        )

    cache_path = _cache_path(
        "entry",
        accession,
    )

    if use_cache:

        cached = _load_cache(
            cache_path
        )

        if cached is not None:

            return {
                "accession": accession,
                "cache_hit": True,
                "response": cached,
            }

    url = (
        f"{UNIPROT_ENTRY_URL}/"
        f"{accession}"
    )

    response = _request_json(
        url,
        params={
            "format": "json",
        },
    )

    _save_cache(
        cache_path,
        response,
    )

    return {
        "accession": accession,
        "cache_hit": False,
        "response": response,
    }


# ============================================================
# Gene -> reviewed human UniProt entry
# ============================================================

def get_reviewed_human_protein(
    gene_symbol: str,
    use_cache: bool = True,
) -> Dict[str, Any]:

    search_result = (
        search_reviewed_human_protein(
            gene_symbol,
            use_cache=use_cache,
        )
    )

    selected = select_best_entry(
        search_result[
            "response"
        ],
        gene_symbol,
    )

    accession = selected.get(
        "primaryAccession"
    )

    if not accession:

        raise UniProtClientError(
            "Selected UniProt result "
            "has no primary accession."
        )

    entry_result = (
        fetch_uniprot_entry(
            accession,
            use_cache=use_cache,
        )
    )

    return {
        "gene_symbol": (
            normalize_gene_symbol(
                gene_symbol
            )
        ),

        "accession": (
            accession
        ),

        "search_cache_hit": (
            search_result[
                "cache_hit"
            ]
        ),

        "entry_cache_hit": (
            entry_result[
                "cache_hit"
            ]
        ),

        "entry": (
            entry_result[
                "response"
            ]
        ),

        "source": "UniProtKB",

        "reviewed_human_only": True,
    }


# ============================================================
# CLI smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 6 "
        "UniProt Protein Retrieval Client"
    )

    print(
        "=" * 72
    )

    gene_symbol = "TP53"

    print(
        f"\nSearching reviewed human "
        f"protein for: {gene_symbol}"
    )

    result = (
        get_reviewed_human_protein(
            gene_symbol
        )
    )

    entry = result[
        "entry"
    ]

    accession = (
        entry.get(
            "primaryAccession"
        )
    )

    entry_type = (
        entry.get(
            "entryType"
        )
    )

    sequence = (
        entry.get(
            "sequence",
            {}
        )
    )

    length = (
        sequence.get(
            "length"
        )
    )

    organism = (
        entry.get(
            "organism",
            {}
        ).get(
            "scientificName"
        )
    )

    print(
        f"Accession: {accession}"
    )

    print(
        f"Entry type: {entry_type}"
    )

    print(
        f"Organism: {organism}"
    )

    print(
        f"Sequence length: {length}"
    )

    print(
        "Search cache hit:",
        result[
            "search_cache_hit"
        ],
    )

    print(
        "Entry cache hit:",
        result[
            "entry_cache_hit"
        ],
    )

    print(
        "\n✅ UniProt retrieval "
        "client completed."
    )


if __name__ == "__main__":
    main()