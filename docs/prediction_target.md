# GeneMirror AI — Prediction Target Definition

## Purpose

This document defines what the GeneMirror AI machine learning system will predict.

The purpose of this step is to keep the prediction target scientifically consistent before dataset preparation and model development begin.

---

## Primary Prediction Target

GeneMirror AI Version 1 will predict:

> The computationally estimated impact of a missense genetic variant on protein function.

The system will not predict a medical diagnosis.

The prediction represents a computational variant-effect estimate only.

---

## Supported Prediction Type

Version 1 will focus on:

- Single Nucleotide Variants (SNVs)
- Missense variants
- Amino-acid substitutions

Example:

Gene:

TP53

DNA Change:

c.743G>A

Protein Change:

p.Arg248His

---

## Model Output

The machine learning system will generate three main outputs:

1. Variant Effect Score
2. Impact Class
3. Model Confidence

These values must be treated separately.

---

# 1. Variant Effect Score

The Variant Effect Score is a numerical value representing the model's predicted effect of the variant.

Planned normalized range:

0.00 to 1.00

Example:

Variant Effect Score:

0.87

A higher score represents a stronger predicted functional impact.

A lower score represents a weaker predicted functional impact.

The exact score calibration will be decided after model training and validation.

---

# 2. Impact Class

The user-facing prediction will contain one of three impact classes:

- LOW
- MODERATE
- HIGH

These labels will make the prediction easier to understand in the GeneMirror AI interface.

---

## LOW Impact

LOW represents a variant that the model predicts is less likely to strongly alter protein function.

Typical interpretation:

- Limited predicted functional disruption
- Lower model effect score
- Features indicate relatively weak impact

Important:

LOW does not mean harmless.

It only means lower predicted impact according to the computational model.

---

## MODERATE Impact

MODERATE represents a variant with an intermediate predicted effect.

Typical interpretation:

- Some features indicate possible functional alteration
- Evidence is not strongly concentrated toward either low or high impact
- The variant may influence protein behavior to some degree

MODERATE should not be interpreted as a clinical diagnosis.

---

## HIGH Impact

HIGH represents a variant predicted to have a comparatively strong effect on protein function.

Typical interpretation:

- Strong predictive features
- High conservation may be present
- Important protein context may be affected
- Significant amino-acid substitution properties may be present

Important:

HIGH does not automatically mean disease-causing.

It means the model predicts a high computational impact.

---

# Dataset Label Mapping

The model's internal training labels will come from curated public genomic datasets.

GeneMirror AI will not manually assign biological labels without supporting data.

The mapping process will follow this principle:

Curated Dataset Labels
↓
Standardized Internal Labels
↓
Machine Learning Target
↓
GeneMirror User-Facing Classes

---

## Important Rule

The LOW, MODERATE, and HIGH classes must not be assigned using arbitrary numerical thresholds before the dataset is analyzed.

For example, we will not immediately assume:

0.00 - 0.33 = LOW

0.34 - 0.66 = MODERATE

0.67 - 1.00 = HIGH

unless model calibration and validation later justify such thresholds.

The final thresholding method will be determined during the machine learning and validation stages.

---

# Model Confidence

Model Confidence represents how reliable the model considers its prediction.

Example:

Impact Score:

0.87

Impact Class:

HIGH

Confidence:

84%

The Impact Score and Confidence must remain separate values.

A high impact score does not automatically imply high confidence.

---

## Confidence Sources

The final confidence calculation may consider:

- Model probability
- Calibration quality
- Agreement between models
- Feature completeness
- Input data quality
- Prediction stability

The exact confidence method will be defined during Sprint 5.

---

# Explainability Target

For every prediction, GeneMirror AI should also explain the major contributing factors.

Possible feature groups include:

- Evolutionary conservation
- Amino-acid substitution properties
- Protein region context
- Sequence context
- Physicochemical differences
- Structural annotations when available

Example:

Prediction:

HIGH

Variant Effect Score:

0.87

Confidence:

84%

Top Contributing Features:

Evolutionary Conservation — 38%

Protein Region Context — 27%

Amino Acid Properties — 20%

Sequence Context — 15%

---

# Output Contract

A future GeneMirror AI prediction should conceptually follow this structure:

{
  "gene": "TP53",
  "dna_change": "c.743G>A",
  "protein_change": "p.Arg248His",
  "effect_score": 0.87,
  "impact_class": "HIGH",
  "confidence": 0.84,
  "prediction_type": "computational_variant_effect"
}

Additional XAI and protein-context information will be attached in later sprints.

---

# Interpretation Rules

GeneMirror AI predictions must always follow these rules:

- LOW does not mean safe
- HIGH does not mean disease-causing
- MODERATE does not mean uncertain diagnosis
- Model confidence is not clinical confidence
- Predictions are computational estimates
- Predictions are for research and educational purposes

---

# Final Version 1 Prediction Definition

Input:

Curated missense variant

Prediction:

Computational effect on protein function

Outputs:

- Variant Effect Score
- LOW / MODERATE / HIGH Impact Class
- Model Confidence
- Explainable Feature Contributions

The exact dataset-to-label mapping and numerical class thresholds will be finalized only after the training dataset has been selected and analyzed.