import {
  analyzeVariant,
} from "./analysis";

import type {
  VariantRequest,
} from "./types";

export async function runAnalysisSmokeTest() {
  const variant: VariantRequest = {
    gene_symbol: "TP53",

    reference_allele: "G",

    alternate_allele: "A",

    protein_position: 248,

    reference_amino_acid: "R",

    alternate_amino_acid: "H",

    protein_change: "R248H",
  };

  const result =
    await analyzeVariant(
      variant,
    );

  console.log(
    "GeneMirror unified analysis:",
    result,
  );

  return result;
}