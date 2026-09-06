# GeneMirror AI — Scientific and Safety Boundaries

## Purpose

This document defines the scientific, ethical, and product boundaries for GeneMirror AI Version 1.

These boundaries are fixed to ensure that the platform remains a computational analysis and educational system rather than a clinical diagnostic or gene-editing tool.

---

# Product Positioning

GeneMirror AI is:

> An explainable computational platform for analyzing and predicting the effects of curated genetic variants.

GeneMirror AI is intended for:

- Research
- Education
- Demonstration
- Computational genomics learning
- Explainable AI experimentation
- Variant analysis workflows

GeneMirror AI is not intended for:

- Clinical diagnosis
- Medical treatment decisions
- Patient-specific recommendations
- Gene-editing design
- Wet-lab experimentation
- Therapeutic decision-making

---

# Core Scientific Boundary

GeneMirror AI will analyze existing, curated, known, or hypothetical genetic variants computationally.

The platform may:

- Read variant information
- Compare reference and alternate alleles
- Analyze sequence context
- Identify protein-level consequences
- Generate machine learning predictions
- Explain model predictions
- Display protein context
- Produce plain-language summaries

The platform will not provide instructions for modifying DNA in a real biological system.

---

# Prohibited Gene-Editing Functionality

GeneMirror AI Version 1 will not include:

- CRISPR guide RNA design
- Gene-editing construct design
- DNA editing protocols
- Delivery-vector design
- Plasmid design
- Primer design for genetic modification
- Experimental optimization for gene editing
- Mutation induction procedures
- Wet-lab gene-editing workflows

The platform is strictly computational and analytical.

---

# Clinical Boundary

GeneMirror AI predictions must never be presented as a diagnosis.

The system must not say:

- "This patient has a disease"
- "This mutation will cause disease"
- "This person should receive treatment"
- "This variant proves a medical condition"
- "This treatment should be taken"

Instead, the system should use language such as:

- Predicted impact
- Computational estimate
- Model prediction
- Predicted functional effect
- Model confidence
- Variant-effect score

---

# Required Disclaimer

The following disclaimer should remain visible in the GeneMirror interface:

> GeneMirror AI provides computational predictions for research and educational purposes only. It is not a clinical diagnostic system and should not be used for medical decision-making.

The exact visual placement may change during frontend development, but the meaning must remain unchanged.

---

# Prediction Language Rules

Preferred wording:

- "Predicted high impact"
- "The model estimates"
- "The model suggests"
- "Computational analysis indicates"
- "Predicted functional effect"
- "Model confidence"

Avoid wording such as:

- "Definitely pathogenic"
- "Guaranteed disease-causing"
- "This mutation causes disease"
- "Safe mutation"
- "Harmless mutation"
- "Clinical confidence"
- "Medical certainty"

---

# Impact Class Interpretation

GeneMirror uses:

- LOW
- MODERATE
- HIGH

These are model-facing product labels.

They must not be interpreted as direct clinical categories.

---

## LOW

LOW means:

The computational model predicts a comparatively lower functional effect.

LOW does not mean:

- Safe
- Harmless
- Benign in all contexts
- Medically insignificant

---

## MODERATE

MODERATE means:

The computational model predicts an intermediate functional effect.

MODERATE does not mean:

- Clinically uncertain
- Partially harmful
- Intermediate disease severity

---

## HIGH

HIGH means:

The computational model predicts a comparatively stronger functional effect.

HIGH does not mean:

- Disease-causing
- Pathogenic
- Clinically actionable
- Medically severe

unless such information is explicitly being shown as a separate source classification from a curated database.

---

# Source Classification vs Model Prediction

GeneMirror must keep source information and model output separate.

Example:

ClinVar Source Classification:
Pathogenic

GeneMirror Prediction:
HIGH predicted functional impact

These are related but not identical concepts.

The interface should avoid presenting them as if one proves the other.

---

# Confidence Boundary

Model confidence represents confidence in the machine learning prediction.

It is not:

- Clinical confidence
- Medical certainty
- Diagnostic certainty
- Biological proof

Example:

Confidence: 84%

means:

The computational model has relatively strong confidence in its own prediction under the available data and model assumptions.

---

# AI Scientist Boundary

The GeneMirror Scientist must explain results produced by the backend.

It should not independently invent new biological conclusions.

Correct architecture:

Backend Analysis
        |
        v
Structured Results
        |
        v
GeneMirror Scientist
        |
        v
Natural-Language Explanation

The AI Scientist should remain grounded in:

- Sequence analysis
- Variant information
- Model output
- XAI results
- Protein context
- Source metadata

---

# AI Scientist Must Not

The AI Scientist must not:

- Diagnose a user
- Recommend treatment
- Suggest DNA edits
- Suggest CRISPR edits
- Design biological modifications
- Provide wet-lab instructions
- Invent unsupported biological claims
- Override backend scientific results

---

# Hypothetical Variant Handling

GeneMirror may allow hypothetical variants for educational analysis.

If a variant is hypothetical or not found in the curated source dataset, the interface should clearly indicate this.

Example:

Status:
Hypothetical / Not Curated

The system must not falsely present hypothetical variants as known clinical evidence.

---

# Data Integrity Boundary

The platform must not create fake biological evidence.

Frontend mock values may be used only during UI development.

They must not be displayed as real scientific predictions after backend integration.

Real system results should come from:

- Validated datasets
- Reproducible processing
- Trained models
- Documented annotation pipelines

---

# Reproducibility Requirement

For every real prediction, GeneMirror should aim to retain:

- Variant identifier
- Input features
- Model version
- Dataset version
- Prediction score
- Prediction class
- Confidence
- XAI result
- Source metadata

This makes results traceable and reproducible.

---

# Unsupported Inputs

If the user provides an unsupported variant type, GeneMirror should not force a prediction.

Example unsupported types:

- Large deletions
- Large insertions
- Gene fusions
- Copy number variants
- Structural rearrangements
- Complex variants

Expected behavior:

Unsupported Variant Type

GeneMirror Version 1 currently supports missense single-nucleotide variants only.

---

# Missing Data Handling

If critical information is missing, GeneMirror should return a clear error or incomplete-analysis status.

It must not fabricate missing values.

Examples:

- Missing reference allele
- Missing alternate allele
- Missing protein change
- Missing transcript mapping
- Missing required model features

---

# Scientific Transparency

GeneMirror should communicate that model predictions have limitations.

Possible limitations include:

- Dataset bias
- Missing annotations
- Limited gene representation
- Model uncertainty
- Conflicting source evidence
- Incomplete biological context

These limitations should be documented during final validation.

---

# Version 1 Safety Summary

GeneMirror AI Version 1 is allowed to:

- Analyze curated variants
- Compare reference and alternate sequences
- Predict computational functional impact
- Explain model predictions
- Show protein context
- Summarize scientific results

GeneMirror AI Version 1 is not allowed to:

- Diagnose disease
- Recommend treatment
- Provide patient-specific medical advice
- Design gene edits
- Design CRISPR guides
- Provide experimental gene-editing protocols
- Fabricate biological evidence
- Present model predictions as clinical certainty

---

# Final Safety Principle

GeneMirror AI must remain:

> Computational, explainable, traceable, non-clinical, and non-editing.

Every future sprint must follow this boundary.