import re

import pandas as pd


def standardize_text(value):
    """
    Standardize string values.

    Converts missing-like values to pandas NA
    and strips unnecessary whitespace.
    """

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if value.lower() in {
        "",
        "-",
        "na",
        "n/a",
        "none",
        "null",
    }:
        return pd.NA

    return value


def extract_dna_change(name):
    """
    Extract coding DNA change from the ClinVar Name field.

    Example:
    NM_000546.6(TP53):c.743G>A (p.Arg248Gln)

    Returns:
    c.743G>A
    """

    if pd.isna(name):
        return pd.NA

    match = re.search(
        r"(c\.[^ \(\)]+)",
        str(name),
    )

    if match:
        return match.group(1)

    return pd.NA


def extract_protein_change(name):
    """
    Extract protein change from the ClinVar Name field.

    Example:
    NM_000546.6(TP53):c.743G>A (p.Arg248Gln)

    Returns:
    p.Arg248Gln
    """

    if pd.isna(name):
        return pd.NA

    match = re.search(
        r"\((p\.[^\)]+)\)",
        str(name),
    )

    if match:
        return match.group(1)

    return pd.NA


def is_missense_protein_change(value):
    """
    Check whether a protein change represents
    a simple missense amino-acid substitution.

    Accepted example:
    p.Arg248Gln

    Rejected examples:
    p.Arg97Ter
    p.Leu473fs
    p.?
    p.Gly12=
    """

    if pd.isna(value):
        return False

    value = str(value).strip()

    amino_acids = {
        "Ala",
        "Arg",
        "Asn",
        "Asp",
        "Cys",
        "Gln",
        "Glu",
        "Gly",
        "His",
        "Ile",
        "Leu",
        "Lys",
        "Met",
        "Phe",
        "Pro",
        "Ser",
        "Thr",
        "Trp",
        "Tyr",
        "Val",
    }

    match = re.match(
        r"^p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})$",
        value,
    )

    if not match:
        return False

    reference_aa = match.group(1)
    alternate_aa = match.group(3)

    if reference_aa not in amino_acids:
        return False

    if alternate_aa not in amino_acids:
        return False

    if reference_aa == alternate_aa:
        return False

    return True

def clean_clinvar(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean validated ClinVar records for GeneMirror.

    Expected input:
    Dataframe produced by validator.py
    """

    if "validation_passed" not in df.columns:
        raise ValueError(
            "Input dataframe must be validated first."
        )

    cleaned = df[
        df["validation_passed"] == True
    ].copy()

    text_columns = [
        "#AlleleID",
        "Type",
        "Name",
        "GeneID",
        "GeneSymbol",
        "ClinicalSignificance",
        "OriginSimple",
        "Assembly",
        "Chromosome",
        "Start",
        "Stop",
        "ReferenceAlleleVCF",
        "AlternateAlleleVCF",
        "ReviewStatus",
        "VariationID",
    ]

    for column in text_columns:
        if column in cleaned.columns:
            cleaned[column] = (
                cleaned[column]
                .apply(standardize_text)
            )

    cleaned["GeneSymbol"] = (
        cleaned["GeneSymbol"]
        .str.upper()
    )

    cleaned["ReferenceAlleleVCF"] = (
        cleaned["ReferenceAlleleVCF"]
        .str.upper()
    )

    cleaned["AlternateAlleleVCF"] = (
        cleaned["AlternateAlleleVCF"]
        .str.upper()
    )

    cleaned["dna_change"] = (
        cleaned["Name"]
        .apply(extract_dna_change)
    )

    cleaned["protein_change"] = (
        cleaned["Name"]
        .apply(extract_protein_change)
    )

    cleaned["is_missense"] = (
        cleaned["protein_change"]
        .apply(is_missense_protein_change)
    )

    cleaned = cleaned[
        cleaned["is_missense"] == True
    ].copy()

    cleaned = cleaned.drop_duplicates(
        subset=[
            "VariationID",
            "Assembly",
        ]
    )

    cleaned = cleaned.reset_index(
        drop=True
    )

    return cleaned


def cleaning_summary(
    before: pd.DataFrame,
    after: pd.DataFrame,
) -> dict:
    """
    Return a basic cleaning summary.
    """

    return {
        "input_rows": len(before),
        "output_rows": len(after),
        "removed_rows": (
            len(before) - len(after)
        ),
        "retained_percentage": (
            round(
                len(after)
                / len(before)
                * 100,
                2,
            )
            if len(before) > 0
            else 0.0
        ),
    }


if __name__ == "__main__":

    try:

        from loader import load_clinvar_sample
        from validator import validate_dataframe

        print("GeneMirror ClinVar Cleaner")
        print("-" * 40)

        sample = load_clinvar_sample(
            rows=10_000
        )

        print(
            f"\nLoaded sample rows: {len(sample)}"
        )

        validated = validate_dataframe(
            sample
        )

        cleaned = clean_clinvar(
            validated
        )

        summary = cleaning_summary(
            validated,
            cleaned,
        )

        print("\nCleaning Summary")

        for key, value in summary.items():
            print(f"{key}: {value}")

        print("\nCleaned sample:")

        display_columns = [
            "GeneSymbol",
            "VariationID",
            "Assembly",
            "ReferenceAlleleVCF",
            "AlternateAlleleVCF",
            "dna_change",
            "protein_change",
            "ClinicalSignificance",
        ]

        print(
            cleaned[
                display_columns
            ].head(20).to_string(
                index=False
            )
        )

        print(
            "\nCleaner test completed successfully."
        )

    except Exception as error:

        print("\nCleaner test failed:")
        print(error)