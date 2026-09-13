import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


VARIANTS = [
    {
        "gene_symbol": "APOE",
        "chromosome": "19",
        "position": 44908822,
        "reference_allele": "C",
        "alternate_allele": "T",
        "protein_position": 176,
        "reference_amino_acid": "R",
        "alternate_amino_acid": "C",
        "dna_change": "c.526C>T",
        "protein_change": "p.Arg176Cys",
    },
    {
        "gene_symbol": "BRCA1",
        "chromosome": "17",
        "position": 43106478,
        "reference_allele": "A",
        "alternate_allele": "C",
        "protein_position": 64,
        "reference_amino_acid": "C",
        "alternate_amino_acid": "G",
        "dna_change": "c.190T>G",
        "protein_change": "p.Cys64Gly",
    },
    {
        "gene_symbol": "CFTR",
        "chromosome": "7",
        "position": 117530953,
        "reference_allele": "G",
        "alternate_allele": "C",
        "protein_position": 110,
        "reference_amino_acid": "D",
        "alternate_amino_acid": "H",
        "dna_change": "c.328G>C",
        "protein_change": "p.Asp110His",
    },
    {
        "gene_symbol": "HBB",
        "chromosome": "11",
        "position": 5226669,
        "reference_allele": "C",
        "alternate_allele": "G",
        "protein_position": 75,
        "reference_amino_acid": "G",
        "alternate_amino_acid": "R",
        "dna_change": "c.223G>C",
        "protein_change": "p.Gly75Arg",
    },
    {
        "gene_symbol": "MTHFR",
        "chromosome": "1",
        "position": 11801166,
        "reference_allele": "C",
        "alternate_allele": "T",
        "protein_position": 157,
        "reference_amino_acid": "R",
        "alternate_amino_acid": "Q",
        "dna_change": "c.470G>A",
        "protein_change": "p.Arg157Gln",
    },
    {
        "gene_symbol": "TP53",
        "chromosome": "17",
        "position": 7674208,
        "reference_allele": "A",
        "alternate_allele": "G",
        "protein_position": 252,
        "reference_amino_acid": "L",
        "alternate_amino_acid": "P",
        "dna_change": "c.755T>C",
        "protein_change": "p.Leu252Pro",
    },
]


@pytest.mark.parametrize(
    "variant",
    VARIANTS,
    ids=[
        "APOE_R176C",
        "BRCA1_C64G",
        "CFTR_D110H",
        "HBB_G75R",
        "MTHFR_R157Q",
        "TP53_L252P",
    ],
)
def test_multi_gene_variant_validation(variant):
    response = client.post(
        "/api/v1/variants/validate",
        json=variant,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    returned_variant = data["variant"]

    assert (
        returned_variant["gene_symbol"]
        == variant["gene_symbol"]
    )

    assert (
        returned_variant["protein_position"]
        == variant["protein_position"]
    )

    assert (
        returned_variant["reference_amino_acid"]
        == variant["reference_amino_acid"]
    )

    assert (
        returned_variant["alternate_amino_acid"]
        == variant["alternate_amino_acid"]
    )


@pytest.mark.parametrize(
    "variant",
    VARIANTS,
    ids=[
        "APOE_R176C",
        "BRCA1_C64G",
        "CFTR_D110H",
        "HBB_G75R",
        "MTHFR_R157Q",
        "TP53_L252P",
    ],
)
def test_multi_gene_prediction(variant):
    response = client.post(
        "/api/v1/predict",
        json=variant,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    prediction = data["prediction"]

    assert (
        0.0
        <= prediction["raw_model_score"]
        <= 1.0
    )

    assert prediction["predicted_class"] in {
        0,
        1,
    }

    assert prediction[
        "predicted_class_name"
    ] in {
        "benign_like",
        "pathogenic_like",
    }

    assert (
        prediction["model_name"]
        == "HistGradientBoostingClassifier"
    )

    assert (
        prediction["model_version"]
        == "GeneMirror-v1-Sprint4"
    )


@pytest.mark.parametrize(
    "variant",
    VARIANTS,
    ids=[
        "APOE_R176C",
        "BRCA1_C64G",
        "CFTR_D110H",
        "HBB_G75R",
        "MTHFR_R157Q",
        "TP53_L252P",
    ],
)
def test_multi_gene_xai(variant):
    response = client.post(
        "/api/v1/xai",
        json=variant,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    result = data["result"]

    assert (
        0.0
        <= result["raw_model_score"]
        <= 1.0
    )

    assert (
        0.0
        <= result["calibrated_probability"]
        <= 1.0
    )

    assert (
        0.0
        <= result["confidence_score"]
        <= 1.0
    )

    assert (
        0.0
        <= result["uncertainty_score"]
        <= 1.0
    )

    assert result["impact_class"] in {
        "LOW",
        "MODERATE",
        "HIGH",
    }

    assert result["confidence_band"] in {
        "LOW",
        "MODERATE",
        "HIGH",
    }

    explanation = data["explanation"]

    assert explanation["feature_count"] == 28

    assert (
        len(explanation["top_features"])
        > 0
    )


@pytest.mark.parametrize(
    "variant",
    VARIANTS,
    ids=[
        "APOE_R176C",
        "BRCA1_C64G",
        "CFTR_D110H",
        "HBB_G75R",
        "MTHFR_R157Q",
        "TP53_L252P",
    ],
)
def test_multi_gene_protein_context(variant):
    response = client.post(
        "/api/v1/protein-context",
        json=variant,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    protein = data["protein"]
    marker = data["variant_marker"]
    sequence_context = data["sequence_context"]

    assert (
        protein["gene_symbol"]
        == variant["gene_symbol"]
    )

    assert protein["sequence_length"] > 0

    assert (
        marker["position"]
        == variant["protein_position"]
    )

    assert (
        marker["reference_amino_acid"]
        == variant["reference_amino_acid"]
    )

    assert (
        marker["alternate_amino_acid"]
        == variant["alternate_amino_acid"]
    )

    assert (
        sequence_context["protein_position"]
        == variant["protein_position"]
    )

    assert (
        sequence_context[
            "reference_amino_acid"
        ]
        == variant["reference_amino_acid"]
    )

    assert (
        sequence_context[
            "sequence_reference_amino_acid"
        ]
        == variant["reference_amino_acid"]
    )

    assert (
        sequence_context[
            "position_matches_reference"
        ]
        is True
    )


@pytest.mark.parametrize(
    "variant",
    VARIANTS,
    ids=[
        "APOE_R176C",
        "BRCA1_C64G",
        "CFTR_D110H",
        "HBB_G75R",
        "MTHFR_R157Q",
        "TP53_L252P",
    ],
)
def test_multi_gene_unified_analysis(variant):
    response = client.post(
        "/api/v1/analysis",
        json=variant,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    assert (
        data["variant"]["gene_symbol"]
        == variant["gene_symbol"]
    )

    prediction = data["prediction"]

    assert (
        0.0
        <= prediction["raw_model_score"]
        <= 1.0
    )

    assert (
        0.0
        <= prediction["calibrated_probability"]
        <= 1.0
    )

    assert (
        0.0
        <= prediction["confidence_score"]
        <= 1.0
    )

    assert (
        0.0
        <= prediction["uncertainty_score"]
        <= 1.0
    )

    assert prediction["impact_class"] in {
        "LOW",
        "MODERATE",
        "HIGH",
    }

    protein_context = data[
        "protein_context"
    ]

    assert (
        protein_context["protein"]["gene_symbol"]
        == variant["gene_symbol"]
    )

    assert (
        protein_context[
            "variant_marker"
        ]["position"]
        == variant["protein_position"]
    )

    assert (
        protein_context[
            "sequence_context"
        ]["position_matches_reference"]
        is True
    )

    scientist = data["scientist"]

    assert scientist[
        "research_only"
    ] is True

    assert (
        scientist["variant"]["gene_symbol"]
        == variant["gene_symbol"]
    )


@pytest.mark.parametrize(
    "variant",
    VARIANTS,
    ids=[
        "APOE_R176C",
        "BRCA1_C64G",
        "CFTR_D110H",
        "HBB_G75R",
        "MTHFR_R157Q",
        "TP53_L252P",
    ],
)
def test_prediction_xai_consistency_across_genes(
    variant,
):
    prediction_response = client.post(
        "/api/v1/predict",
        json=variant,
    )

    xai_response = client.post(
        "/api/v1/xai",
        json=variant,
    )

    assert prediction_response.status_code == 200
    assert xai_response.status_code == 200

    raw_prediction = prediction_response.json()[
        "prediction"
    ]

    xai_result = xai_response.json()[
        "result"
    ]

    assert (
        raw_prediction["raw_model_score"]
        == xai_result["raw_model_score"]
    )

    assert (
        raw_prediction["predicted_class"]
        == xai_result["predicted_class"]
    )

    assert (
        raw_prediction[
            "predicted_class_name"
        ]
        == xai_result[
            "predicted_class_name"
        ]
    )