# GeneMirror AI — Demo Gene and Variant Scope

## Purpose

This document defines the genes and variant types that will be used for the GeneMirror AI Version 1 demonstration.

The purpose of limiting the initial scope is to make the system scientifically manageable, testable, and suitable for a reliable competition demonstration.

---

# Version 1 Gene Scope

GeneMirror AI Version 1 will initially showcase the following six genes:

1. TP53
2. BRCA1
3. CFTR
4. HBB
5. APOE
6. MTHFR

These genes provide a diverse demonstration set for the platform.

The machine learning architecture should not be permanently restricted to these six genes.

They represent the initial product and competition-demo scope.

---

# 1. TP53

Gene Symbol:

TP53

Gene Name:

Tumor Protein P53

Purpose in GeneMirror:

TP53 will act as one of the primary demonstration genes for variant-effect analysis.

It provides a useful example for showing:

- DNA-level variation
- Amino-acid substitution
- Protein context
- Variant-effect prediction
- Explainable AI

---

# 2. BRCA1

Gene Symbol:

BRCA1

Gene Name:

BRCA1 DNA Repair Associated

Purpose in GeneMirror:

BRCA1 provides an additional gene with different protein characteristics and allows GeneMirror to demonstrate that the platform is not restricted to a single gene.

---

# 3. CFTR

Gene Symbol:

CFTR

Gene Name:

CF Transmembrane Conductance Regulator

Purpose in GeneMirror:

CFTR adds additional biological diversity to the demonstration dataset and provides useful missense-variant examples for computational analysis.

---

# 4. HBB

Gene Symbol:

HBB

Gene Name:

Hemoglobin Subunit Beta

Purpose in GeneMirror:

HBB provides a compact and well-studied gene/protein example that can be used to clearly demonstrate DNA-to-protein variant interpretation.

---

# 5. APOE

Gene Symbol:

APOE

Gene Name:

Apolipoprotein E

Purpose in GeneMirror:

APOE provides another protein context for testing and demonstrating the generality of the GeneMirror analysis workflow.

---

# 6. MTHFR

Gene Symbol:

MTHFR

Gene Name:

Methylenetetrahydrofolate Reductase

Purpose in GeneMirror:

MTHFR expands the initial demonstration set and provides additional missense variants for model and interface testing.

---

# Supported Variant Scope

GeneMirror AI Version 1 will focus on:

- Single Nucleotide Variants (SNVs)
- Missense variants
- Protein-changing single-nucleotide substitutions

The initial demo will not attempt to support every possible genomic variant type.

---

# Excluded Variant Types for Version 1

The following are outside the initial prediction scope:

- Insertions
- Deletions
- Frameshift variants
- Stop-gain variants
- Stop-loss variants
- Splice-site variants
- Copy number variations
- Large structural variants
- Gene fusions

These may be considered in future versions.

---

# Demo Variant Selection Rule

Variants used in the final GeneMirror demonstration must come from verified public genomic data sources.

The variants must not be assigned biological labels manually.

For each selected demo variant, we should preserve available information such as:

- Gene symbol
- Variant identifier
- Genomic position
- DNA change
- Protein change
- Reference allele
- Alternate allele
- Variant type
- Source
- Source classification
- Evidence/review information when available

---

# Important Mock-Data Rule

The current Lovable frontend contains mock variants and mock prediction values.

These values exist only to demonstrate the interface.

They must not automatically become backend training data or scientific ground truth.

During later sprints:

Frontend Mock Data
        ↓
DO NOT use as scientific labels
        ↓
Retrieve Curated Public Data
        ↓
Validate
        ↓
Create Processed Dataset
        ↓
Generate Real Backend Results

---

# Demo Selection Strategy

For the final competition demonstration, we should eventually select a small number of representative variants.

A useful demonstration should include examples where the trained system produces different predicted impact levels.

For example:

Gene A
→ Variant 1
→ Lower predicted impact

Gene B
→ Variant 2
→ Intermediate predicted impact

Gene C
→ Variant 3
→ Higher predicted impact

The actual variants and their classifications will be selected only after the curated dataset has been processed.

---

# Primary Demo Gene

TP53 will initially serve as the flagship GeneMirror demonstration gene because the existing frontend already uses TP53 prominently.

The flagship workflow will be:

TP53
↓
Select Curated Missense Variant
↓
Reference vs Variant DNA
↓
Protein Consequence
↓
Variant Effect Prediction
↓
Explainable AI
↓
Protein Context
↓
AI Scientist Explanation

The specific TP53 variant used for the final demonstration must be verified against the selected public dataset.

---

# Secondary Demo Genes

The secondary genes are:

- BRCA1
- CFTR
- HBB
- APOE
- MTHFR

They will demonstrate that the GeneMirror architecture can analyze variants across multiple genes.

---

# Scalability Requirement

Although Version 1 highlights six genes, backend components should be designed around standardized variant records rather than hard-coded gene-specific logic.

The intended architecture is:

Curated Variant Record
        ↓
Generic Validation
        ↓
Generic Feature Extraction
        ↓
Prediction Model
        ↓
XAI
        ↓
GeneMirror Result

This allows additional genes to be introduced later without redesigning the entire application.

---

# Version 1 Demo Scope Summary

Primary Demo Gene:

TP53

Secondary Demo Genes:

BRCA1
CFTR
HBB
APOE
MTHFR

Supported Variant Type:

Missense Single Nucleotide Variants

Primary Analysis:

Computational Variant-Effect Prediction

Final Variant Source:

Curated Public Genomic Dataset

Frontend Mock Variants:

UI demonstration only and not scientific ground truth