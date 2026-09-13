from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


VALID_VARIANT = {
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


def test_missing_gene_symbol():
    payload = {
        key: value
        for key, value in VALID_VARIANT.items()
        if key != "gene_symbol"
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code == 422


def test_missing_protein_position():
    payload = {
        key: value
        for key, value in VALID_VARIANT.items()
        if key != "protein_position"
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code == 422


def test_zero_protein_position():
    payload = {
        **VALID_VARIANT,
        "protein_position": 0,
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_negative_protein_position():
    payload = {
        **VALID_VARIANT,
        "protein_position": -5,
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_zero_genomic_position():
    payload = {
        **VALID_VARIANT,
        "position": 0,
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_negative_genomic_position():
    payload = {
        **VALID_VARIANT,
        "position": -100,
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_invalid_chromosome():
    payload = {
        **VALID_VARIANT,
        "chromosome": "99",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_mitochondrial_chromosome_rejected():
    payload = {
        **VALID_VARIANT,
        "chromosome": "MT",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_invalid_reference_nucleotide():
    payload = {
        **VALID_VARIANT,
        "reference_allele": "N",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_invalid_alternate_nucleotide():
    payload = {
        **VALID_VARIANT,
        "alternate_allele": "R",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_same_reference_and_alternate_nucleotide():
    payload = {
        **VALID_VARIANT,
        "alternate_allele": "G",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_invalid_reference_amino_acid_symbol():
    payload = {
        **VALID_VARIANT,
        "reference_amino_acid": "Z",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_invalid_alternate_amino_acid_symbol():
    payload = {
        **VALID_VARIANT,
        "alternate_amino_acid": "B",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_same_reference_and_alternate_amino_acid():
    payload = {
        **VALID_VARIANT,
        "alternate_amino_acid": "R",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_wrong_reference_amino_acid_fails_unified_analysis():
    payload = {
        **VALID_VARIANT,
        "reference_amino_acid": "A",
    }

    response = client.post(
        "/api/v1/analysis",
        json=payload,
    )

    assert response.status_code >= 400

    data = response.json()

    assert "detail" in data


def test_impossible_large_protein_position():
    payload = {
        **VALID_VARIANT,
        "protein_position": 999999,
    }

    response = client.post(
        "/api/v1/protein-context",
        json=payload,
    )

    assert response.status_code >= 400


def test_empty_json_request():
    response = client.post(
        "/api/v1/variants/validate",
        json={},
    )

    assert response.status_code == 422


def test_no_json_body():
    response = client.post(
        "/api/v1/variants/validate",
    )

    assert response.status_code == 422


def test_string_used_for_numeric_position():
    payload = {
        **VALID_VARIANT,
        "position": "not-a-number",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code == 422


def test_string_used_for_protein_position():
    payload = {
        **VALID_VARIANT,
        "protein_position": "abc",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code == 422


def test_empty_gene_symbol():
    payload = {
        **VALID_VARIANT,
        "gene_symbol": "",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400


def test_unknown_gene_unified_analysis_fails_safely():
    payload = {
        **VALID_VARIANT,
        "gene_symbol": "NOTAREALGENE",
    }

    response = client.post(
        "/api/v1/analysis",
        json=payload,
    )

    assert response.status_code >= 400


def test_wrong_genomic_coordinates_do_not_silently_succeed():
    payload = {
        **VALID_VARIANT,
        "position": 1,
    }

    response = client.post(
        "/api/v1/analysis",
        json=payload,
    )

    assert response.status_code >= 400


def test_invalid_request_never_returns_success_true():
    payload = {
        **VALID_VARIANT,
        "reference_allele": "X",
    }

    response = client.post(
        "/api/v1/variants/validate",
        json=payload,
    )

    assert response.status_code >= 400

    data = response.json()

    if "success" in data:
        assert data["success"] is not True