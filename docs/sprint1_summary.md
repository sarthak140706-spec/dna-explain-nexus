# GeneMirror AI — Sprint 1 Summary

## Sprint

Sprint 1 — Scientific Scope, Dataset & Variant Definition

## Status

COMPLETED AND FROZEN

---

# Sprint Objective

The objective of Sprint 1 was to define the scientific foundation of GeneMirror AI before implementing data processing, machine learning, APIs, or backend integration.

Sprint 1 establishes:

- What GeneMirror predicts
- Which variants are initially supported
- Which genes are used for the competition demonstration
- Which public genomic resources will be used
- How predictions should be interpreted
- Scientific and safety boundaries

---

# 1. Scientific Scope

GeneMirror AI is defined as:

> An explainable computational platform for predicting and visualizing the effects of genetic variants.

Version 1 focuses on:

- Human genetic variants
- Single nucleotide variants
- Missense variants
- Protein-changing amino-acid substitutions

GeneMirror is intended for:

- Research
- Education
- Computational genomics
- Explainable AI demonstrations

It is not a clinical diagnostic or gene-editing system.

---

# 2. Prediction Task

The primary machine learning task is:

> Predict the computationally estimated functional impact of a missense genetic variant.

The planned prediction outputs are:

- Variant Effect Score
- Impact Class
- Model Confidence
- Explainable feature contributions

---

# 3. User-Facing Impact Classes

GeneMirror will use:

- LOW
- MODERATE
- HIGH

These are computational impact labels.

They must not be presented as direct clinical classifications.

The final numerical boundaries between these classes will not be assigned arbitrarily.

Thresholds will be determined after dataset analysis, model training, calibration, and validation.

---

# 4. Prediction Score vs Confidence

GeneMirror will keep these concepts separate:

Variant Effect Score
!=
Model Confidence

The effect score represents the predicted functional impact.

Confidence represents the reliability of the model prediction under the available model and data assumptions.

The confidence methodology will be finalized during Sprint 5.

---

# 5. Initial Demo Genes

The competition demonstration will initially showcase:

- TP53
- BRCA1
- CFTR
- HBB
- APOE
- MTHFR

TP53 will initially act as the flagship demonstration gene.

The backend and machine learning architecture must not be hard-coded to these six genes.

Additional genes may be included in the training dataset.

---

# 6. Supported Variant Type

GeneMirror Version 1 supports:

Missense Single Nucleotide Variants

The initial prediction model will not attempt to support:

- Insertions
- Deletions
- Frameshift variants
- Splice variants
- Copy number variants
- Structural variants
- Gene fusions

Unsupported variants should be rejected or clearly identified rather than forced through the prediction model.

---

# 7. Dataset Strategy

Primary variant source:

NCBI ClinVar

Primary purposes:

- Variant records
- Source classifications
- Variant identifiers
- Review status
- Evidence/conflict metadata

Supporting annotation resources may include:

Ensembl
- Sequence information
- Transcript mapping
- Variant consequences

UniProt
- Protein information
- Functional regions
- Protein context

Appropriate NCBI sequence resources may also be used for reference sequence verification and identifier mapping.

---

# 8. Dataset Processing Principle

The required data workflow is:

Public Genomic Data
        |
        v
Raw Dataset
        |
        v
Validation
        |
        v
Filtering
        |
        v
Normalization
        |
        v
Annotation
        |
        v
Feature Engineering
        |
        v
Processed Dataset
        |
        v
Machine Learning

Frontend mock data must never be used as scientific training ground truth.

---

# 9. Dataset Layers

The planned data structure is:

data/
|
|-- raw/
|
|-- interim/
|
|-- processed/
|
`-- demo/

Raw downloaded datasets should remain unchanged.

Processed datasets should be versioned.

Initial planned output:

data/processed/genemirror_variants_v1.csv

---

# 10. Label Strategy

GeneMirror must keep the following concepts separate:

Source Classification
        |
        v
Training Target
        |
        v
Machine Learning Prediction
        |
        v
GeneMirror Impact Class

Source classifications will be cleaned and analyzed before defining the final machine learning target.

Conflicting or insufficiently supported source records must be handled explicitly.

No arbitrary LOW / MODERATE / HIGH mapping will be introduced before the real dataset is inspected.

---

# 11. Explainability Requirement

Every production prediction should eventually support an explanation.

Potential explanation groups include:

- Evolutionary conservation
- Amino-acid properties
- Sequence context
- Protein context
- Physicochemical changes
- Structural annotations when available

The final explainability implementation will depend on the model selected during later sprints.

---

# 12. AI Scientist Principle

The GeneMirror Scientist will explain structured backend results.

Architecture:

Scientific Engines
        |
        v
Structured Analysis
        |
        v
AI Scientist
        |
        v
Natural-Language Explanation

The language model must not become the source of the scientific prediction.

It should explain results produced by the validated computational pipeline.

---

# 13. Safety Boundary

GeneMirror may:

- Analyze existing variants
- Compare reference and alternate sequences
- Generate computational predictions
- Explain model predictions
- Display protein context
- Generate educational summaries

GeneMirror must not:

- Diagnose patients
- Recommend medical treatment
- Provide patient-specific medical advice
- Design CRISPR guides
- Design gene-editing constructs
- Provide gene-editing protocols
- Provide wet-lab modification instructions
- Fabricate biological evidence

---

# 14. Required Product Disclaimer

GeneMirror should communicate:

> GeneMirror AI provides computational predictions for research and educational purposes only. It is not a clinical diagnostic system and should not be used for medical decision-making.

---

# 15. Frozen Sprint 1 Decisions

The following decisions are now frozen:

Variant Scope:
Missense SNVs

Primary Dataset:
ClinVar

Sequence / Consequence Annotation:
Ensembl and/or appropriate NCBI resources

Protein Annotation:
UniProt

Demo Genes:
TP53, BRCA1, CFTR, HBB, APOE, MTHFR

Primary Prediction:
Computational variant-effect prediction

Product Classes:
LOW, MODERATE, HIGH

Primary Competition Domain:
Explainable AI (XAI)

Secondary Competition Domain:
Generative AI & LLM Applications

Frontend:
Current Lovable React frontend remains the V1 frontend baseline.

Backend:
Not implemented during Sprint 1.

---

# 16. Conditions for Changing Frozen Decisions

A frozen Sprint 1 decision should only be changed if later implementation reveals a genuine scientific or technical problem.

Examples include:

- Insufficient training data
- Unusable source fields
- Severe class imbalance
- Annotation incompatibility
- Data leakage
- Poor model validity
- Unsupported transcript mappings

Changes must be documented rather than silently introduced.

---

# Sprint 1 Completion

Sprint 1 is complete when all required documentation files exist and contain the agreed definitions.

Required files:

docs/scientific_scope.md
docs/prediction_target.md
docs/demo_variants.md
docs/dataset_plan.md
docs/safety_boundaries.md
docs/sprint1_summary.md

Status:

SPRINT 1 COMPLETE

Next:

Sprint 2 — Genomic Data Ingestion & Validation Pipeline