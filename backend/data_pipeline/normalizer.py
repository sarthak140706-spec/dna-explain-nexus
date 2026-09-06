import re

import pandas as pd


AMINO_ACID_3_TO_1 = {
    "Ala": "A",
    "Arg": "R",
    "Asn": "N",
    "Asp": "D",
    "Cys": "C",
    "Gln": "Q",
    "Glu": "E",
    "Gly": "G",
    "His": "H",
    "Ile": "I",
    "Leu": "L",
    "Lys": "K",
    "Met": "M",
    "Phe": "F",
    "Pro": "P",
    "Ser": "S",
    "Thr": "T",
    "Trp": "W",
    "Tyr": "Y",
    "Val": "V",
}


def normalize_chromosome(value):
    """
    Normalize chromosome names.

    Examples:
    1 -> 1
    chr1 -> 1
    x -> X
    chrX -> X
    """

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if value.lower().startswith("chr"):
        value = value[3:]

    value = value.upper()

    return value


def normalize_dbsnp(value):
    """
    Normalize dbSNP identifiers.

    Example:
    123456 -> rs123456
    rs123456 -> rs123456
    """

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if value.lower() in {
        "",
        "-",
        "na",
        "nan",
        "none",
    }:
        return pd.NA

    if value.lower().startswith("rs"):
        return value.lower()

    if value.isdigit():
        return f"rs{value}"

    return value


def parse_protein_change(value):
    """
    Parse a simple missense protein substitution.

    Example:
    p.Arg248His

    Returns:
    reference amino acid,
    protein position,
    alternate amino acid
    """

    if pd.isna(value):
        return pd.NA, pd.NA, pd.NA

    match = re.match(
        r"^p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})$",
        str(value).strip(),
    )

    if not match:
        return pd.NA, pd.NA, pd.NA

    reference_aa = match.group(1)
    position = int(match.group(2))
    alternate_aa = match.group(3)

    return (
        reference_aa,
        position,
        alternate_aa,
    )


def create_variant_key(row):
    """
    Create a unique genomic representation.

    Example:
    chr17:7674220:G>A
    """

    chromosome = row["chromosome"]
    position = row["position"]
    reference = row["reference_allele"]
    alternate = row["alternate_allele"]

    if (
        pd.isna(chromosome)
        or pd.isna(position)
        or pd.isna(reference)
        or pd.isna(alternate)
    ):
        return pd.NA

    return (
        f"chr{chromosome}:"
        f"{int(position)}:"
        f"{reference}>{alternate}"
    )


def normalize_clinvar(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize cleaned ClinVar missense variants
    into GeneMirror's internal data format.
    """

    required_columns = [
        "#AlleleID",
        "VariationID",
        "GeneID",
        "GeneSymbol",
        "HGNC_ID",
        "Name",
        "ClinicalSignificance",
        "ClinSigSimple",
        "LastEvaluated",
        "RS# (dbSNP)",
        "PhenotypeList",
        "OriginSimple",
        "Assembly",
        "Chromosome",
        "PositionVCF",
        "ReferenceAlleleVCF",
        "AlternateAlleleVCF",
        "ReviewStatus",
        "NumberSubmitters",
        "dna_change",
        "protein_change",
        "is_missense",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    normalized = df[
        required_columns
    ].copy()

    normalized = normalized.rename(
        columns={
            "#AlleleID": "allele_id",
            "VariationID": "variation_id",
            "GeneID": "gene_id",
            "GeneSymbol": "gene_symbol",
            "HGNC_ID": "hgnc_id",
            "Name": "clinvar_name",
            "ClinicalSignificance":
                "source_clinical_significance",
            "ClinSigSimple":
                "source_clinsig_simple",
            "LastEvaluated":
                "last_evaluated",
            "RS# (dbSNP)":
                "dbsnp_id",
            "PhenotypeList":
                "phenotype_list",
            "OriginSimple":
                "origin",
            "Assembly":
                "assembly",
            "Chromosome":
                "chromosome",
            "PositionVCF":
                "position",
            "ReferenceAlleleVCF":
                "reference_allele",
            "AlternateAlleleVCF":
                "alternate_allele",
            "ReviewStatus":
                "review_status",
            "NumberSubmitters":
                "number_submitters",
        }
    )

    normalized["gene_symbol"] = (
        normalized["gene_symbol"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    normalized["chromosome"] = (
        normalized["chromosome"]
        .apply(normalize_chromosome)
    )

    normalized["reference_allele"] = (
        normalized["reference_allele"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    normalized["alternate_allele"] = (
        normalized["alternate_allele"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    normalized["position"] = pd.to_numeric(
        normalized["position"],
        errors="coerce",
    ).astype("Int64")

    normalized["number_submitters"] = (
        pd.to_numeric(
            normalized["number_submitters"],
            errors="coerce",
        ).astype("Int64")
    )

    normalized["allele_id"] = pd.to_numeric(
        normalized["allele_id"],
        errors="coerce",
    ).astype("Int64")

    normalized["variation_id"] = (
        pd.to_numeric(
            normalized["variation_id"],
            errors="coerce",
        ).astype("Int64")
    )

    normalized["gene_id"] = pd.to_numeric(
        normalized["gene_id"],
        errors="coerce",
    ).astype("Int64")

    normalized["dbsnp_id"] = (
        normalized["dbsnp_id"]
        .apply(normalize_dbsnp)
    )

    protein_parts = (
        normalized["protein_change"]
        .apply(parse_protein_change)
    )

    normalized["reference_aa_3"] = [
        value[0]
        for value in protein_parts
    ]

    normalized["protein_position"] = [
        value[1]
        for value in protein_parts
    ]

    normalized["alternate_aa_3"] = [
        value[2]
        for value in protein_parts
    ]

    normalized["protein_position"] = (
        pd.to_numeric(
            normalized["protein_position"],
            errors="coerce",
        ).astype("Int64")
    )

    normalized["reference_aa"] = (
        normalized["reference_aa_3"]
        .map(AMINO_ACID_3_TO_1)
    )

    normalized["alternate_aa"] = (
        normalized["alternate_aa_3"]
        .map(AMINO_ACID_3_TO_1)
    )

    normalized["amino_acid_change"] = (
        normalized["reference_aa"]
        + normalized["protein_position"]
        .astype("string")
        + normalized["alternate_aa"]
    )

    normalized["variant_key"] = (
        normalized.apply(
            create_variant_key,
            axis=1,
        )
    )

    normalized = normalized.drop_duplicates(
        subset=["variant_key"]
    )

    normalized = normalized.reset_index(
        drop=True
    )

    return normalized


def normalization_summary(
    df: pd.DataFrame,
) -> dict:
    """
    Generate summary statistics for
    normalized GeneMirror variants.
    """

    return {
        "total_variants": len(df),
        "unique_genes":
            df["gene_symbol"].nunique(),
        "unique_variants":
            df["variant_key"].nunique(),
        "missing_variant_keys":
            int(df["variant_key"].isna().sum()),
        "missing_protein_positions":
            int(
                df[
                    "protein_position"
                ].isna().sum()
            ),
    }


if __name__ == "__main__":

    try:

        from loader import load_clinvar_sample
        from validator import validate_dataframe
        from cleaner import clean_clinvar

        print("GeneMirror Variant Normalizer")
        print("-" * 40)

        sample = load_clinvar_sample(
            rows=10_000
        )

        validated = validate_dataframe(
            sample
        )

        cleaned = clean_clinvar(
            validated
        )

        normalized = normalize_clinvar(
            cleaned
        )

        summary = normalization_summary(
            normalized
        )

        print("\nNormalization Summary")

        for key, value in summary.items():
            print(f"{key}: {value}")

        display_columns = [
            "gene_symbol",
            "variation_id",
            "dbsnp_id",
            "chromosome",
            "position",
            "reference_allele",
            "alternate_allele",
            "dna_change",
            "protein_change",
            "reference_aa",
            "protein_position",
            "alternate_aa",
            "amino_acid_change",
            "variant_key",
        ]

        print("\nNormalized sample:")

        print(
            normalized[
                display_columns
            ].head(20).to_string(
                index=False
            )
        )

        print(
            "\nNormalizer test completed successfully."
        )

    except Exception as error:

        print("\nNormalizer test failed:")
        print(error)