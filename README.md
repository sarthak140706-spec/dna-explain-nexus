# GeneMirror Insights

Build a complete, polished, modern frontend for a project called GeneMirror AI.

Project concept

GeneMirror AI is an Explainable AI platform for analyzing and visualizing genetic variants.

The product allows users to:

 Select a gene

 Select a curated genetic variant

 Compare the reference DNA sequence with the variant sequence

 View the corresponding protein-level change

 View an AI-predicted impact score

 View an explainable AI breakdown showing why the model gave that prediction

 Explore a visual protein representation

 Ask an AI Scientist assistant to explain the results in simple or technical language

Important development rule

Build FRONTEND ONLY.

Do NOT implement:

 backend

 FastAPI

 Flask

 database

 authentication backend

 APIs

 ML models

 real genomic processing

 real LLM integration

 real file processing

Use mock/static data only.

However, structure the frontend cleanly so that backend APIs can easily be connected later.

Design Direction

Create a premium futuristic biotech / AI research interface.

The UI should feel like a combination of:

 modern genomics platform

 scientific research dashboard

 AI laboratory software

 futuristic medical-tech interface

Avoid making it look like:

 a hospital website

 a generic admin dashboard

 a colorful student project

 a basic Bootstrap layout

The design should look suitable for an AI Innovation Challenge presentation.

Visual Theme

Use a dark futuristic biotechnology theme.

Suggested colors:

 Main background: #07111F

 Secondary background: #0C1828

 Card background: #111F32

 Primary cyan: #22D3EE

 Biotechnology violet: #8B5CF6

 DNA blue: #38BDF8

 Success green: #22C55E

 Warning amber: #F59E0B

 Critical red: #EF4444

 Main text: #F8FAFC

 Secondary text: #94A3B8

 Borders: subtle blue/cyan transparent borders

Use gradients only subtly.

Use soft glow effects around important DNA/AI elements.

Do not overuse neon.

Typography

Use a modern clean font such as:

 Inter

 Manrope

 Geist

Use bold headings and clean readable body text.

Scientific values should use a slightly technical/monospaced appearance where appropriate.

Application Layout

Use a fixed left sidebar and a top navigation bar.

Sidebar should contain:

 Overview

 Genome Explorer

 Gene Mirror

 Protein Explorer

 XAI Lab

 AI Scientist

At the bottom of the sidebar show:

 GeneMirror AI logo

 version text such as Research Prototype v1.0

Top navbar should contain:

 current page title

 small project status badge: Simulation Mode

 notification icon

 profile/avatar placeholder

PAGE 1 — Overview Dashboard

Create a visually impressive landing dashboard.

Header:

GeneMirror AI

Subtitle:

Explainable Intelligence for Genetic Variant Analysis

Add a short statement:

Analyze, compare and understand the predicted effects of genetic variants through AI-powered computational insights.

Create four KPI cards:

 Genes Available — 12

 Curated Variants — 248

 Variants Analyzed — 1,372

 Average Model Confidence — 87.4%

Use demo values only.

Add a large central section called:

Variant Analysis Pipeline

Show an interactive visual flow:

DNA Variant → Sequence Analysis → Protein Context → AI Prediction → XAI Explanation

Each stage should appear as a connected visual card/node.

Add another panel:

Recent Analyses

Use a table with mock data containing:

 Gene

 Variant

 Protein Change

 Predicted Impact

 Confidence

 Status

Example rows:

 BRCA1

 CFTR

 TP53

 HBB

 APOE

Use status pills like:

 Low

 Moderate

 High

Add a small panel called:

Model Confidence Distribution

Create a clean mock bar/chart visualization.

PAGE 2 — Genome Explorer

Create a page for browsing genes and variants.

Top section:

Search Genes

Include:

 search bar

 gene category filter

 chromosome filter

Below show gene cards.

Each card should display:

 gene symbol

 full gene name

 chromosome

 number of curated variants

 short description

 View Gene button

Use mock gene entries such as:

 BRCA1

 TP53

 CFTR

 HBB

 APOE

 MTHFR

Do not provide clinical or medical advice.

When a gene is selected, show a detailed side panel with:

 gene symbol

 gene description

 chromosome

 sequence length

 protein name

 number of curated variants

Below that display a table of variants with:

 Variant ID

 DNA Change

 Protein Change

 Type

 Predicted Impact

 Confidence

Add a button:

Open in Gene Mirror

This button should navigate to the Gene Mirror page using frontend state only.

PAGE 3 — Gene Mirror

This is the MAIN flagship page.

Design this page to be the most visually impressive part of the application.

Header:

Gene Mirror

Subtitle:

Compare reference and variant sequences side by side.

At the top add selectors:

 Select Gene

 Select Variant

Use static data.

Example:

Gene: TP53

Variant: c.743G>A

Main Mirror Comparison

Create two large side-by-side panels.

LEFT PANEL

Title:

REFERENCE

Show:

 reference DNA sequence

 highlighted nucleotide position

 reference amino acid

 protein position

 model score

Example:

DNA:

... A C G T G C C A G T ...

Highlight the reference nucleotide.

Show:

Protein:

Arginine

Score:

0.14

Prediction badge:

LOW IMPACT

RIGHT PANEL

Title:

VARIANT

Show:

 variant DNA sequence

 highlighted changed nucleotide

 changed amino acid

 protein position

 predicted score

Example:

DNA:

... A C G T A C C A G T ...

Highlight the changed nucleotide.

Protein:

Histidine

Score:

0.87

Prediction badge:

HIGH IMPACT

Between both panels add a central visual connector:

REFERENCE → VARIANT

and show the mutation:

G → A

Add subtle animation/glow highlighting the difference.

Impact Comparison Section

Below the mirror create cards comparing:

 Sequence Context

 Conservation Score

 Protein Region Importance

 Amino Acid Difference

 Predicted Functional Impact

Show reference vs variant values.

Impact Meter

Create a large gauge/progress indicator:

Predicted Variant Effect Score

Example:

0.87 / 1.00

Status:

High Predicted Impact

Add text:

Computational prediction only — not a clinical diagnosis.

This disclaimer should always be visible.

PAGE 4 — Protein Explorer

Create a modern protein visualization page.

Since there is no backend or real 3D viewer yet, create a placeholder interactive protein visualization card.

It should visually resemble a 3D protein structure using:

 abstract molecular shapes

 connected chains

 highlighted mutation point

Show:

Protein Information

 Protein Name

 Gene

 Protein Length

 Variant Position

 Amino Acid Change

Example:

Arg248His

Highlight the affected residue with a glowing marker.

Add a control panel:

 Rotate

 Zoom

 Reset View

 Highlight Variant

These buttons only need frontend interactions.

Add cards showing:

 Structural Region

 Conservation

 Local Environment

 Predicted Stability Change

Use mock data.

PAGE 5 — XAI Lab

This should focus entirely on explainability.

Header:

XAI Lab

Subtitle:

Understand why the model produced its prediction.

Create a large section:

Prediction Explanation

Show:

Predicted Impact: HIGH

Model Confidence: 87%

Create a horizontal feature-importance chart using mock values:

 Evolutionary Conservation — 38%

 Protein Region Context — 27%

 Amino Acid Properties — 20%

 Sequence Context — 15%

Use animated bars.

Add another card:

Key Model Drivers

Show explanations such as:

 High evolutionary conservation at affected position

 Strong amino-acid property change

 Variant located within a functionally important protein region

 Sequence context differs from common benign patterns

Add a section:

Model Reasoning Summary

Display:

The model prediction is primarily influenced by conservation and protein-region context. These features contribute most strongly to the elevated effect score.

Add another section:

Confidence Breakdown

Show:

 Data Quality

 Feature Reliability

 Model Agreement

 Prediction Stability

Use progress bars.

PAGE 6 — AI Scientist

Create an AI assistant interface.

Name:

GeneMirror Scientist

Subtitle:

Ask questions about your variant analysis.

The chat UI should look premium and scientific.

Add suggested prompts:

 Explain this variant simply

 Why is the impact score high?

 What does conservation mean?

 Explain the protein change

 Summarize this analysis

Since there is no backend, clicking suggested prompts should return predefined mock responses.

Add two modes:

Student Mode

Simplified explanations.

Research Mode

More technical explanations.

Use a toggle switch.

Example mock response:

This variant changes one nucleotide in the DNA sequence, which alters the corresponding amino acid in the protein. The model assigns a high impact score mainly because the affected position is strongly conserved and lies within an important protein region.

Always include:

This information is for computational analysis and educational use only.

Interaction Requirements

Make the interface feel like a real application.

Implement frontend-only interactions such as:

 sidebar navigation

 dropdown selections

 tabs

 search

 filtering

 hover effects

 animated progress bars

 modal windows

 selected variant states

 AI chat mock responses

 view transitions

 responsive cards

 tooltips

 protein visualization placeholder controls

 gene selection

 variant selection

No backend requests should occur.

Frontend Architecture

Use:

 React

 TypeScript

 Tailwind CSS

 reusable components

 clean component structure

If available, use:

 shadcn/ui

 Lucide icons

 Recharts for charts

Create mock data inside local frontend files.

Use clean components such as:

 Sidebar

 TopNavbar

 KPICard

 GeneCard

 VariantTable

 SequenceViewer

 MirrorComparison

 ImpactGauge

 FeatureImportance

 ProteinViewer

 ScientistChat

Keep backend integration in mind by isolating mock data from UI components.

For example, store data under:

src/data/mockGenes.ts

src/data/mockVariants.ts

src/data/mockAnalysis.ts

Later these will be replaced with backend API calls.

Responsive Design

Optimize primarily for:

1920 × 1080 desktop presentation

because this project will be demonstrated on a laptop/projector.

Also make it reasonably responsive for smaller laptop screens.

Do not prioritize mobile design over desktop.

Safety and Scientific Communication

The frontend must never present results as medical diagnosis or treatment advice.

Use terminology such as:

 Predicted impact

 Computational estimate

 Model confidence

 Variant effect prediction

Avoid definitive terminology such as:

 This mutation causes disease

 This person has a disease

 This gene should be edited

 Recommended genetic modification

Always display a subtle disclaimer:

GeneMirror AI provides computational predictions for research and educational purposes and is not a diagnostic or clinical decision-making system.

Final Goal

The final frontend should feel like a real AI biotechnology research product, not a student dashboard.

Prioritize:

 Premium visual quality

 Strong Gene Mirror reference-vs-variant comparison

 Clear XAI visualizations

 Smooth interactions

 Scientific appearance

 Easy future backend integration

Use meaningful mock data throughout so every page looks complete and demo-ready even without a backend.

Do not build or connect any backend functionality yet.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/c8f39fc4-fc00-46c3-a3b0-225fdf710b04).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
