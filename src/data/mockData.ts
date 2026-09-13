export type Impact = "Low" | "Moderate" | "High";

export type Gene = {
  symbol: string;
  name: string;
  chromosome: string;
  variants: number;
  length: string;
  protein: string;
  description: string;
  category: string;
};

export type Variant = {
  id: string;
  gene: string;

  chromosome: string;
  position: number;

  dna: string;
  protein: string;

  type: string;

  demoLabel?: string;
};

export const genes: Gene[] = [
  { symbol: "TP53", name: "Tumor protein p53", chromosome: "17p13.1", variants: 42, length: "2,516 bp", protein: "Cellular tumor antigen p53", description: "A stress-response protein used here as a curated research example for sequence and protein-context analysis.", category: "Tumor suppressor" },
  { symbol: "BRCA1", name: "BRCA1 DNA repair associated", chromosome: "17q21.31", variants: 56, length: "5,592 bp", protein: "Breast cancer type 1 susceptibility protein", description: "A DNA repair gene represented in the research corpus with curated variant annotations.", category: "DNA repair" },
  { symbol: "CFTR", name: "CF transmembrane conductance regulator", chromosome: "7q31.2", variants: 38, length: "6,129 bp", protein: "Cystic fibrosis transmembrane conductance regulator", description: "An ion-channel gene used to explore sequence context and protein-region importance.", category: "Transport" },
  { symbol: "HBB", name: "Hemoglobin subunit beta", chromosome: "11p15.4", variants: 31, length: "1,606 bp", protein: "Hemoglobin subunit beta", description: "A compact protein-coding gene useful for studying high-contrast amino acid changes.", category: "Blood protein" },
  { symbol: "APOE", name: "Apolipoprotein E", chromosome: "19q13.32", variants: 27, length: "3,597 bp", protein: "Apolipoprotein E", description: "A lipid-transport gene included for comparative analysis across protein contexts.", category: "Lipid transport" },
  { symbol: "MTHFR", name: "Methylenetetrahydrofolate reductase", chromosome: "1p36.22", variants: 22, length: "2,205 bp", protein: "Methylenetetrahydrofolate reductase", description: "A metabolic gene represented with curated sequence and conservation signals.", category: "Metabolism" },
];

export const variants: Variant[] = [
  {
    id: "GM-TP53-R248H",
    gene: "TP53",
    chromosome: "17",
    position: 7674220,
    dna: "c.743G>A",
    protein: "p.Arg248His",
    type: "Missense",
    demoLabel: "Flagship demo",
  },

  {
    id: "GM-APOE-R176C",
    gene: "APOE",
    chromosome: "19",
    position: 44908822,
    dna: "c.526C>T",
    protein: "p.Arg176Cys",
    type: "Missense",
    demoLabel: "Verified demo",
  },

  {
    id: "GM-BRCA1-C64G",
    gene: "BRCA1",
    chromosome: "17",
    position: 43106478,
    dna: "c.190T>G",
    protein: "p.Cys64Gly",
    type: "Missense",
    demoLabel: "Verified demo",
  },

  {
    id: "GM-CFTR-D110H",
    gene: "CFTR",
    chromosome: "7",
    position: 117530953,
    dna: "c.328G>C",
    protein: "p.Asp110His",
    type: "Missense",
    demoLabel: "Verified demo",
  },

  {
    id: "GM-HBB-G75R",
    gene: "HBB",
    chromosome: "11",
    position: 5226669,
    dna: "c.223G>C",
    protein: "p.Gly75Arg",
    type: "Missense",
    demoLabel: "Verified demo",
  },

  {
    id: "GM-MTHFR-R157Q",
    gene: "MTHFR",
    chromosome: "1",
    position: 11801166,
    dna: "c.470G>A",
    protein: "p.Arg157Gln",
    type: "Missense",
    demoLabel: "Verified demo",
  },
];

export const recentAnalyses = [
  { gene: "BRCA1", variant: "c.5266G>A", protein: "p.Gly1756Asp", impact: "High" as Impact, confidence: 91 },
  { gene: "CFTR", variant: "c.1521_1523del", protein: "p.Phe508del", impact: "Moderate" as Impact, confidence: 74 },
  { gene: "TP53", variant: "c.743G>A", protein: "p.Arg248His", impact: "High" as Impact, confidence: 87 },
  { gene: "HBB", variant: "c.20A>T", protein: "p.Glu6Val", impact: "High" as Impact, confidence: 96 },
  { gene: "APOE", variant: "c.3920C>T", protein: "p.Ser130Cys", impact: "Low" as Impact, confidence: 88 },
];

export const dnaReference = ["A", "C", "G", "T", "G", "C", "C", "A", "G", "T"];
export const dnaVariant = ["A", "C", "G", "T", "A", "C", "C", "A", "G", "T"];
