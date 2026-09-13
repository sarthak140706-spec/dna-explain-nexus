# 🧬 GeneMirror AI

### Explainable Intelligence for Genetic Variant Analysis

GeneMirror AI is an Explainable AI platform for computational analysis of human missense genetic variants.

The system combines genomic variant validation, machine-learning-based variant effect prediction, confidence calibration, explainable AI, protein-level context, and grounded scientific explanations within a unified research interface.

GeneMirror AI is designed for **research and educational use** and does not provide clinical diagnosis, treatment recommendations, or medical advice.

---

## 🎯 Problem Statement

Interpreting the potential impact of genetic variants is complex, and many computational prediction systems provide results without clearly explaining why a variant receives a particular prediction.

GeneMirror AI addresses this gap by using Explainable AI to analyze human missense variants, predict their potential impact, estimate prediction confidence, and provide interpretable evidence and protein-level context through a unified research platform.

---

## 💡 Proposed Solution

GeneMirror AI provides an end-to-end computational workflow:

```text
Genetic Variant
      ↓
Variant Validation
      ↓
Genomic Annotation
      ↓
Variant Effect Prediction
      ↓
Confidence Calibration
      ↓
Explainable AI
      ↓
Protein Context Analysis
      ↓
GeneMirror Scientist
      ↓
Interactive Research Interface
```

Instead of returning only a prediction score, GeneMirror AI provides multiple layers of evidence so users can understand how the system reached its computational result.

---

## ✨ Core Features

### 🧬 Genome Explorer

Browse curated genes and missense variants through an interactive interface.

Current demonstration genes include:

- TP53
- BRCA1
- CFTR
- HBB
- APOE
- MTHFR

---

### 🪞 Gene Mirror

The flagship analysis interface compares the reference and variant representations and displays the live computational analysis.

Outputs include:

- Raw model score
- Calibrated probability
- Predicted impact class
- Confidence score
- Uncertainty score
- Confidence band
- Reference and alternate amino acids

Impact classes are presented as:

```text
LOW
MODERATE
HIGH
```

These classes represent computational model outputs and must not be interpreted as clinical classifications.

---

### 🔬 Genomic Annotation

GeneMirror AI uses genomic annotation to verify variant identity and consequence.

The annotation pipeline:

- validates GRCh38 genomic coordinates
- verifies reference and alternate alleles
- identifies transcript consequences
- prioritizes appropriate transcripts
- verifies missense consequences
- compares DNA and protein-level representations

Transcript selection prioritizes:

```text
MANE Select
    ↓
MANE Plus Clinical
    ↓
Canonical Transcript
    ↓
Protein-Coding Transcript
    ↓
Missense Consequence
```

Annotation results are locally cached to improve repeated analysis performance.

---

### 🤖 Variant Effect Prediction

The prediction engine uses a:

**HistGradientBoostingClassifier**

The model was trained using a processed ClinVar-derived missense variant dataset.

The prediction target is a:

> ClinVar-derived pathogenicity proxy for computational variant-effect modeling.

The model output is not a clinical probability.

Model information:

```text
Model: HistGradientBoostingClassifier
Model Version: GeneMirror-v1-Sprint4
Input Features: 28
```

Held-out evaluation included:

```text
ROC-AUC ≈ 0.77
PR-AUC  ≈ 0.66
MCC     ≈ 0.40
```

---

## 📊 Explainable AI — XAI Lab

GeneMirror AI does not present the prediction as a black-box result.

The XAI engine estimates how individual model features influence the prediction relative to a reference input.

Examples of model features include:

- amino-acid molecular-weight differences
- hydrophobicity differences
- charge changes
- reference amino-acid properties
- sequence-derived properties
- variant-related features

Feature effects are categorized as:

```text
Higher Impact
Lower Impact
Neutral
```

The explanation is a model interpretation and should not be treated as proof of biological causation.

---

## 🎯 Confidence Calibration

GeneMirror AI explicitly separates:

```text
Raw Model Score
≠
Calibrated Probability
≠
Confidence
≠
Impact Class
```

Isotonic calibration is used to calibrate model outputs.

Prediction confidence is derived from the uncertainty of the calibrated probability using normalized binary entropy.

The interface exposes both:

- Confidence
- Uncertainty

This prevents raw classifier scores from being presented as certainty.

---

## 🧪 Protein Explorer

Protein-level context is retrieved using UniProtKB.

The protein engine provides:

- UniProt accession
- protein name
- protein length
- affected residue
- local sequence window
- reference residue verification
- overlapping protein annotations
- nearby protein annotations
- visualization tracks

The affected residue is verified against the protein sequence before the complete analysis is accepted.

---

## 🧠 GeneMirror Scientist

GeneMirror Scientist converts structured analysis results into a readable scientific explanation.

It receives grounded information from:

- variant validation
- prediction engine
- confidence calibration
- XAI engine
- protein context engine

The Scientist does **not** calculate the scientific prediction itself.

Its role is to explain already-computed structured evidence.

The system includes a deterministic fallback so explanations remain available even when an external language-model provider is disabled or unavailable.

The Scientist is constrained from inventing:

- unsupported disease associations
- treatment recommendations
- genetic modification instructions
- unsupported biological mechanisms
- clinical conclusions

---

## 🏗️ System Architecture

```text
┌──────────────────────────────────────┐
│          React + TypeScript          │
│              Frontend                │
└──────────────────┬───────────────────┘
                   │
                   │ REST API
                   ▼
┌──────────────────────────────────────┐
│              FastAPI                 │
│               Backend                │
└──────────────────┬───────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   Validation   Prediction   Protein
   & VEP        + XAI        Context
        │          │          │
        └──────────┼──────────┘
                   ▼
          GeneMirror Scientist
                   │
                   ▼
          Unified Analysis API
```

The main frontend analysis flow uses:

```text
POST /api/v1/analysis
```

This endpoint orchestrates the complete GeneMirror analysis pipeline.

---

## 🔌 API Endpoints

GeneMirror AI exposes the following FastAPI endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | API health check |
| POST | `/api/v1/variants/validate` | Variant validation |
| POST | `/api/v1/predict` | Raw model prediction |
| POST | `/api/v1/xai` | Calibrated prediction and XAI |
| POST | `/api/v1/protein-context` | Protein context |
| POST | `/api/v1/scientist` | Grounded explanation |
| POST | `/api/v1/analysis` | Complete unified analysis |

Interactive API documentation is available while the backend is running at:

```text
http://127.0.0.1:8000/docs
```

---

## 📚 Dataset

The primary variant source is **ClinVar**.

The data pipeline performs:

```text
Raw ClinVar
    ↓
Validation
    ↓
GRCh38 Filtering
    ↓
Germline SNV Filtering
    ↓
Missense Selection
    ↓
Allele Validation
    ↓
Normalization
    ↓
Duplicate Removal
    ↓
Processed Dataset
```

Final processed dataset statistics:

```text
Variants:     2,431,963
Genes:        19,116
Variant Type: Missense SNVs
Assembly:     GRCh38
```

Large raw and processed datasets are intentionally excluded from Git version control.

---

## 🧬 Competition Demo Variants

The frontend contains curated variants for demonstrating the complete pipeline.

| Gene | DNA Change | Protein Change |
|---|---|---|
| TP53 | c.743G>A | p.Arg248His |
| BRCA1 | c.190T>G | p.Cys64Gly |
| CFTR | c.328G>C | p.Asp110His |
| HBB | c.223G>C | p.Gly75Arg |
| APOE | c.526C>T | p.Arg176Cys |
| MTHFR | c.470G>A | p.Arg157Gln |

### Flagship Demonstration

```text
Gene: TP53
DNA Change: c.743G>A
Protein Change: p.Arg248His
```

This variant is used to demonstrate the complete GeneMirror workflow across Gene Mirror, XAI Lab, Protein Explorer, and GeneMirror Scientist.

---

## 🖥️ Frontend

The frontend is built using:

- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack
- Recharts
- Lucide
- shadcn/Radix components

Main pages:

```text
Overview
Genome Explorer
Gene Mirror
Protein Explorer
XAI Lab
AI Scientist
```

---

## ⚙️ Backend

The backend uses:

- Python
- FastAPI
- Pydantic
- pandas
- NumPy
- scikit-learn
- requests
- Uvicorn

Scientific resources include:

- ClinVar
- Ensembl VEP
- UniProtKB

---

## 📁 Project Structure

```text
dna-explain-nexus/
│
├── backend/
│   ├── annotation/
│   ├── api/
│   ├── calibration/
│   ├── modeling/
│   ├── protein/
│   ├── scientist/
│   └── xai/
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── docs/
│
├── models/
│
├── src/
│   ├── components/
│   ├── data/
│   ├── routes/
│   └── services/
│       └── api/
│
├── tests/
│
├── README.md
└── package.json
```

---

## 🚀 Running GeneMirror AI Locally

### 1. Clone the repository

```bash
git clone https://github.com/sarthak140706-spec/dna-explain-nexus.git
cd dna-explain-nexus
```

### 2. Create and activate the Python environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```powershell
pip install -r backend\requirements.txt
```

### 4. Start the FastAPI backend

For a stable demonstration run:

```powershell
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

### 5. Install frontend dependencies

In another terminal:

```powershell
npm install
```

### 6. Start the frontend

```powershell
npm run dev
```

Frontend:

```text
http://localhost:8080
```

---

## 🧪 Testing

GeneMirror AI includes automated tests covering:

- API integration
- scientific consistency
- cross-component consistency
- safety guardrails
- multiple genes and variants
- failure conditions
- malformed input
- genomic validation failures
- protein reference mismatches
- unsupported variants

Run the complete test suite using:

```powershell
python -m pytest tests -q
```

---

## 🔒 Safety & Scientific Boundaries

GeneMirror AI is an **in-silico research prototype**.

It does not:

- diagnose genetic disease
- determine whether a person has a medical condition
- recommend treatment
- provide medical advice
- design gene-editing experiments
- generate CRISPR guides
- recommend genetic modification
- provide wet-lab protocols

A LOW predicted impact does not mean that a variant is medically safe or benign.

A HIGH predicted impact does not mean that a variant is disease-causing or clinically pathogenic.

Predictions must be interpreted only as computational model outputs.

---

## ⚠️ Disclaimer

> **GeneMirror AI provides computational predictions for research and educational purposes only. It does not provide clinical diagnosis, treatment recommendations, or medical advice.**

---

## 🛠️ Development Roadmap

GeneMirror AI was developed through ten structured sprints:

```text
Sprint 1  — Scientific Scope, Dataset & Variant Definition
Sprint 2  — Genomic Data Ingestion & Validation
Sprint 3  — Sequence Annotation & Variant Consequence
Sprint 4  — Variant Effect Prediction Model
Sprint 5  — Explainable AI & Confidence Calibration
Sprint 6  — Protein Context & Visualization Data
Sprint 7  — GeneMirror Scientist
Sprint 8  — FastAPI Backend & API Contracts
Sprint 9  — Frontend Integration
Sprint 10 — Testing, Validation, Safety & Competition Demo
```

---

## 🎓 AI Innovation Challenge 2026

GeneMirror AI was developed as a software-based AI research prototype for the **AI Innovation Challenge 2026**.

Primary competition domain:

**Healthcare & Digital Well-being**

Technical focus:

**Explainable AI for computational genetic variant interpretation**

---

## 👨‍💻 Author

**Sarthak Jadhav**

B.Tech — Artificial Intelligence & Data Science  
AISSMS Institute of Information Technology, Pune

---

## 📌 Project Status

**Research Prototype — v1.0**

The complete pipeline currently supports:

```text
Variant Selection
      ↓
Scientific Validation
      ↓
Genomic Annotation
      ↓
ML Prediction
      ↓
Confidence Calibration
      ↓
Explainable AI
      ↓
Protein Context
      ↓
Grounded Scientist Explanation
      ↓
Interactive Visualization
```

GeneMirror AI demonstrates how explainability can make computational genetic variant prediction more transparent and interpretable.