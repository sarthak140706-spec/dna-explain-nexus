from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


TP53_R248H = {
    "gene_symbol": "TP53",
    "chromosome": "17",
    "position": 7674220,
    "reference_allele": "G",
    "alternate_allele": "A",
    "protein_position": 248,
    "reference_amino_acid": "R",
    "alternate_amino_acid": "H",
    "dna_change": "c.743G>A",
    "protein_change": "p.Arg248His",
}


def get_json(path, payload):
    response = client.post(
        path,
        json=payload,
    )

    assert response.status_code == 200

    return response.json()


def test_variant_identity_consistency():
    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    variant = analysis["variant"]

    assert variant["gene_symbol"] == "TP53"
    assert variant["chromosome"] == "17"
    assert variant["position"] == 7674220
    assert variant["reference_allele"] == "G"
    assert variant["alternate_allele"] == "A"

    assert variant["protein_position"] == 248
    assert variant["reference_amino_acid"] == "R"
    assert variant["alternate_amino_acid"] == "H"

    assert variant["dna_change"] == "c.743G>A"
    assert variant["protein_change"] == "p.Arg248His"


def test_raw_prediction_matches_unified_analysis():
    prediction_response = get_json(
        "/api/v1/predict",
        TP53_R248H,
    )

    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    raw_prediction = prediction_response[
        "prediction"
    ]

    unified_prediction = analysis[
        "prediction"
    ]

    assert (
        raw_prediction["raw_model_score"]
        == unified_prediction[
            "raw_model_score"
        ]
    )

    assert (
        raw_prediction["predicted_class"]
        == unified_prediction[
            "predicted_class"
        ]
    )

    assert (
        raw_prediction[
            "predicted_class_name"
        ]
        == unified_prediction[
            "predicted_class_name"
        ]
    )

    assert (
        raw_prediction["model_name"]
        == unified_prediction[
            "model_name"
        ]
    )

    assert (
        raw_prediction["model_version"]
        == unified_prediction[
            "model_version"
        ]
    )


def test_xai_matches_unified_prediction():
    xai_response = get_json(
        "/api/v1/xai",
        TP53_R248H,
    )

    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    xai_result = xai_response[
        "result"
    ]

    unified_prediction = analysis[
        "prediction"
    ]

    assert (
        xai_result["raw_model_score"]
        == unified_prediction[
            "raw_model_score"
        ]
    )

    assert (
        xai_result[
            "calibrated_probability"
        ]
        == unified_prediction[
            "calibrated_probability"
        ]
    )

    assert (
        xai_result["confidence_score"]
        == unified_prediction[
            "confidence_score"
        ]
    )

    assert (
        xai_result["uncertainty_score"]
        == unified_prediction[
            "uncertainty_score"
        ]
    )

    assert (
        xai_result["confidence_band"]
        == unified_prediction[
            "confidence_band"
        ]
    )

    assert (
        xai_result["impact_class"]
        == unified_prediction[
            "impact_class"
        ]
    )


def test_confidence_uncertainty_relationship():
    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    prediction = analysis["prediction"]

    confidence = prediction[
        "confidence_score"
    ]

    uncertainty = prediction[
        "uncertainty_score"
    ]

    assert 0.0 <= confidence <= 1.0
    assert 0.0 <= uncertainty <= 1.0

    assert abs(
        confidence
        + uncertainty
        - 1.0
    ) < 1e-9


def test_tp53_expected_reference_values():
    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    prediction = analysis["prediction"]

    assert abs(
        prediction["raw_model_score"]
        - 0.3944095695196884
    ) < 1e-12

    assert abs(
        prediction[
            "calibrated_probability"
        ]
        - 0.22283813747228381
    ) < 1e-12

    assert abs(
        prediction["confidence_score"]
        - 0.2346838982173589
    ) < 1e-12

    assert abs(
        prediction["uncertainty_score"]
        - 0.7653161017826411
    ) < 1e-12

    assert (
        prediction["confidence_band"]
        == "LOW"
    )

    assert (
        prediction["impact_class"]
        == "MODERATE"
    )


def test_protein_context_matches_variant():
    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    protein_context = analysis[
        "protein_context"
    ]

    protein = protein_context[
        "protein"
    ]

    marker = protein_context[
        "variant_marker"
    ]

    assert protein["gene_symbol"] == "TP53"
    assert protein["accession"] == "P04637"
    assert protein["sequence_length"] == 393

    assert marker["position"] == 248
    assert marker["reference_amino_acid"] == "R"
    assert marker["alternate_amino_acid"] == "H"
    assert marker["label"] == "R248H"


def test_sequence_context_reference_matches():
    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    sequence_context = analysis[
        "protein_context"
    ]["sequence_context"]

    assert (
        sequence_context[
            "protein_position"
        ]
        == 248
    )

    assert (
        sequence_context[
            "reference_amino_acid"
        ]
        == "R"
    )

    assert (
        sequence_context[
            "sequence_reference_amino_acid"
        ]
        == "R"
    )

    assert (
        sequence_context[
            "position_matches_reference"
        ]
        is True
    )

    assert (
        sequence_context[
            "window_start"
        ]
        == 238
    )

    assert (
        sequence_context[
            "window_end"
        ]
        == 258
    )

    assert (
        sequence_context[
            "sequence_window"
        ]
        == "CNSSCMGGMNRRPILTIITLE"
    )

    assert (
        sequence_context[
            "variant_index_in_window"
        ]
        == 10
    )

    assert (
        sequence_context[
            "protein_length"
        ]
        == 393
    )


def test_xai_feature_count_consistency():
    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    xai = analysis["xai"]

    explanation = xai[
        "explanation"
    ]

    assert (
        explanation["feature_count"]
        == 28
    )

    assert (
        len(
            explanation["top_features"]
        )
        <= explanation[
            "feature_count"
        ]
    )

    assert (
        explanation[
            "test_set_used"
        ]
        is False
    )


def test_scientist_is_grounded_to_same_variant():
    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    scientist = analysis[
        "scientist"
    ]

    variant = scientist[
        "variant"
    ]

    assert variant["gene_symbol"] == "TP53"
    assert variant["protein_position"] == 248
    assert variant["reference_amino_acid"] == "R"
    assert variant["alternate_amino_acid"] == "H"

    assert (
        scientist["scientist_name"]
        == "GeneMirror Scientist"
    )

    assert scientist[
        "research_only"
    ] is True

    assert (
        len(
            scientist["grounded_facts"]
        )
        > 0
    )


def test_research_only_consistency():
    analysis = get_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    assert (
        analysis["research_only"]
        is True
    )

    assert (
        analysis["validation"][
            "research_only"
        ]
        is True
    )

    assert (
        analysis["xai"][
            "research_only"
        ]
        is True
    )

    assert (
        analysis[
            "protein_context"
        ]["research_only"]
        is True
    )

    assert (
        analysis["scientist"][
            "research_only"
        ]
        is True
    )