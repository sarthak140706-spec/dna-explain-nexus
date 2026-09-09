import math

import pandas as pd

try:
    from .config import (
        MODELING_DATASET_PATH,
        FEATURE_DATASET_PATH,
        TARGET_COLUMN,
    )

except ImportError:
    from config import (
        MODELING_DATASET_PATH,
        FEATURE_DATASET_PATH,
        TARGET_COLUMN,
    )


# ============================================================
# Amino-acid physicochemical properties
# ============================================================

# Approximate residue molecular weights
AA_MOLECULAR_WEIGHT = {
    "A": 89.09,
    "R": 174.20,
    "N": 132.12,
    "D": 133.10,
    "C": 121.16,
    "E": 147.13,
    "Q": 146.15,
    "G": 75.07,
    "H": 155.16,
    "I": 131.17,
    "L": 131.17,
    "K": 146.19,
    "M": 149.21,
    "F": 165.19,
    "P": 115.13,
    "S": 105.09,
    "T": 119.12,
    "W": 204.23,
    "Y": 181.19,
    "V": 117.15,
}


# Kyte-Doolittle hydrophobicity
AA_HYDROPHOBICITY = {
    "A": 1.8,
    "R": -4.5,
    "N": -3.5,
    "D": -3.5,
    "C": 2.5,
    "Q": -3.5,
    "E": -3.5,
    "G": -0.4,
    "H": -3.2,
    "I": 4.5,
    "L": 3.8,
    "K": -3.9,
    "M": 1.9,
    "F": 2.8,
    "P": -1.6,
    "S": -0.8,
    "T": -0.7,
    "W": -0.9,
    "Y": -1.3,
    "V": 4.2,
}


# Approximate residue charge at physiological pH
AA_CHARGE = {
    "A": 0,
    "R": 1,
    "N": 0,
    "D": -1,
    "C": 0,
    "E": -1,
    "Q": 0,
    "G": 0,
    "H": 0,
    "I": 0,
    "L": 0,
    "K": 1,
    "M": 0,
    "F": 0,
    "P": 0,
    "S": 0,
    "T": 0,
    "W": 0,
    "Y": 0,
    "V": 0,
}


AA_POLARITY = {
    "A": 0,
    "R": 1,
    "N": 1,
    "D": 1,
    "C": 0,
    "E": 1,
    "Q": 1,
    "G": 0,
    "H": 1,
    "I": 0,
    "L": 0,
    "K": 1,
    "M": 0,
    "F": 0,
    "P": 0,
    "S": 1,
    "T": 1,
    "W": 0,
    "Y": 1,
    "V": 0,
}


AA_AROMATIC = {
    aa: int(
        aa in {
            "F",
            "W",
            "Y",
        }
    )
    for aa in AA_MOLECULAR_WEIGHT
}


AA_SPECIAL = {
    aa: int(
        aa in {
            "G",
            "P",
            "C",
        }
    )
    for aa in AA_MOLECULAR_WEIGHT
}


# ============================================================
# Nucleotide substitution properties
# ============================================================

PURINES = {
    "A",
    "G",
}

PYRIMIDINES = {
    "C",
    "T",
}


def is_transition(
    reference: str,
    alternate: str,
) -> int:
    """
    A<->G or C<->T.
    """

    pair = {
        str(reference).upper(),
        str(alternate).upper(),
    }

    if pair == {"A", "G"}:
        return 1

    if pair == {"C", "T"}:
        return 1

    return 0


def is_transversion(
    reference: str,
    alternate: str,
) -> int:
    """
    Purine <-> pyrimidine substitution.
    """

    ref = str(
        reference
    ).upper()

    alt = str(
        alternate
    ).upper()

    if (
        ref in PURINES
        and alt in PYRIMIDINES
    ):
        return 1

    if (
        ref in PYRIMIDINES
        and alt in PURINES
    ):
        return 1

    return 0


# ============================================================
# Feature engineering
# ============================================================

def create_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    dataframe = dataframe.copy()

    dataframe[
        "reference_aa"
    ] = (
        dataframe[
            "reference_aa"
        ]
        .astype(str)
        .str.upper()
    )

    dataframe[
        "alternate_aa"
    ] = (
        dataframe[
            "alternate_aa"
        ]
        .astype(str)
        .str.upper()
    )

    # --------------------------------------------------------
    # Reference amino-acid properties
    # --------------------------------------------------------

    dataframe[
        "ref_molecular_weight"
    ] = dataframe[
        "reference_aa"
    ].map(
        AA_MOLECULAR_WEIGHT
    )

    dataframe[
        "ref_hydrophobicity"
    ] = dataframe[
        "reference_aa"
    ].map(
        AA_HYDROPHOBICITY
    )

    dataframe[
        "ref_charge"
    ] = dataframe[
        "reference_aa"
    ].map(
        AA_CHARGE
    )

    dataframe[
        "ref_polar"
    ] = dataframe[
        "reference_aa"
    ].map(
        AA_POLARITY
    )

    dataframe[
        "ref_aromatic"
    ] = dataframe[
        "reference_aa"
    ].map(
        AA_AROMATIC
    )

    dataframe[
        "ref_special"
    ] = dataframe[
        "reference_aa"
    ].map(
        AA_SPECIAL
    )

    # --------------------------------------------------------
    # Alternate amino-acid properties
    # --------------------------------------------------------

    dataframe[
        "alt_molecular_weight"
    ] = dataframe[
        "alternate_aa"
    ].map(
        AA_MOLECULAR_WEIGHT
    )

    dataframe[
        "alt_hydrophobicity"
    ] = dataframe[
        "alternate_aa"
    ].map(
        AA_HYDROPHOBICITY
    )

    dataframe[
        "alt_charge"
    ] = dataframe[
        "alternate_aa"
    ].map(
        AA_CHARGE
    )

    dataframe[
        "alt_polar"
    ] = dataframe[
        "alternate_aa"
    ].map(
        AA_POLARITY
    )

    dataframe[
        "alt_aromatic"
    ] = dataframe[
        "alternate_aa"
    ].map(
        AA_AROMATIC
    )

    dataframe[
        "alt_special"
    ] = dataframe[
        "alternate_aa"
    ].map(
        AA_SPECIAL
    )

    # --------------------------------------------------------
    # Property changes caused by mutation
    # --------------------------------------------------------

    dataframe[
        "delta_molecular_weight"
    ] = (
        dataframe[
            "alt_molecular_weight"
        ]
        - dataframe[
            "ref_molecular_weight"
        ]
    )

    dataframe[
        "abs_delta_molecular_weight"
    ] = dataframe[
        "delta_molecular_weight"
    ].abs()

    dataframe[
        "delta_hydrophobicity"
    ] = (
        dataframe[
            "alt_hydrophobicity"
        ]
        - dataframe[
            "ref_hydrophobicity"
        ]
    )

    dataframe[
        "abs_delta_hydrophobicity"
    ] = dataframe[
        "delta_hydrophobicity"
    ].abs()

    dataframe[
        "delta_charge"
    ] = (
        dataframe[
            "alt_charge"
        ]
        - dataframe[
            "ref_charge"
        ]
    )

    dataframe[
        "charge_changed"
    ] = (
        dataframe[
            "ref_charge"
        ]
        != dataframe[
            "alt_charge"
        ]
    ).astype(
        "int8"
    )

    dataframe[
        "polarity_changed"
    ] = (
        dataframe[
            "ref_polar"
        ]
        != dataframe[
            "alt_polar"
        ]
    ).astype(
        "int8"
    )

    dataframe[
        "aromaticity_changed"
    ] = (
        dataframe[
            "ref_aromatic"
        ]
        != dataframe[
            "alt_aromatic"
        ]
    ).astype(
        "int8"
    )

    dataframe[
        "special_residue_changed"
    ] = (
        dataframe[
            "ref_special"
        ]
        != dataframe[
            "alt_special"
        ]
    ).astype(
        "int8"
    )

    # --------------------------------------------------------
    # Genomic nucleotide substitution
    # --------------------------------------------------------

    dataframe[
        "is_transition"
    ] = dataframe.apply(
        lambda row: is_transition(
            row[
                "reference_allele"
            ],
            row[
                "alternate_allele"
            ],
        ),
        axis=1,
    )

    dataframe[
        "is_transversion"
    ] = dataframe.apply(
        lambda row: is_transversion(
            row[
                "reference_allele"
            ],
            row[
                "alternate_allele"
            ],
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Protein-position features
    # --------------------------------------------------------

    dataframe[
        "protein_position"
    ] = pd.to_numeric(
        dataframe[
            "protein_position"
        ],
        errors="coerce",
    )

    dataframe[
        "protein_position_log"
    ] = dataframe[
        "protein_position"
    ].apply(
        lambda value:
            math.log1p(value)
            if pd.notna(value)
            else None
    )

    return dataframe


# ============================================================
# Predictive feature columns
# ============================================================

NUMERIC_FEATURE_COLUMNS = [
    "protein_position",
    "protein_position_log",

    "ref_molecular_weight",
    "alt_molecular_weight",
    "delta_molecular_weight",
    "abs_delta_molecular_weight",

    "ref_hydrophobicity",
    "alt_hydrophobicity",
    "delta_hydrophobicity",
    "abs_delta_hydrophobicity",

    "ref_charge",
    "alt_charge",
    "delta_charge",
    "charge_changed",

    "ref_polar",
    "alt_polar",
    "polarity_changed",

    "ref_aromatic",
    "alt_aromatic",
    "aromaticity_changed",

    "ref_special",
    "alt_special",
    "special_residue_changed",

    "is_transition",
    "is_transversion",
]


CATEGORICAL_FEATURE_COLUMNS = [
    "reference_aa",
    "alternate_aa",
    "reference_allele",
    "alternate_allele",
]


# ============================================================
# Dataset generation
# ============================================================

def build_feature_dataset():

    if not MODELING_DATASET_PATH.exists():

        raise FileNotFoundError(
            "Modeling dataset not found:\n"
            f"{MODELING_DATASET_PATH}"
        )

    print(
        "GeneMirror Feature Engineering"
    )

    print(
        "=" * 60
    )

    print(
        f"\nInput:\n"
        f"{MODELING_DATASET_PATH}"
    )

    dataframe = pd.read_csv(
        MODELING_DATASET_PATH,
        low_memory=False,
    )

    print(
        f"\nRows loaded: "
        f"{len(dataframe):,}"
    )

    dataframe = create_features(
        dataframe
    )

    required_features = (
        NUMERIC_FEATURE_COLUMNS
        + CATEGORICAL_FEATURE_COLUMNS
    )

    missing_features = [
        column
        for column
        in required_features
        if column
        not in dataframe.columns
    ]

    if missing_features:

        raise RuntimeError(
            "Feature columns missing:\n"
            + "\n".join(
                missing_features
            )
        )

    missing_numeric = int(
        dataframe[
            NUMERIC_FEATURE_COLUMNS
        ]
        .isna()
        .sum()
        .sum()
    )

    if missing_numeric != 0:

        raise RuntimeError(
            "Numeric feature engineering "
            f"produced {missing_numeric} "
            "missing values."
        )

    dataframe.to_csv(
        FEATURE_DATASET_PATH,
        index=False,
    )

    print(
        f"\nNumeric features: "
        f"{len(NUMERIC_FEATURE_COLUMNS)}"
    )

    print(
        f"Categorical features: "
        f"{len(CATEGORICAL_FEATURE_COLUMNS)}"
    )

    print(
        f"Total predictive features before encoding: "
        f"{len(required_features)}"
    )

    print(
        f"\nMissing numeric feature values: "
        f"{missing_numeric}"
    )

    print(
        f"\nOutput:\n"
        f"{FEATURE_DATASET_PATH}"
    )

    file_size_mb = (
        FEATURE_DATASET_PATH
        .stat()
        .st_size
        / (1024 * 1024)
    )

    print(
        f"\nOutput file size: "
        f"{file_size_mb:.2f} MB"
    )

    print(
        "\n✅ Sprint 4 feature engineering completed."
    )


if __name__ == "__main__":

    build_feature_dataset()