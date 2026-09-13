import time
from typing import Any

import requests

from config import (
    ENSEMBL_REST_SERVER,
    VEP_REGION_ENDPOINT,
    REQUEST_TIMEOUT_SECONDS,
    MAX_RETRIES,
    VEP_BATCH_SIZE,
)


# ============================================================
# Variant formatting
# ============================================================

def build_vep_variant(
    chromosome: str,
    position: int,
    reference: str,
    alternate: str,
) -> str:
    """
    Convert a GeneMirror genomic SNV into
    Ensembl VEP region format.

    Example:
        chromosome = 17
        position = 7674208
        reference = A
        alternate = G

    Output:
        17 7674208 7674208 A/G
    """

    chromosome = str(
        chromosome
    ).strip()

    reference = str(
        reference
    ).strip().upper()

    alternate = str(
        alternate
    ).strip().upper()

    position = int(
        position
    )

    if not chromosome:
        raise ValueError(
            "Chromosome cannot be empty."
        )

    if position <= 0:
        raise ValueError(
            "Genomic position must be positive."
        )

    valid_bases = {
        "A",
        "C",
        "G",
        "T",
    }

    if reference not in valid_bases:
        raise ValueError(
            f"Invalid reference allele: "
            f"{reference}"
        )

    if alternate not in valid_bases:
        raise ValueError(
            f"Invalid alternate allele: "
            f"{alternate}"
        )

    if reference == alternate:
        raise ValueError(
            "Reference and alternate alleles "
            "cannot be identical."
        )

    return (
        f"{chromosome} "
        f"{position} "
        f"{position} "
        f"{reference}/{alternate}"
    )


# ============================================================
# Payload
# ============================================================

def build_vep_payload(
    variants: list[str],
) -> dict[str, list[str]]:
    """
    Build the JSON body sent to the
    Ensembl VEP REST endpoint.
    """

    if not variants:
        raise ValueError(
            "Variant list cannot be empty."
        )

    if len(variants) > VEP_BATCH_SIZE:
        raise ValueError(
            f"Maximum VEP batch size is "
            f"{VEP_BATCH_SIZE} variants."
        )

    return {
        "variants": variants,
    }


# ============================================================
# Logging helpers
# ============================================================

def _print_request_error(
    error: Exception,
) -> None:
    """
    Print detailed request error information
    for production debugging.
    """

    print(
        "========== ENSEMBL VEP ERROR ==========",
        flush=True,
    )

    print(
        "Error type:",
        type(error).__name__,
        flush=True,
    )

    print(
        "Error:",
        str(error),
        flush=True,
    )

    if isinstance(
        error,
        requests.exceptions.HTTPError,
    ):
        response = error.response

        if response is not None:

            print(
                "HTTP status:",
                response.status_code,
                flush=True,
            )

            print(
                "Response URL:",
                response.url,
                flush=True,
            )

            print(
                "Response body:",
                response.text[:2000],
                flush=True,
            )

    print(
        "=======================================",
        flush=True,
    )


# ============================================================
# Ensembl VEP request
# ============================================================

def annotate_variants(
    variants: list[str],
) -> list[dict[str, Any]]:
    """
    Send genomic variants to Ensembl VEP.

    Returns the raw JSON response produced
    by the VEP REST service.
    """

    payload = build_vep_payload(
        variants
    )

    url = (
        ENSEMBL_REST_SERVER
        + VEP_REGION_ENDPOINT
    )

    params = {
        "hgvs": 1,
        "mane": 1,
        "canonical": 1,
        "numbers": 1,
    }

    headers = {
        "Content-Type": (
            "application/json"
        ),
        "Accept": (
            "application/json"
        ),
        "User-Agent": (
            "GeneMirror-AI/1.0 "
            "(research-and-education)"
        ),
    }

    last_error: Exception | None = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        print(
            f"VEP request attempt "
            f"{attempt}/{MAX_RETRIES}",
            flush=True,
        )

        print(
            "VEP URL:",
            url,
            flush=True,
        )

        print(
            "VEP variants:",
            variants,
            flush=True,
        )

        try:

            response = requests.post(
                url,
                params=params,
                headers=headers,
                json=payload,
                timeout=(
                    REQUEST_TIMEOUT_SECONDS
                ),
            )

            print(
                "VEP response status:",
                response.status_code,
                flush=True,
            )

            # ------------------------------------------------
            # Rate limiting
            # ------------------------------------------------

            if response.status_code == 429:

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )

                if retry_after:

                    try:
                        wait_seconds = float(
                            retry_after
                        )

                    except ValueError:
                        wait_seconds = (
                            attempt * 5
                        )

                else:
                    wait_seconds = (
                        attempt * 5
                    )

                last_error = (
                    requests.exceptions.HTTPError(
                        "Ensembl VEP rate limit "
                        "reached.",
                        response=response,
                    )
                )

                _print_request_error(
                    last_error
                )

                if attempt < MAX_RETRIES:

                    print(
                        f"Retrying after "
                        f"{wait_seconds} seconds...",
                        flush=True,
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                break

            # ------------------------------------------------
            # Temporary Ensembl server failures
            # ------------------------------------------------

            if (
                500
                <= response.status_code
                < 600
            ):

                last_error = (
                    requests.exceptions.HTTPError(
                        "Temporary Ensembl "
                        "server error.",
                        response=response,
                    )
                )

                _print_request_error(
                    last_error
                )

                if attempt < MAX_RETRIES:

                    wait_seconds = (
                        attempt * 5
                    )

                    print(
                        f"Retrying after "
                        f"{wait_seconds} seconds...",
                        flush=True,
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                break

            # ------------------------------------------------
            # Other HTTP errors
            # ------------------------------------------------

            response.raise_for_status()

            # ------------------------------------------------
            # JSON decoding
            # ------------------------------------------------

            try:

                data = response.json()

            except ValueError as error:

                last_error = error

                print(
                    "========== INVALID JSON ==============",
                    flush=True,
                )

                print(
                    "Response:",
                    response.text[:2000],
                    flush=True,
                )

                print(
                    "======================================",
                    flush=True,
                )

                if attempt < MAX_RETRIES:

                    wait_seconds = (
                        attempt * 2
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                break

            # ------------------------------------------------
            # Schema validation
            # ------------------------------------------------

            if not isinstance(
                data,
                list,
            ):
                raise ValueError(
                    "Unexpected Ensembl "
                    "response format. "
                    "Expected a JSON list."
                )

            print(
                f"VEP request successful. "
                f"Returned {len(data)} "
                f"annotation result(s).",
                flush=True,
            )

            return data

        # ====================================================
        # Timeout
        # ====================================================

        except requests.exceptions.Timeout as error:

            last_error = error

            print(
                "Ensembl VEP request timed out.",
                flush=True,
            )

            _print_request_error(
                error
            )

        # ====================================================
        # Connection errors
        # ====================================================

        except requests.exceptions.ConnectionError as error:

            last_error = error

            print(
                "Could not connect to "
                "Ensembl REST API.",
                flush=True,
            )

            _print_request_error(
                error
            )

        # ====================================================
        # HTTP errors
        # ====================================================

        except requests.exceptions.HTTPError as error:

            last_error = error

            _print_request_error(
                error
            )

        # ====================================================
        # Other requests errors
        # ====================================================

        except requests.RequestException as error:

            last_error = error

            _print_request_error(
                error
            )

        # ====================================================
        # Response / validation errors
        # ====================================================

        except ValueError as error:

            last_error = error

            print(
                "Ensembl response validation "
                f"failed: {error}",
                flush=True,
            )

        # ====================================================
        # Retry
        # ====================================================

        if attempt < MAX_RETRIES:

            wait_seconds = (
                attempt * 3
            )

            print(
                f"Retrying Ensembl VEP "
                f"after {wait_seconds} seconds...",
                flush=True,
            )

            time.sleep(
                wait_seconds
            )

    # ========================================================
    # All retries failed
    # ========================================================

    error_message = (
        "Ensembl VEP request failed "
        f"after {MAX_RETRIES} attempts."
    )

    if last_error is not None:

        error_message += (
            f" Last error: "
            f"{type(last_error).__name__}: "
            f"{last_error}"
        )

    raise RuntimeError(
        error_message
    ) from last_error


# ============================================================
# Single variant helper
# ============================================================

def annotate_single_variant(
    chromosome: str,
    position: int,
    reference: str,
    alternate: str,
) -> dict[str, Any]:
    """
    Convenience function for annotating
    one genomic variant.
    """

    variant = build_vep_variant(
        chromosome=chromosome,
        position=position,
        reference=reference,
        alternate=alternate,
    )

    results = annotate_variants(
        [
            variant,
        ]
    )

    if not results:
        raise ValueError(
            "Ensembl returned no annotation."
        )

    return results[0]


# ============================================================
# Result debugging
# ============================================================

def print_basic_result(
    result: dict[str, Any],
) -> None:
    """
    Print basic fields from a raw
    Ensembl VEP response.
    """

    print(
        "\nBasic VEP result"
    )

    print(
        "-" * 45
    )

    print(
        "Input:",
        result.get(
            "input"
        ),
    )

    print(
        "Most severe consequence:",
        result.get(
            "most_severe_consequence"
        ),
    )

    print(
        "Assembly:",
        result.get(
            "assembly_name"
        ),
    )

    print(
        "Chromosome:",
        result.get(
            "seq_region_name"
        ),
    )

    print(
        "Start:",
        result.get(
            "start"
        ),
    )

    print(
        "End:",
        result.get(
            "end"
        ),
    )

    transcript_consequences = (
        result.get(
            "transcript_consequences",
            [],
        )
    )

    print(
        "Transcript consequences:",
        len(
            transcript_consequences
        ),
    )

    if transcript_consequences:

        first = (
            transcript_consequences[0]
        )

        print(
            "First transcript:",
            first.get(
                "transcript_id"
            ),
        )

        print(
            "Gene:",
            first.get(
                "gene_symbol"
            ),
        )

        print(
            "HGVSc:",
            first.get(
                "hgvsc"
            ),
        )

        print(
            "HGVSp:",
            first.get(
                "hgvsp"
            ),
        )


# ============================================================
# Local test
# ============================================================

if __name__ == "__main__":

    try:

        print(
            "GeneMirror Ensembl VEP Client"
        )

        print(
            "-" * 45
        )

        # Known GRCh38 TP53 SNV used only
        # to verify communication with the
        # Ensembl REST API.
        #
        # Do not interpret this test variant
        # as the GeneMirror R248H demo preset.

        test_variant = (
            build_vep_variant(
                chromosome="17",
                position=7674208,
                reference="A",
                alternate="G",
            )
        )

        print(
            "\nTest VEP representation:"
        )

        print(
            test_variant
        )

        result = annotate_variants(
            [
                test_variant,
            ]
        )

        print(
            f"\nVariants returned: "
            f"{len(result)}"
        )

        if result:

            print_basic_result(
                result[0]
            )

        print(
            "\nVEP client test "
            "completed successfully."
        )

    except Exception as error:

        print(
            "\nVEP client test failed."
        )

        print(
            "Error type:",
            type(error).__name__,
        )

        print(
            f"Error: {error}"
        )

        raise