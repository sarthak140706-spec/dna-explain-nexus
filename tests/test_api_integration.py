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


def test_health_endpoint():
    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "GeneMirror AI"
    assert data["api_version"] == "v1"
    assert data["research_only"] is True


def test_validate_variant():
    response = client.post(
        "/api/v1/variants/validate",
        json=TP53_R248H,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    assert data["variant"]["gene_symbol"] == "TP53"
    assert data["variant"]["protein_position"] == 248
    assert data["variant"]["reference_amino_acid"] == "R"
    assert data["variant"]["alternate_amino_acid"] == "H"


def test_prediction_endpoint():
    response = client.post(
        "/api/v1/predict",
        json=TP53_R248H,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    prediction = data["prediction"]

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
        0.0
        <= prediction["raw_model_score"]
        <= 1.0
    )

    # /predict is the raw Sprint 4 model endpoint.
    # Calibration and confidence are intentionally
    # added later by the XAI/calibration pipeline.
    assert (
        prediction["calibrated_probability"]
        is None
    )

    assert (
        prediction["confidence_score"]
        is None
    )

    assert (
        prediction["uncertainty_score"]
        is None
    )

    assert (
        prediction["confidence_band"]
        is None
    )

    assert (
        prediction["impact_class"]
        is None
    )

    assert (
        prediction["model_name"]
        == "HistGradientBoostingClassifier"
    )


def test_xai_endpoint():
    response = client.post(
        "/api/v1/xai",
        json=TP53_R248H,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    assert (
        data["variant"]["gene_symbol"]
        == "TP53"
    )

    result = data["result"]
    explanation = data["explanation"]

    assert result["impact_class"] in {
        "LOW",
        "MODERATE",
        "HIGH",
    }

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

    assert (
        result["confidence_band"]
        in {
            "LOW",
            "MODERATE",
            "HIGH",
        }
    )

    assert (
        explanation["feature_count"]
        > 0
    )

    assert (
        len(
            explanation["top_features"]
        )
        > 0
    )

    assert (
        explanation["test_set_used"]
        is False
    )


def test_protein_context_endpoint():
    response = client.post(
        "/api/v1/protein-context",
        json=TP53_R248H,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    assert (
        data["variant"]["gene_symbol"]
        == "TP53"
    )

    protein = data["protein"]

    assert protein["accession"] == "P04637"
    assert protein["gene_symbol"] == "TP53"

    assert (
        protein["protein_name"]
        == "Cellular tumor antigen p53"
    )

    assert (
        protein["organism"]
        == "Homo sapiens"
    )

    assert protein["sequence_length"] == 393
    assert protein["reviewed"] is True
    assert protein["source"] == "UniProtKB"

    marker = data["variant_marker"]

    assert marker["position"] == 248

    assert (
        marker["reference_amino_acid"]
        == "R"
    )

    assert (
        marker["alternate_amino_acid"]
        == "H"
    )

    assert marker["label"] == "R248H"

    assert (
        len(
            data["overlapping_features"]
        )
        > 0
    )

    assert (
        len(
            data["visualization_tracks"]
        )
        > 0
    )


def test_scientist_endpoint():
    response = client.post(
        "/api/v1/scientist",
        json=TP53_R248H,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    assert (
        data["scientist_name"]
        == "GeneMirror Scientist"
    )

    assert (
        data["variant"]["gene_symbol"]
        == "TP53"
    )

    sections = data["sections"]

    assert sections["overview"]
    assert sections["prediction"]
    assert sections["evidence"]
    assert sections["protein_context"]
    assert sections["limitations"]

    execution = data["execution"]

    assert execution["provider_used"]
    assert isinstance(
        execution["used_llm_response"],
        bool,
    )

    assert isinstance(
        execution["fallback_used"],
        bool,
    )


def test_unified_analysis_endpoint():
    response = client.post(
        "/api/v1/analysis",
        json=TP53_R248H,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["research_only"] is True

    assert (
        data["variant"]["gene_symbol"]
        == "TP53"
    )

    prediction = data["prediction"]
    xai = data["xai"]

    assert (
        prediction["impact_class"]
        == xai["result"]["impact_class"]
    )

    assert (
        prediction["raw_model_score"]
        == xai["result"]["raw_model_score"]
    )

    assert (
        prediction[
            "calibrated_probability"
        ]
        == xai["result"][
            "calibrated_probability"
        ]
    )

    assert (
        prediction["confidence_score"]
        == xai["result"][
            "confidence_score"
        ]
    )

    assert (
        prediction["uncertainty_score"]
        == xai["result"][
            "uncertainty_score"
        ]
    )

    assert (
        data[
            "protein_context"
        ]["protein"]["accession"]
        == "P04637"
    )

    assert (
        data["scientist"][
            "scientist_name"
        ]
        == "GeneMirror Scientist"
    )

    assert (
        data["scientist"][
            "research_only"
        ]
        is True
    )


def test_invalid_reference_amino_acid():
    invalid_variant = {
        **TP53_R248H,
        "reference_amino_acid": "A",
    }

    response = client.post(
        "/api/v1/analysis",
        json=invalid_variant,
    )

    assert response.status_code >= 400

    data = response.json()

    assert "detail" in data