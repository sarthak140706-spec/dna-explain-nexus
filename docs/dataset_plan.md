# GeneMirror AI — Dataset Strategy

## Purpose

This document defines the public genomic data sources that will be used by GeneMirror AI Version 1.

The goal is to create a reproducible and scientifically defensible dataset pipeline before machine learning development begins.

GeneMirror AI will not use manually invented biological labels as training ground truth.

---

# Primary Dataset Source

## ClinVar

Primary Source:

NCBI ClinVar

Primary Role:

ClinVar will serve as the main source of curated human genetic variant records and submitted clinical classifications.

GeneMirror will use ClinVar primarily to obtain:

- Gene symbol
- Variant identifiers
- Variant type
- DNA-level change
- Protein-level change where available
- Reference and alternate alleles where available
- Germline classification
- Review status
- Variation ID
- VCV accession
- Evidence-related metadata
- Submission consistency or conflict information

---

# Why ClinVar Is the Primary Source

ClinVar provides structured public information about human genomic variants and their submitted interpretations.

It also reports a review-status system that helps indicate the level of review supporting a classification.

GeneMirror should preserve this information rather than treating all records as having identical evidence quality.

---

# ClinVar Review Status

ClinVar uses review statuses that may include:

- Practice guideline
- Reviewed by expert panel
- Criteria provided, multiple submitters, no conflicts
- Criteria provided, single submitter
- Criteria provided, conflicting classifications
- No assertion criteria provided

GeneMirror will retain the review status as part of each processed variant record.

Review status may later be used for:

- Dataset filtering
- Data quality indicators
- Confidence analysis
- Model evaluation
- Competition-demo transparency

---

# Important ClinVar Rule

ClinVar records may contain agreement or disagreement between submitters.

GeneMirror must not silently treat conflicting records as unquestioned ground truth.

Conflicting or insufficiently supported classifications should be:

- Flagged
- Filtered
- Separated
- Or handled explicitly during dataset preparation

The exact filtering strategy will be finalized during Sprint 2 after examining the downloaded dataset.

---

# Initial Variant Filtering Strategy

GeneMirror Version 1 will initially retain variants that satisfy the following scope:

- Human variants
- Single nucleotide variants
- Missense variants
- Protein-changing substitutions
- Gene symbol is available
- Protein change is available where possible
- Classification information is available
- Variant can be normalized into the GeneMirror schema

The initial competition-demo gene set is:

- TP53
- BRCA1
- CFTR
- HBB
- APOE
- MTHFR

The ML dataset may later contain additional genes if needed to obtain sufficient training data.

The model must not be designed only around these six genes.

---

# Secondary Data Sources

GeneMirror will use additional public resources for annotations that are not reliably available from the primary variant dataset alone.

---

## Ensembl

Primary Role:

Sequence and variant consequence annotation.

Possible uses include:

- Gene identifiers
- Transcript identifiers
- Genomic coordinates
- Reference sequence context
- Variant consequence
- Protein consequence
- Amino-acid position
- Transcript mapping

Ensembl annotations may be used during the sequence-analysis and feature-engineering stages.

---

## UniProt

Primary Role:

Protein-level annotation.

Possible uses include:

- Protein identifiers
- Protein length
- Protein domains
- Functional regions
- Residue annotations
- Protein descriptions
- Other available protein-context annotations

UniProt will primarily support the Protein Context Engine rather than provide the main machine learning target.

---

## NCBI Sequence Resources

Possible Role:

Reference sequence verification and identifier mapping.

These resources may be used when reference genomic or transcript sequence information is required.

---

# Data Source Responsibilities

The intended division of responsibilities is:

ClinVar
    |
    |-- Variant records
    |-- Submitted classifications
    |-- Review status
    |-- Variant identifiers
    |
    v
Core Variant Dataset

Ensembl
    |
    |-- Sequence annotation
    |-- Transcript mapping
    |-- Variant consequence
    |
    v
Sequence Features

UniProt
    |
    |-- Protein annotation
    |-- Protein regions
    |-- Functional context
    |
    v
Protein Features

Combined Data
    |
    v
Processed GeneMirror Dataset

---

# Training Target Strategy

The raw ClinVar classification must not automatically be copied directly into the final GeneMirror LOW, MODERATE, and HIGH classes.

The expected workflow is:

Raw ClinVar Classification
        |
        v
Clean and Normalize Labels
        |
        v
Remove or Separate Unsupported / Conflicting Cases
        |
        v
Define Machine Learning Target
        |
        v
Train and Validate Model
        |
        v
Calibrate Model Output
        |
        v
GeneMirror Impact Classes

The exact label-mapping strategy will be decided only after inspecting the real class distribution.

---

# Avoiding Label Leakage

GeneMirror must not use a feature during training if that feature directly reveals the target classification.

Examples of potential leakage include:

- Clinical significance text used as both input and target
- Pathogenicity labels included inside model features
- Derived fields that directly encode the target
- External prediction scores that duplicate the desired output without justification

Training features must describe the variant itself rather than simply exposing its label.

---

# Candidate Feature Groups

The final feature set will be determined after data inspection.

Potential feature groups include:

## Variant Features

- Reference allele
- Alternate allele
- Nucleotide substitution type
- Position-related information
- Sequence context

## Amino-Acid Features

- Reference amino acid
- Alternate amino acid
- Amino-acid property differences
- Charge change
- Polarity change
- Hydrophobicity-related change
- Molecular-property differences

## Conservation Features

Where reliable public conservation annotations are available:

- Evolutionary conservation scores
- Residue conservation indicators

## Protein Context Features

Where available:

- Protein position
- Relative protein position
- Domain membership
- Functional region
- Structural/context annotation

The final model should use only features that can be reproduced consistently for new variants.

---

# Dataset Quality Rules

Each processed record should eventually contain a data-quality status.

Possible checks include:

- Missing gene symbol
- Missing variant identifier
- Missing DNA change
- Missing protein change
- Invalid allele representation
- Unsupported variant type
- Conflicting source classification
- Missing required annotations
- Duplicate record

Records that fail critical validation should not silently enter model training.

---

# Planned Dataset Layers

The project will maintain separate data stages.

data/
|
|-- raw/
|     Original downloaded public datasets
|
|-- interim/
|     Filtered and partially normalized records
|
|-- processed/
|     Final machine-learning-ready dataset
|
`-- demo/
      Curated competition demonstration records

Raw files should remain unchanged after download.

All transformations should happen in later layers.

---

# Planned Core Variant Schema

The processed dataset should aim to contain fields similar to:

variant_id
gene
chromosome
position
reference_allele
alternate_allele
dna_change
protein_change
variant_type
reference_amino_acid
alternate_amino_acid
protein_position
source
source_classification
review_status
conflict_status
data_quality_status

Additional engineered features will be introduced in later sprints.

---

# Data Provenance

Every variant used by GeneMirror should retain information about where it originated.

At minimum:

- Source database
- Source identifier
- Data/version date where practical
- Original classification
- Review/evidence status where available

This allows predictions and demonstrations to remain traceable.

---

# Dataset Versioning

Processed datasets should be versioned.

Example:

genemirror_variants_v1.csv

Future changes may produce:

genemirror_variants_v2.csv

Dataset versions should not be overwritten without documenting what changed.

---

# Machine Learning Dataset Rule

Frontend mock data must never be used as training data.

The correct workflow is:

Public Genomic Source
        |
        v
Download
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
Feature Engineering
        |
        v
Machine Learning Dataset

The current file:

src/data/mockData.ts

is UI demonstration data only.

---

# Version 1 Dataset Strategy

Primary Variant Source:

NCBI ClinVar

Sequence / Consequence Annotation:

Ensembl and/or appropriate NCBI reference resources

Protein Annotation:

UniProt

Initial Variant Type:

Missense Single Nucleotide Variants

Initial Demo Genes:

TP53
BRCA1
CFTR
HBB
APOE
MTHFR

Training Scope:

May include additional genes to ensure adequate and diverse model training data.

Final Output Dataset:

data/processed/genemirror_variants_v1.csv

---

# Key Scientific Rule

GeneMirror will separate three concepts:

1. Source classification
2. Machine learning prediction
3. User-facing GeneMirror impact class

These must not be presented as if they are identical.

Source classification provides training/evaluation evidence.

The machine learning model generates a computational prediction.

The GeneMirror interface presents that prediction in an understandable format.

---

# Step 4 Final Decision

GeneMirror AI Version 1 will use ClinVar as the primary curated variant source and supplement it with sequence and protein annotations from established public genomic resources.

No model training will begin until the dataset has been downloaded, inspected, validated, filtered, normalized, and checked for label leakage.