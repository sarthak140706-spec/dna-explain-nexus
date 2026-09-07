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
        position = 7674220
        reference = G
        alternate = A

    Output:
        17 7674220 7674220 G/A
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

    return (
        f"{chromosome} "
        f"{position} "
        f"{position} "
        f"{reference}/{alternate}"
    )


def build_vep_payload(
    variants: list[str],
) -> dict:
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
        "Content-Type":
            "application/json",

        "Accept":
            "application/json",
    }

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            print(
                f"VEP request attempt "
                f"{attempt}/{MAX_RETRIES}"
            )

            response = requests.post(
                url,
                params=params,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(
                data,
                list,
            ):
                raise ValueError(
                    "Unexpected Ensembl "
                    "response format."
                )

            return data

        except (
            requests.RequestException,
            ValueError,
        ) as error:

            last_error = error

            print(
                f"VEP request failed: "
                f"{error}"
            )

            if attempt < MAX_RETRIES:

                wait_seconds = (
                    attempt * 2
                )

                print(
                    f"Retrying after "
                    f"{wait_seconds} seconds..."
                )

                time.sleep(
                    wait_seconds
                )

    raise RuntimeError(
        "Ensembl VEP request failed "
        f"after {MAX_RETRIES} attempts."
    ) from last_error


def annotate_single_variant(
    chromosome: str,
    position: int,
    reference: str,
    alternate: str,
) -> dict:
    """
    Convenience function for testing
    a single genomic variant.
    """

    variant = build_vep_variant(
        chromosome=chromosome,
        position=position,
        reference=reference,
        alternate=alternate,
    )

    results = annotate_variants(
        [variant]
    )

    if not results:
        raise ValueError(
            "Ensembl returned no annotation."
        )

    return results[0]


def print_basic_result(
    result: dict,
) -> None:
    """
    Print basic fields from a raw
    Ensembl VEP response.
    """

    print(
        "\nBasic VEP result"
    )

    print("-" * 45)

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


if __name__ == "__main__":

    try:

        print(
            "GeneMirror Ensembl VEP Client"
        )

        print("-" * 45)

        # A real TP53 GRCh38 SNV from the
        # GeneMirror processed dataset will
        # be supplied during testing below.

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
            [test_variant]
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
            f"Error: {error}"
        )

        raise