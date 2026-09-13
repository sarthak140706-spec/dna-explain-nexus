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


def post_json(path, payload):
    response = client.post(
        path,
        json=payload,
    )

    return response, response.json()


def test_health_declares_research_only():
    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["research_only"] is True


def test_prediction_has_research_only_disclaimer():
    response, data = post_json(
        "/api/v1/predict",
        TP53_R248H,
    )

    assert response.status_code == 200

    assert data["research_only"] is True

    disclaimer = data["disclaimer"].lower()

    assert "research" in disclaimer
    assert "clinical" in disclaimer
    assert "diagnosis" in disclaimer
    assert "medical" in disclaimer


def test_xai_has_research_only_disclaimer():
    response, data = post_json(
        "/api/v1/xai",
        TP53_R248H,
    )

    assert response.status_code == 200

    assert data["research_only"] is True

    disclaimer = data["disclaimer"].lower()

    assert "research" in disclaimer
    assert "clinical" in disclaimer


def test_protein_context_has_research_only_disclaimer():
    response, data = post_json(
        "/api/v1/protein-context",
        TP53_R248H,
    )

    assert response.status_code == 200

    assert data["research_only"] is True

    disclaimer = data["disclaimer"].lower()

    assert "research" in disclaimer
    assert "clinical" in disclaimer
    assert "medical" in disclaimer


def test_scientist_has_research_only_disclaimer():
    response, data = post_json(
        "/api/v1/scientist",
        TP53_R248H,
    )

    assert response.status_code == 200

    assert data["research_only"] is True

    disclaimer = data["disclaimer"].lower()

    assert "research" in disclaimer
    assert "clinical" in disclaimer


def test_unified_analysis_research_only_everywhere():
    response, data = post_json(
        "/api/v1/analysis",
        TP53_R248H,
    )

    assert response.status_code == 200

    assert data["research_only"] is True

    assert (
        data["validation"]["research_only"]
        is True
    )

    assert (
        data["xai"]["research_only"]
        is True
    )

    assert (
        data["protein_context"][
            "research_only"
        ]
        is True
    )

    assert (
        data["scientist"][
            "research_only"
        ]
        is True
    )


def test_raw_prediction_does_not_claim_clinical_probability():
    response, data = post_json(
        "/api/v1/predict",
        TP53_R248H,
    )

    assert response.status_code == 200

    prediction = data["prediction"]

    interpretation = prediction[
        "score_interpretation"
    ].lower()

    assert "uncalibrated" in interpretation
    assert "not" in interpretation
    assert "clinical" in interpretation


def test_prediction_target_is_described_as_proxy():
    response, data = post_json(
        "/api/v1/predict",
        TP53_R248H,
    )

    assert response.status_code == 200

    target = data["prediction"][
        "target_interpretation"
    ].lower()

    assert "proxy" in target
    assert "clinvar" in target


def test_protein_context_does_not_claim_pathogenicity():
    response, data = post_json(
        "/api/v1/protein-context",
        TP53_R248H,
    )

    assert response.status_code == 200

    interpretation = data[
        "interpretation"
    ].lower()

    assert "does not independently establish" in interpretation
    assert "pathogenicity" in interpretation
    assert "clinical significance" in interpretation


def test_scientist_is_grounded():
    response, data = post_json(
        "/api/v1/scientist",
        TP53_R248H,
    )

    assert response.status_code == 200

    assert data["scientist_name"] == "GeneMirror Scientist"

    assert len(
        data["grounded_facts"]
    ) > 0

    execution = data["execution"]

    assert isinstance(
        execution["used_llm_response"],
        bool,
    )

    assert isinstance(
        execution["fallback_used"],
        bool,
    )


def test_scientist_contains_limitations_section():
    response, data = post_json(
        "/api/v1/scientist",
        TP53_R248H,
    )

    assert response.status_code == 200

    sections = data["sections"]

    assert "limitations" in sections

    assert sections[
        "limitations"
    ].strip()


def test_invalid_reference_amino_acid_is_rejected():
    invalid_variant = {
        **TP53_R248H,
        "reference_amino_acid": "A",
    }

    response, data = post_json(
        "/api/v1/analysis",
        invalid_variant,
    )

    assert response.status_code >= 400

    assert "detail" in data


def test_invalid_same_reference_and_alternate_dna_is_rejected():
    invalid_variant = {
        **TP53_R248H,
        "alternate_allele": "G",
    }

    response, data = post_json(
        "/api/v1/variants/validate",
        invalid_variant,
    )

    assert response.status_code >= 400

    assert "detail" in data


def test_invalid_amino_acid_symbol_is_rejected():
    invalid_variant = {
        **TP53_R248H,
        "alternate_amino_acid": "Z",
    }

    response, data = post_json(
        "/api/v1/variants/validate",
        invalid_variant,
    )

    assert response.status_code >= 400

    assert "detail" in data