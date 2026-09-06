import pandas as pd


REQUIRED_COLUMNS = [
    "#AlleleID",
    "Type",
    "Name",
    "GeneSymbol",
    "ClinicalSignificance",
    "OriginSimple",
    "Assembly",
    "Chromosome",
    "Start",
    "Stop",
    "PositionVCF",
    "ReferenceAlleleVCF",
    "AlternateAlleleVCF",
    "ReviewStatus",
    "VariationID",
]


SUPPORTED_ASSEMBLY = "GRCh38"

SUPPORTED_TYPE = "single nucleotide variant"

SUPPORTED_ORIGIN = "germline"


VALID_BASES = {
    "A",
    "C",
    "G",
    "T",
}


VALID_CHROMOSOMES = {
    *(str(i) for i in range(1, 23)),
    "X",
    "Y",
}


MISSING_VALUES = {
    "",
    "-",
    "na",
    "n/a",
    "none",
    "null",
}


def has_required_columns(df: pd.DataFrame) -> bool:
    """
    Check whether the dataframe contains all
    columns required by the GeneMirror pipeline.
    """

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        print("Missing required columns:")

        for column in missing:
            print(f"- {column}")

        return False

    return True


def is_missing(value) -> bool:
    """
    Check whether a value should be treated as missing.
    """

    if pd.isna(value):
        return True

    value = str(value).strip().lower()

    return value in MISSING_VALUES


def normalize_chromosome_for_validation(value):
    """
    Normalize chromosome notation for validation.

    Examples:
    chr1 -> 1
    chrX -> X
    x -> X
    """

    if is_missing(value):
        return ""

    value = str(value).strip()

    if value.lower().startswith("chr"):
        value = value[3:]

    return value.upper()


def validate_variant_row(
    row: pd.Series,
) -> tuple[bool, list[str]]:
    """
    Validate a single ClinVar record.

    GeneMirror V1 accepts:
    - GRCh38
    - germline
    - single nucleotide variants
    - chromosomes 1-22, X, Y
    - unambiguous A/C/G/T REF and ALT bases

    Returns:
        (is_valid, list_of_errors)
    """

    errors = []

    # --------------------------------------------------
    # Required metadata
    # --------------------------------------------------

    if is_missing(
        row.get("GeneSymbol")
    ):
        errors.append(
            "missing_gene_symbol"
        )

    if is_missing(
        row.get("VariationID")
    ):
        errors.append(
            "missing_variation_id"
        )

    if is_missing(
        row.get(
            "ClinicalSignificance"
        )
    ):
        errors.append(
            "missing_clinical_significance"
        )

    # --------------------------------------------------
    # Variant type
    # --------------------------------------------------

    variant_type = str(
        row.get("Type", "")
    ).strip().lower()

    if (
        variant_type
        != SUPPORTED_TYPE
    ):
        errors.append(
            "unsupported_variant_type"
        )

    # --------------------------------------------------
    # Genome assembly
    # --------------------------------------------------

    assembly = str(
        row.get("Assembly", "")
    ).strip()

    if (
        assembly
        != SUPPORTED_ASSEMBLY
    ):
        errors.append(
            "unsupported_assembly"
        )

    # --------------------------------------------------
    # Origin
    # --------------------------------------------------

    origin = str(
        row.get(
            "OriginSimple",
            "",
        )
    ).strip().lower()

    if (
        origin
        != SUPPORTED_ORIGIN
    ):
        errors.append(
            "unsupported_origin"
        )

    # --------------------------------------------------
    # Chromosome
    # --------------------------------------------------

    chromosome = (
        normalize_chromosome_for_validation(
            row.get("Chromosome")
        )
    )

    if chromosome not in VALID_CHROMOSOMES:
        errors.append(
            "unsupported_chromosome"
        )

    # --------------------------------------------------
    # REF / ALT
    # --------------------------------------------------

    ref = row.get(
        "ReferenceAlleleVCF"
    )

    alt = row.get(
        "AlternateAlleleVCF"
    )

    if is_missing(ref):

        errors.append(
            "missing_reference_allele"
        )

    else:

        ref = str(
            ref
        ).strip().upper()

        if ref not in VALID_BASES:
            errors.append(
                "invalid_reference_allele"
            )

    if is_missing(alt):

        errors.append(
            "missing_alternate_allele"
        )

    else:

        alt = str(
            alt
        ).strip().upper()

        if alt not in VALID_BASES:
            errors.append(
                "invalid_alternate_allele"
            )

    # --------------------------------------------------
    # REF and ALT must differ
    # --------------------------------------------------

    if (
        not is_missing(ref)
        and not is_missing(alt)
    ):

        if (
            str(ref).upper()
            == str(alt).upper()
        ):
            errors.append(
                "reference_equals_alternate"
            )

    return (
        len(errors) == 0,
        errors,
    )


def validate_dataframe(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Validate all rows in a dataframe.

    Adds:
        validation_passed
        validation_errors
    """

    if not has_required_columns(
        df
    ):
        raise ValueError(
            "ClinVar dataframe does not "
            "contain all required columns."
        )

    results = df.apply(
        validate_variant_row,
        axis=1,
    )

    validated = df.copy()

    validated[
        "validation_passed"
    ] = [
        result[0]
        for result in results
    ]

    validated[
        "validation_errors"
    ] = [
        "|".join(
            result[1]
        )
        for result in results
    ]

    return validated


def validation_summary(
    df: pd.DataFrame,
) -> dict:
    """
    Produce a summary of validation results.
    """

    if (
        "validation_passed"
        not in df.columns
    ):
        raise ValueError(
            "Dataframe has not "
            "been validated yet."
        )

    total = len(df)

    valid = int(
        df[
            "validation_passed"
        ].sum()
    )

    invalid = total - valid

    return {
        "total_rows":
            total,

        "valid_rows":
            valid,

        "invalid_rows":
            invalid,

        "valid_percentage":
            (
                round(
                    valid
                    / total
                    * 100,
                    2,
                )
                if total > 0
                else 0.0
            ),
    }


if __name__ == "__main__":

    try:

        from loader import (
            load_clinvar_sample,
        )

        print(
            "GeneMirror Variant Validator"
        )

        print("-" * 40)

        sample = (
            load_clinvar_sample(
                rows=1000
            )
        )

        print(
            f"\nLoaded sample rows: "
            f"{len(sample)}"
        )

        validated = (
            validate_dataframe(
                sample
            )
        )

        summary = (
            validation_summary(
                validated
            )
        )

        print(
            "\nValidation Summary"
        )

        for key, value in (
            summary.items()
        ):
            print(
                f"{key}: {value}"
            )

        print(
            "\nExample validation results:"
        )

        columns = [
            "GeneSymbol",
            "Type",
            "Assembly",
            "Chromosome",
            "ReferenceAlleleVCF",
            "AlternateAlleleVCF",
            "validation_passed",
            "validation_errors",
        ]

        print(
            validated[
                columns
            ]
            .head(20)
            .to_string(
                index=False
            )
        )

        print(
            "\nValidator test "
            "completed successfully."
        )

    except Exception as error:

        print(
            "\nValidator test failed:"
        )

        print(error)