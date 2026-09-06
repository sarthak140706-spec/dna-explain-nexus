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
  dna: string;
  protein: string;
  type: string;
  impact: Impact;
  confidence: number;
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
  { id: "GM-TP53-0743", gene: "TP53", dna: "c.743G>A", protein: "p.Arg248His", type: "Missense", impact: "High", confidence: 87 },
  { id: "GM-TP53-0524", gene: "TP53", dna: "c.524C>G", protein: "p.Pro175Arg", type: "Missense", impact: "Moderate", confidence: 79 },
  { id: "GM-BRCA1-1513", gene: "BRCA1", dna: "c.1513G>T", protein: "p.Val505Leu", type: "Missense", impact: "Moderate", confidence: 84 },
  { id: "GM-CFTR-2199", gene: "CFTR", dna: "c.2199C>T", protein: "p.Phe733Cys", type: "Missense", impact: "Moderate", confidence: 79 },
  { id: "GM-HBB-0020", gene: "HBB", dna: "c.20A>T", protein: "p.Glu6Val", type: "Missense", impact: "High", confidence: 96 },
  { id: "GM-APOE-3920", gene: "APOE", dna: "c.3920C>T", protein: "p.Ser130Cys", type: "Missense", impact: "Low", confidence: 88 },
  { id: "GM-MTHFR-0667", gene: "MTHFR", dna: "c.667C>T", protein: "p.Ala222Val", type: "Missense", impact: "Moderate", confidence: 82 },
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
