import {
  useMemo,
  useState,
} from "react";

import {
  Activity,
  ArrowRight,
  Bell,
  BrainCircuit,
  CircleHelp,
  Dna,
  Gauge,
  GitCompareArrows,
  Grid2X2,
  Info,
  Layers3,
  Menu,
  MessageSquareText,
  Microscope,
  Network,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Sparkles,
  Target,
  ZoomIn,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";

import {
  analyzeVariant,
  ApiError,
} from "@/services/api";

import type {
  UnifiedAnalysisResponse,
  VariantRequest,
} from "@/services/api";

import {
  dnaReference,
  dnaVariant,
  genes,
  recentAnalyses,
  variants,
  type Gene,
  type Impact,
} from "@/data/mockData";


// ============================================================
// Page types
// ============================================================

type Page =
  | "Overview"
  | "Genome Explorer"
  | "Gene Mirror"
  | "Protein Explorer"
  | "XAI Lab"
  | "AI Scientist";


// ============================================================
// Navigation
// ============================================================

const navItems: {
  label: Page;
  icon: typeof Grid2X2;
  accent: string;
}[] = [
  {
    label: "Overview",
    icon: Grid2X2,
    accent: "text-cyan",
  },
  {
    label: "Genome Explorer",
    icon: Dna,
    accent: "text-dna",
  },
  {
    label: "Gene Mirror",
    icon: GitCompareArrows,
    accent: "text-violet",
  },
  {
    label: "Protein Explorer",
    icon: Microscope,
    accent: "text-mint",
  },
  {
    label: "XAI Lab",
    icon: BrainCircuit,
    accent: "text-amber",
  },
  {
    label: "AI Scientist",
    icon: MessageSquareText,
    accent: "text-danger",
  },
];


// ============================================================
// Shared styling
// ============================================================

const impactStyles: Record<
  Impact,
  string
> = {
  Low:
    "border-mint/30 bg-mint/10 text-mint",

  Moderate:
    "border-amber/30 bg-amber/10 text-amber",

  High:
    "border-danger/30 bg-danger/10 text-danger",
};

const pageSubtitles: Record<
  Page,
  string
> = {
  Overview:
    "Explainable intelligence for genetic variant analysis",

  "Genome Explorer":
    "Browse curated genes and variant context",

  "Gene Mirror":
    "Reference vs. variant sequence comparison",

  "Protein Explorer":
    "Visualize the local protein environment",

  "XAI Lab":
    "Understand why the model produced its prediction",

  "AI Scientist":
    "Ask questions about your variant analysis",
};


// ============================================================
// Variant helpers
// ============================================================

const aminoAcidThreeToOne:
  Record<string, string> = {
    Ala: "A",
    Arg: "R",
    Asn: "N",
    Asp: "D",
    Cys: "C",
    Gln: "Q",
    Glu: "E",
    Gly: "G",
    His: "H",
    Ile: "I",
    Leu: "L",
    Lys: "K",
    Met: "M",
    Phe: "F",
    Pro: "P",
    Ser: "S",
    Thr: "T",
    Trp: "W",
    Tyr: "Y",
    Val: "V",
  };

const aminoAcidOneToName:
  Record<string, string> = {
    A: "Alanine",
    R: "Arginine",
    N: "Asparagine",
    D: "Aspartic acid",
    C: "Cysteine",
    Q: "Glutamine",
    E: "Glutamic acid",
    G: "Glycine",
    H: "Histidine",
    I: "Isoleucine",
    L: "Leucine",
    K: "Lysine",
    M: "Methionine",
    F: "Phenylalanine",
    P: "Proline",
    S: "Serine",
    T: "Threonine",
    W: "Tryptophan",
    Y: "Tyrosine",
    V: "Valine",
  };

function backendImpactToUi(
  impact: string | null,
): Impact {
  if (impact === "HIGH") {
    return "High";
  }

  if (
    impact === "MODERATE"
  ) {
    return "Moderate";
  }

  return "Low";
}

function buildVariantRequest(
  variant:
    (typeof variants)[number],
): VariantRequest {
  const dnaMatch =
    variant.dna.match(
      /(?:c\.)?(\d+)([ACGT])>([ACGT])/i,
    );

  if (!dnaMatch) {
    throw new Error(
      `Unable to parse DNA change: ${variant.dna}`,
    );
  }

  const proteinMatch =
    variant.protein.match(
      /(?:p\.)?([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})/,
    );

  if (!proteinMatch) {
    throw new Error(
      `Unable to parse protein change: ${variant.protein}`,
    );
  }

  const referenceAminoAcid =
    aminoAcidThreeToOne[
      proteinMatch[1]
    ];

  const alternateAminoAcid =
    aminoAcidThreeToOne[
      proteinMatch[3]
    ];

  if (
    !referenceAminoAcid ||
    !alternateAminoAcid
  ) {
    throw new Error(
      `Unsupported amino-acid change: ${variant.protein}`,
    );
  }

  const proteinPosition =
    Number(
      proteinMatch[2],
    );

    return {
      gene_symbol:
        variant.gene,
    
      chromosome:
        variant.chromosome,
    
      position:
        variant.position,
    
      reference_allele:
        dnaMatch[
          2
        ].toUpperCase(),
    
      alternate_allele:
        dnaMatch[
          3
        ].toUpperCase(),
    
      protein_position:
        proteinPosition,
    
      reference_amino_acid:
        referenceAminoAcid,
    
      alternate_amino_acid:
        alternateAminoAcid,
    
      dna_change:
        variant.dna,
    
      protein_change:
        `${referenceAminoAcid}${proteinPosition}${alternateAminoAcid}`,
    };
}

function parseVariantDisplay(
  variant:
    (typeof variants)[number],
) {
  const dnaMatch =
    variant.dna.match(
      /(?:c\.)?(\d+)([ACGT])>([ACGT])/i,
    );

  const proteinMatch =
    variant.protein.match(
      /(?:p\.)?([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})/,
    );

  const dnaPosition =
    dnaMatch
      ? dnaMatch[1]
      : "?";

  const referenceBase =
    dnaMatch
      ? dnaMatch[2].toUpperCase()
      : "?";

  const alternateBase =
    dnaMatch
      ? dnaMatch[3].toUpperCase()
      : "?";

  const referenceAa =
    proteinMatch
      ? aminoAcidThreeToOne[
          proteinMatch[1]
        ]
      : "?";

  const alternateAa =
    proteinMatch
      ? aminoAcidThreeToOne[
          proteinMatch[3]
        ]
      : "?";

  const proteinPosition =
    proteinMatch
      ? proteinMatch[2]
      : "?";

  return {
    dnaPosition,
    referenceBase,
    alternateBase,
    referenceAa,
    alternateAa,
    proteinPosition,
  };
}


// ============================================================
// Shared UI
// ============================================================

function StatusPill({
  impact,
}: {
  impact: Impact;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[10px] font-mono font-medium ${impactStyles[impact]}`}
    >
      <span className="size-1.5 rounded-full bg-current" />

      {impact}
    </span>
  );
}


function ProgressBar({
  value,
  tone = "bg-cyan",
}: {
  value: number;
  tone?: string;
}) {
  const safeValue =
    Math.max(
      0,
      Math.min(
        100,
        value,
      ),
    );

  return (
    <div className="h-2 overflow-hidden rounded-full bg-foreground/5">
      <div
        className={`gm-grow h-full rounded-full ${tone}`}
        style={{
          width:
            `${safeValue}%`,
        }}
      />
    </div>
  );
}


function MetricCard({
  label,
  value,
  detail,
  tone = "bg-cyan",
  icon: Icon = Activity,
}: {
  label: string;
  value: string;
  detail: string;
  tone?: string;
  icon?: typeof Activity;
}) {
  return (
    <div className="glass-panel rounded-2xl p-4 transition-transform duration-300 hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
          {label}
        </p>

        <Icon className="size-4 text-cyan/70" />
      </div>

      <p className="mt-3 text-3xl font-bold tracking-tight text-foreground">
        {value}
      </p>

      <div className="mt-3 flex items-center gap-2">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-foreground/5">
          <div
            className={`gm-grow h-full rounded-full ${tone}`}
            style={{
              width:
                detail,
            }}
          />
        </div>

        <span className="font-mono text-[10px] text-muted-foreground">
          {detail}
        </span>
      </div>
    </div>
  );
}


function PageHeader({
  page,
  eyebrow,
  activeTrace = "TP53 / c.743G>A",
}: {
  page: Page;
  eyebrow?: string;
  activeTrace?: string;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.25em] text-cyan">
          {eyebrow ??
            "Research Console"}
        </p>

        <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
          {page}
        </h2>

        <p className="mt-1.5 text-sm text-muted-foreground">
          {
            pageSubtitles[
              page
            ]
          }
        </p>
      </div>

      <div className="text-right">
        <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
          Active trace
        </p>

        <p className="mt-1 font-mono text-xs text-cyan">
          {activeTrace}
        </p>
      </div>
    </div>
  );
}


function SequenceStrip({
  sequence,
  highlight,
  tone,
}: {
  sequence: string[];
  highlight: number;
  tone:
    | "reference"
    | "variant";
}) {
  return (
    <div className="flex flex-wrap gap-1.5 font-mono text-sm">
      {sequence.map(
        (
          base,
          index,
        ) => (
          <span
            key={`${base}-${index}`}
            className={`grid size-8 place-items-center rounded-md transition-all ${
              index ===
              highlight
                ? tone ===
                  "reference"
                  ? "border border-cyan/60 bg-cyan/20 text-cyan shadow-[0_0_18px_color-mix(in_oklab,var(--color-cyan)_35%,transparent)]"
                  : "border border-danger/60 bg-danger/20 text-danger shadow-[0_0_18px_color-mix(in_oklab,var(--color-danger)_35%,transparent)]"
                : "bg-foreground/5 text-foreground"
            }`}
          >
            {base}
          </span>
        ),
      )}
    </div>
  );
}


function MiniStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-foreground/5 bg-foreground/[0.04] p-3">
      <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
        {label}
      </p>

      <p className="mt-1 line-clamp-1 text-xs font-semibold">
        {value}
      </p>
    </div>
  );
}


function StatePanel({
  tone,
  title,
  message,
  icon: Icon = Info,
  actionLabel,
  onAction,
}: {
  tone:
    | "loading"
    | "error"
    | "empty";
  title: string;
  message: string;
  icon?: typeof Activity;
  actionLabel?: string;
  onAction?: () => void;
}) {
  const toneClasses = {
    loading:
      "border-cyan/20 bg-cyan/[0.04] text-cyan",
    error:
      "border-danger/25 bg-danger/[0.05] text-danger",
    empty:
      "border-foreground/10 bg-foreground/[0.025] text-muted-foreground",
  } as const;

  return (
    <section
      className={`glass-panel rounded-2xl border p-6 ${toneClasses[tone]}`}
    >
      <div className="flex flex-col items-center text-center">
        <div
          className={`grid size-11 place-items-center rounded-xl border border-current/20 bg-current/[0.06] ${
            tone === "loading"
              ? "animate-pulse"
              : ""
          }`}
        >
          <Icon className="size-5" />
        </div>

        <h3 className="mt-4 text-sm font-semibold text-foreground">
          {title}
        </h3>

        <p className="mt-2 max-w-2xl text-xs leading-relaxed text-muted-foreground">
          {message}
        </p>

        {actionLabel &&
          onAction && (
            <Button
              size="sm"
              className="mt-4 bg-cyan text-primary-foreground hover:bg-cyan/90"
              onClick={onAction}
            >
              {actionLabel}
            </Button>
          )}
      </div>
    </section>
  );
}


function ConfidenceBar({
  label,
  count,
  value,
  tone,
}: {
  label: string;
  count: string;
  value: number;
  tone: string;
}) {
  return (
    <div>
      <div className="mb-1 flex justify-between font-mono text-[10px] text-muted-foreground">
        <span>
          {label}
        </span>

        <span>
          {count}
        </span>
      </div>

      <ProgressBar
        value={value}
        tone={tone}
      />
    </div>
  );
}


// ============================================================
// Step 5 — Gene Mirror live backend integration
// ============================================================

function MirrorPage({
  selectedGene,
  selectedVariant,
  onGeneChange,
  onVariantChange,
  currentAnalysis,
  onAnalysisComplete,
}: {
  selectedGene: string;
  selectedVariant: string;
  onGeneChange: (
    value: string,
  ) => void;
  onVariantChange: (
    value: string,
  ) => void;
  currentAnalysis:
    UnifiedAnalysisResponse |
    null;
  onAnalysisComplete: (
    result:
      UnifiedAnalysisResponse,
  ) => void;
}) {
  const [
    loading,
    setLoading,
  ] =
    useState(false);

  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);

  const geneVariants =
    variants.filter(
      (variant) =>
        variant.gene ===
        selectedGene,
    );

  const activeVariant =
    geneVariants.find(
      (variant) =>
        variant.id ===
        selectedVariant,
    ) ??
    geneVariants[0] ??
    variants[0];

  if (!activeVariant) {
    return null;
  }

  const display =
    parseVariantDisplay(
      activeVariant,
    );

  const analysisMatchesVariant =
    currentAnalysis?.variant
      ?.gene_symbol ===
      activeVariant.gene &&
    currentAnalysis?.variant
      ?.protein_change ===
      `${display.referenceAa}${display.proteinPosition}${display.alternateAa}`;

  const analysis =
    analysisMatchesVariant
      ? currentAnalysis
      : null;

  const impact =
    analysis
      ? backendImpactToUi(
          analysis
            .prediction
            .impact_class,
        )
      : null;

  const rawScore =
    analysis
      ? analysis
          .prediction
          .raw_model_score
      : null;

  const calibratedProbability =
    analysis
      ? analysis
          .prediction
          .calibrated_probability
      : null;

  const confidence =
    analysis
      ? analysis
          .prediction
          .confidence_score
      : null;

  const uncertainty =
    analysis
      ? analysis
          .prediction
          .uncertainty_score
      : null;

  const handleAnalyze =
    async () => {
      setLoading(
        true,
      );

      setError(
        null,
      );

      try {
        const request =
          buildVariantRequest(
            activeVariant,
          );

        const result =
          await analyzeVariant(
            request,
          );

        onAnalysisComplete(
          result,
        );
      } catch (caughtError) {
        if (
          caughtError instanceof
          ApiError
        ) {
          setError(
            caughtError.message,
          );
        } else if (
          caughtError instanceof
          Error
        ) {
          setError(
            caughtError.message,
          );
        } else {
          setError(
            "Unable to analyze this variant.",
          );
        }
      } finally {
        setLoading(
          false,
        );
      }
    };

  const handleGeneSelection =
    (
      gene:
        string,
    ) => {
      onGeneChange(
        gene,
      );

      const firstVariant =
        variants.find(
          (variant) =>
            variant.gene ===
            gene,
        );

      if (
        firstVariant
      ) {
        onVariantChange(
          firstVariant.id,
        );
      }

      setError(
        null,
      );
    };

  const referenceName =
    aminoAcidOneToName[
      display.referenceAa
    ] ??
    display.referenceAa;

  const alternateName =
    aminoAcidOneToName[
      display.alternateAa
    ] ??
    display.alternateAa;

  const activeTrace =
    `${activeVariant.gene} / ${activeVariant.dna}`;

  return (
    <div className="space-y-6">
      <PageHeader
        page="Gene Mirror"
        eyebrow="Flagship analysis"
        activeTrace={
          activeTrace
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2">
          <span className="font-mono text-[10px] tracking-[0.18em] text-muted-foreground">
            GENE
          </span>

          <select
            disabled={
              loading
            }
            value={
              selectedGene
            }
            onChange={(
              event,
            ) =>
              handleGeneSelection(
                event.target
                  .value,
              )
            }
            className="rounded-lg border border-cyan/25 bg-foreground/5 px-3 py-2 text-sm font-semibold text-foreground outline-none"
          >
            {genes.map(
              (
                gene,
              ) => (
                <option
                  key={
                    gene.symbol
                  }
                  value={
                    gene.symbol
                  }
                  className="bg-ink-2"
                >
                  {
                    gene.symbol
                  }
                </option>
              ),
            )}
          </select>
        </label>

        <label className="flex items-center gap-2">
          <span className="font-mono text-[10px] tracking-[0.18em] text-muted-foreground">
            VARIANT
          </span>

          <select
            disabled={
              loading
            }
            value={
              activeVariant.id
            }
            onChange={(
              event,
            ) => {
              onVariantChange(
                event.target
                  .value,
              );

              setError(
                null,
              );
            }}
            className="rounded-lg border border-cyan/25 bg-foreground/5 px-3 py-2 font-mono text-sm text-foreground outline-none"
          >
            {geneVariants.map(
              (
                variant,
              ) => (
                <option
                  key={
                    variant.id
                  }
                  value={
                    variant.id
                  }
                  className="bg-ink-2"
                >
                  {
                    variant.dna
                  }{" "}
                  ·{" "}
                  {
                    variant.protein
                  }
                </option>
              ),
            )}
          </select>
        </label>

        <Button
          className="bg-cyan text-primary-foreground hover:bg-cyan/90"
          disabled={
            loading
          }
          onClick={
            handleAnalyze
          }
        >
          {loading
            ? "Analyzing..."
            : analysis
              ? "Re-analyze Variant"
              : "Analyze Variant"}

          <BrainCircuit />
        </Button>

        <span className="ml-auto font-mono text-[11px] text-muted-foreground">
          {
            activeVariant.gene
          }{" "}
          ·{" "}
          {
            activeVariant.type
          }
        </span>
      </div>

      {loading && (
        <StatePanel
          tone="loading"
          icon={BrainCircuit}
          title="Running unified analysis"
          message={`GeneMirror is analyzing ${activeVariant.gene} ${activeVariant.protein}. Prediction, calibration, XAI, protein context, and Scientist output are being generated.`}
        />
      )}

      {error && (
        <StatePanel
          tone="error"
          icon={CircleHelp}
          title="Analysis failed"
          message={error}
          actionLabel="Retry analysis"
          onAction={handleAnalyze}
        />
      )}

      <section className="glass-panel relative overflow-hidden rounded-2xl p-5">
        <div className="pointer-events-none absolute -left-20 -top-20 size-72 rounded-full bg-cyan/10 blur-3xl gm-float" />

        <div className="pointer-events-none absolute -bottom-32 right-1/4 size-80 rounded-full bg-danger/10 blur-3xl gm-float-slow" />

        <div className="relative grid grid-cols-1 items-stretch gap-4 lg:grid-cols-[1fr_auto_1fr]">
          <div className="rounded-xl border border-cyan/25 bg-ink-2/60 p-5">
            <div className="mb-4 flex items-center justify-between">
              <p className="font-mono text-[11px] tracking-[0.2em] text-cyan">
                REFERENCE
              </p>

              <span className="rounded-full border border-cyan/30 bg-cyan/10 px-2 py-1 font-mono text-[10px] text-cyan">
                Reference
              </span>
            </div>

            <p className="mb-2 font-mono text-[11px] text-muted-foreground">
              DNA · position{" "}
              {
                display.dnaPosition
              }
            </p>

            <SequenceStrip
              sequence={
                dnaReference
              }
              highlight={4}
              tone="reference"
            />

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-foreground/5 bg-foreground/[0.04] p-3">
                <p className="font-mono text-[10px] text-muted-foreground">
                  PROTEIN
                </p>

                <p className="mt-1 text-sm font-semibold">
                  {
                    referenceName
                  }{" "}
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {
                      display.referenceAa
                    }
                    {
                      display.proteinPosition
                    }
                  </span>
                </p>
              </div>

              <div className="rounded-lg border border-foreground/5 bg-foreground/[0.04] p-3">
                <p className="font-mono text-[10px] text-muted-foreground">
                  DNA BASE
                </p>

                <p className="mt-1 font-mono text-sm font-semibold text-cyan">
                  {
                    display.referenceBase
                  }
                </p>
              </div>
            </div>
          </div>

          <div className="hidden flex-col items-center justify-center gap-3 px-1 md:flex">
            <span className="font-mono text-[10px] tracking-[0.2em] text-muted-foreground">
              REF → VAR
            </span>

            <div className="relative grid size-16 place-items-center rounded-2xl border border-cyan/30 bg-gradient-to-br from-cyan/20 to-violet/20 shadow-[0_0_35px_color-mix(in_oklab,var(--color-violet)_28%,transparent)]">
              <span className="font-mono text-[13px] font-bold">
                {
                  display.referenceBase
                }{" "}
                <span className="text-cyan">
                  →
                </span>{" "}
                {
                  display.alternateBase
                }
              </span>

              <span className="gm-pulse absolute inset-0 rounded-2xl ring-1 ring-cyan/30" />
            </div>

            <span className="font-mono text-[10px] text-cyan">
              missense
            </span>
          </div>

          <div className="rounded-xl border border-danger/25 bg-ink-2/60 p-5">
            <div className="mb-4 flex items-center justify-between">
              <p className="font-mono text-[11px] tracking-[0.2em] text-danger">
                VARIANT
              </p>

              {analysis ? (
                <StatusPill
                  impact={
                    impact
                  }
                />
              ) : (
                <span className="rounded-full border border-foreground/10 bg-foreground/5 px-2 py-1 font-mono text-[10px] text-muted-foreground">
                  Not analyzed
                </span>
              )}
            </div>

            <p className="mb-2 font-mono text-[11px] text-muted-foreground">
              DNA ·{" "}
              {
                activeVariant.dna
              }
            </p>

            <SequenceStrip
              sequence={
                dnaVariant
              }
              highlight={4}
              tone="variant"
            />

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-foreground/5 bg-foreground/[0.04] p-3">
                <p className="font-mono text-[10px] text-muted-foreground">
                  PROTEIN
                </p>

                <p className="mt-1 text-sm font-semibold">
                  {
                    alternateName
                  }{" "}
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {
                      display.alternateAa
                    }
                    {
                      display.proteinPosition
                    }
                  </span>
                </p>
              </div>

              <div className="rounded-lg border border-foreground/5 bg-foreground/[0.04] p-3">
                <p className="font-mono text-[10px] text-muted-foreground">
                  RAW MODEL
                  SCORE
                </p>

                <p className="mt-1 font-mono text-sm font-semibold text-danger">
                  {rawScore !==
                  null
                    ? rawScore.toFixed(
                        3,
                      )
                    : "—"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {analysis ? (
        <>
          <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="glass-panel rounded-2xl p-5">
              <p className="font-mono text-[11px] tracking-[0.2em] text-muted-foreground">
                CALIBRATED MODEL
                PROBABILITY
              </p>

              <div className="mt-4 flex items-end gap-2">
                <span
                  className={`text-5xl font-extrabold tracking-tighter ${
                    impact ===
                    "High"
                      ? "text-danger"
                      : impact ===
                          "Moderate"
                        ? "text-amber"
                        : "text-mint"
                  }`}
                >
                  {calibratedProbability !==
                  null
                    ? (
                        calibratedProbability *
                        100
                      ).toFixed(
                        1,
                      )
                    : "N/A"}
                </span>

                {calibratedProbability !==
                  null && (
                  <span className="mb-2 font-mono text-sm text-muted-foreground">
                    %
                  </span>
                )}
              </div>

              <div className="mt-4">
                <ProgressBar
                  value={
                    calibratedProbability !==
                    null
                      ? calibratedProbability *
                        100
                      : 0
                  }
                  tone={
                    impact ===
                    "High"
                      ? "bg-danger"
                      : impact ===
                          "Moderate"
                        ? "bg-amber"
                        : "bg-mint"
                  }
                />
              </div>

              <div className="mt-3 flex items-center gap-2">
                <span
                  className={`gm-pulse size-1.5 rounded-full ${
                    impact ===
                    "High"
                      ? "bg-danger"
                      : impact ===
                          "Moderate"
                        ? "bg-amber"
                        : "bg-mint"
                  }`}
                />

                <span className="text-xs font-semibold">
                  {impact}{" "}
                  Predicted
                  Impact
                </span>
              </div>
            </div>

            <div className="glass-panel rounded-2xl p-5 lg:col-span-2">
              <p className="mb-4 font-mono text-[11px] tracking-[0.2em] text-muted-foreground">
                LIVE MODEL OUTPUT
              </p>

              <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                <MiniStat
                  label="Raw model score"
                  value={
                    rawScore !==
                    null
                      ? rawScore.toFixed(
                          3,
                        )
                      : "N/A"
                  }
                />

                <MiniStat
                  label="Calibrated probability"
                  value={
                    calibratedProbability !==
                    null
                      ? `${(
                          calibratedProbability *
                          100
                        ).toFixed(
                          1,
                        )}%`
                      : "N/A"
                  }
                />

                <MiniStat
                  label="Confidence"
                  value={
                    confidence !==
                    null
                      ? `${(
                          confidence *
                          100
                        ).toFixed(
                          1,
                        )}%`
                      : "N/A"
                  }
                />

                <MiniStat
                  label="Uncertainty"
                  value={
                    uncertainty !==
                    null
                      ? `${(
                          uncertainty *
                          100
                        ).toFixed(
                          1,
                        )}%`
                      : "N/A"
                  }
                />

                <MiniStat
                  label="Confidence band"
                  value={
                    analysis
                      .prediction
                      .confidence_band ??
                    "N/A"
                  }
                />

                <MiniStat
                  label="Predicted class"
                  value={
                    analysis
                      .prediction
                      .predicted_class_name
                  }
                />
              </div>
            </div>
          </section>

          <section className="glass-panel rounded-2xl p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
                  Verified backend
                  context
                </p>

                <h3 className="mt-2 text-lg font-bold">
                  {
                    analysis
                      .variant
                      .gene_symbol
                  }{" "}
                  ·{" "}
                  {
                    analysis
                      .variant
                      .protein_change
                  }
                </h3>
              </div>

              <StatusPill
                impact={
                  impact
                }
              />
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
              <MiniStat
                label="Protein accession"
                value={
                  analysis
                    .protein_context
                    .protein
                    .accession
                }
              />

              <MiniStat
                label="Protein position"
                value={`${analysis.variant.protein_position}`}
              />

              <MiniStat
                label="XAI features"
                value={`${analysis.xai.explanation.feature_count}`}
              />

              <MiniStat
                label="Scientist provider"
                value={
                  analysis
                    .scientist
                    .execution
                    .provider_used
                }
              />
            </div>

            <div className="mt-5 rounded-xl border border-amber/20 bg-amber/[0.05] p-4">
              <div className="flex items-start gap-3">
                <Info className="mt-0.5 size-4 shrink-0 text-amber" />

                <p className="text-xs leading-relaxed text-muted-foreground">
                  {
                    analysis.disclaimer
                  }
                </p>
              </div>
            </div>
          </section>
        </>
      ) : (
        <StatePanel
          tone="empty"
          icon={BrainCircuit}
          title="No live prediction loaded"
          message="Choose a curated missense variant and click Analyze Variant to run the GeneMirror FastAPI analysis pipeline."
        />
      )}

      <p className="flex items-center justify-center gap-2 text-center font-mono text-[11px] text-muted-foreground">
        <Info className="size-3.5" />

        Computational
        prediction only —
        not a clinical
        diagnosis.
      </p>
    </div>
  );
}


// ============================================================
// Overview
// ============================================================

function OverviewPage({
  onNavigate,
}: {
  onNavigate: (
    page: Page,
  ) => void;
}) {
  return (
    <div className="space-y-6">
      <PageHeader
        page="Overview"
        eyebrow="GeneMirror AI"
      />

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <MetricCard
          label="Genes Available"
          value="12"
          detail="75%"
          tone="bg-cyan"
          icon={Dna}
        />

        <MetricCard
          label="Curated Variants"
          value="248"
          detail="88%"
          tone="bg-dna"
          icon={Layers3}
        />

        <MetricCard
          label="Variants Analyzed"
          value="1,372"
          detail="64%"
          tone="bg-violet"
          icon={Activity}
        />

        <MetricCard
          label="Average Confidence"
          value="87.4%"
          detail="stable"
          tone="bg-mint"
          icon={Gauge}
        />
      </div>

      <section className="glass-panel rounded-2xl p-5">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h3 className="font-semibold tracking-tight">
              Variant Analysis
              Pipeline
            </h3>

            <p className="mt-1 font-mono text-[11px] text-muted-foreground">
              Five-stage signal
              trace · TP53 /
              c.743G&gt;A
            </p>
          </div>

          <span className="font-mono text-[10px] text-cyan">
            TRACE COMPLETE
          </span>
        </div>

        <div className="relative">
          <div className="absolute left-0 right-0 top-1/2 hidden h-px bg-gradient-to-r from-cyan/30 via-violet/30 to-danger/30 md:block" />

          <div className="relative grid grid-cols-1 gap-3 md:grid-cols-5">
            {[
              {
                label:
                  "DNA Variant",
                detail:
                  "G>A @743",
                icon: Dna,
                tone:
                  "text-cyan",
              },
              {
                label:
                  "Sequence Analysis",
                detail:
                  "align · 99.2%",
                icon: Network,
                tone:
                  "text-dna",
              },
              {
                label:
                  "Protein Context",
                detail:
                  "Arg248His",
                icon:
                  Microscope,
                tone:
                  "text-violet",
              },
              {
                label:
                  "AI Prediction",
                detail:
                  "live model",
                icon:
                  BrainCircuit,
                tone:
                  "text-amber",
              },
              {
                label:
                  "XAI Explanation",
                detail:
                  "feature trace",
                icon:
                  Sparkles,
                tone:
                  "text-mint",
              },
            ].map(
              (
                stage,
                index,
              ) => (
                <div
                  key={
                    stage.label
                  }
                  className="glass-panel rounded-xl p-3 transition-transform hover:-translate-y-1"
                >
                  <div
                    className={`mb-3 flex size-7 items-center justify-center rounded-full bg-foreground/5 ring-1 ring-current/25 ${stage.tone}`}
                  >
                    <stage.icon className="size-3.5" />
                  </div>

                  <p className="text-xs font-semibold">
                    {
                      stage.label
                    }
                  </p>

                  <p className="mt-1 font-mono text-[10px] text-muted-foreground">
                    {
                      stage.detail
                    }
                  </p>

                  <p className="mt-3 font-mono text-[9px] text-cyan/70">
                    0
                    {index +
                      1}{" "}
                    / READY
                  </p>
                </div>
              ),
            )}
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_320px]">
        <section className="glass-panel overflow-hidden rounded-2xl">
          <div className="flex items-center justify-between p-5">
            <div>
              <h3 className="font-semibold tracking-tight">
                Recent
                Analyses
              </h3>

              <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                Latest
                resolved
                traces
              </p>
            </div>

            <Button
              variant="ghost"
              size="sm"
              className="text-cyan hover:bg-cyan/10 hover:text-cyan"
              onClick={() =>
                onNavigate(
                  "Genome Explorer",
                )
              }
            >
              Explore data
              <ArrowRight />
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px] text-left text-xs">
              <thead className="border-y border-foreground/5 bg-foreground/[0.02] font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-5 py-3 font-medium">
                    Gene
                  </th>

                  <th className="px-3 py-3 font-medium">
                    Variant
                  </th>

                  <th className="px-3 py-3 font-medium">
                    Protein Change
                  </th>

                  <th className="px-3 py-3 font-medium">
                    Impact
                  </th>

                  <th className="px-3 py-3 text-right font-medium">
                    Conf.
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-foreground/5">
                {recentAnalyses.map(
                  (
                    row,
                  ) => (
                    <tr
                      key={`${row.gene}-${row.variant}`}
                      className="transition-colors hover:bg-cyan/[0.04]"
                    >
                      <td className="px-5 py-3 font-mono font-semibold">
                        {
                          row.gene
                        }
                      </td>

                      <td className="px-3 py-3 font-mono text-muted-foreground">
                        {
                          row.variant
                        }
                      </td>

                      <td className="px-3 py-3 font-mono text-muted-foreground">
                        {
                          row.protein
                        }
                      </td>

                      <td className="px-3 py-3">
                        <StatusPill
                          impact={
                            row.impact
                          }
                        />
                      </td>

                      <td className="px-3 py-3 text-right font-mono text-cyan">
                        {
                          row.confidence
                        }
                        %
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="space-y-6">
          <div className="glass-panel rounded-2xl p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-mono text-[10px] tracking-[0.18em] text-muted-foreground">
                  MODEL
                  CONFIDENCE
                </p>

                <p className="mt-1 text-sm font-semibold">
                  Distribution
                </p>
              </div>

              <Gauge className="size-4 text-violet" />
            </div>

            <div className="mt-5 space-y-4">
              <ConfidenceBar
                label="Low"
                count="212"
                value={31}
                tone="bg-mint"
              />

              <ConfidenceBar
                label="Moderate"
                count="588"
                value={55}
                tone="bg-amber"
              />

              <ConfidenceBar
                label="High"
                count="572"
                value={84}
                tone="bg-danger"
              />
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-5">
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted-foreground">
              NEXT
              SUGGESTED VIEW
            </p>

            <p className="mt-2 text-sm font-semibold">
              Open the
              flagship Gene
              Mirror
            </p>

            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              Compare
              sequence context
              and inspect
              the live backend
              prediction.
            </p>

            <Button
              className="mt-4 w-full bg-cyan text-primary-foreground hover:bg-cyan/90"
              onClick={() =>
                onNavigate(
                  "Gene Mirror",
                )
              }
            >
              Open Gene Mirror
              <GitCompareArrows />
            </Button>
          </div>
        </aside>
      </div>

      <p className="text-center font-mono text-[10px] text-muted-foreground">
        GeneMirror AI
        provides
        computational
        predictions for
        research and
        educational
        purposes and is
        not a diagnostic
        or clinical
        decision-making
        system.
      </p>
    </div>
  );
}


// ============================================================
// Genome Explorer
// ============================================================

function ExplorerPage({
  onOpenMirror,
  onAnalysisComplete,
}: {
  onOpenMirror: (
    gene: string,
  ) => void;
  onAnalysisComplete: (
    result:
      UnifiedAnalysisResponse,
  ) => void;
}) {
  const [
    query,
    setQuery,
  ] =
    useState("");

  const [
    category,
    setCategory,
  ] =
    useState(
      "All categories",
    );

  const [
    selected,
    setSelected,
  ] =
    useState<Gene>(
      genes[0] as Gene,
    );

  const [
    analysisByVariant,
    setAnalysisByVariant,
  ] =
    useState<
      Record<
        string,
        UnifiedAnalysisResponse
      >
    >({});

  const [
    loadingVariantId,
    setLoadingVariantId,
  ] =
    useState<
      string | null
    >(null);

  const [
    analysisError,
    setAnalysisError,
  ] =
    useState<
      string | null
    >(null);

  const [
    activeAnalysisId,
    setActiveAnalysisId,
  ] =
    useState<
      string | null
    >(null);

  const filtered =
    genes.filter(
      (gene) =>
        `${gene.symbol} ${gene.name}`
          .toLowerCase()
          .includes(
            query.toLowerCase(),
          ) &&
        (
          category ===
            "All categories" ||
          gene.category ===
            category
        ),
    );

  const selectedVariants =
    variants
      .filter(
        (variant) =>
          variant.gene ===
          selected.symbol,
      )
      .slice(
        0,
        4,
      );

  const activeAnalysis =
    activeAnalysisId
      ? analysisByVariant[
          activeAnalysisId
        ]
      : undefined;

  const failedVariant =
    activeAnalysisId
      ? selectedVariants.find(
          (variant) =>
            variant.id ===
            activeAnalysisId,
        )
      : undefined;

  const handleAnalyze =
    async (
      variant:
        (typeof variants)[number],
    ) => {
      setLoadingVariantId(
        variant.id,
      );

      setAnalysisError(
        null,
      );

      setActiveAnalysisId(
        variant.id,
      );

      try {
        const request =
          buildVariantRequest(
            variant,
          );

        const result =
          await analyzeVariant(
            request,
          );

        setAnalysisByVariant(
          (current) => ({
            ...current,
            [variant.id]:
              result,
          }),
        );

        onAnalysisComplete(
          result,
        );
      } catch (error) {
        if (
          error instanceof
          ApiError
        ) {
          setAnalysisError(
            error.message,
          );
        } else if (
          error instanceof
          Error
        ) {
          setAnalysisError(
            error.message,
          );
        } else {
          setAnalysisError(
            "Unable to analyze this variant.",
          );
        }
      } finally {
        setLoadingVariantId(
          null,
        );
      }
    };

  return (
    <div className="space-y-6">
      <PageHeader
        page="Genome Explorer"
        eyebrow="Curated corpus"
      />

      <div className="flex flex-wrap gap-3">
        <label className="flex min-w-[260px] flex-1 items-center gap-2 rounded-lg border border-cyan/20 bg-foreground/5 px-3">
          <Search className="size-4 text-muted-foreground" />

          <input
            value={query}
            onChange={(
              event,
            ) =>
              setQuery(
                event.target
                  .value,
              )
            }
            placeholder="Search genes by symbol or name"
            className="h-10 flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
          />
        </label>

        <select
          value={
            category
          }
          onChange={(
            event,
          ) =>
            setCategory(
              event.target
                .value,
            )
          }
          className="rounded-lg border border-foreground/10 bg-foreground/5 px-3 text-sm text-foreground outline-none"
        >
          <option className="bg-ink-2">
            All categories
          </option>

          <option className="bg-ink-2">
            Tumor suppressor
          </option>

          <option className="bg-ink-2">
            DNA repair
          </option>

          <option className="bg-ink-2">
            Transport
          </option>

          <option className="bg-ink-2">
            Blood protein
          </option>

          <option className="bg-ink-2">
            Lipid transport
          </option>

          <option className="bg-ink-2">
            Metabolism
          </option>
        </select>

        <Button
          variant="outline"
          className="border-cyan/20 bg-foreground/5 text-cyan hover:bg-cyan/10 hover:text-cyan"
        >
          <SlidersHorizontal />
          Filters
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {filtered.map(
            (gene) => (
              <button
                key={
                  gene.symbol
                }
                onClick={() => {
                  setSelected(
                    gene,
                  );

                  setActiveAnalysisId(
                    null,
                  );

                  setAnalysisError(
                    null,
                  );
                }}
                className={`glass-panel rounded-xl p-4 text-left transition-all hover:-translate-y-0.5 hover:border-cyan/30 ${
                  selected.symbol ===
                  gene.symbol
                    ? "border-cyan/35 bg-cyan/[0.05]"
                    : ""
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-mono text-lg font-bold text-cyan">
                      {
                        gene.symbol
                      }
                    </span>

                    <p className="mt-1 text-xs font-medium">
                      {
                        gene.name
                      }
                    </p>
                  </div>

                  <span className="rounded-md border border-foreground/10 bg-foreground/5 px-2 py-1 font-mono text-[10px] text-muted-foreground">
                    {
                      gene.chromosome
                    }
                  </span>
                </div>

                <p className="mt-4 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                  {
                    gene.description
                  }
                </p>

                <div className="mt-4 flex items-center justify-between">
                  <span className="font-mono text-[10px] text-violet">
                    {
                      gene.variants
                    }{" "}
                    curated
                    variants
                  </span>

                  <span className="text-[11px] font-semibold text-cyan">
                    View gene

                    <ArrowRight className="ml-1 inline size-3" />
                  </span>
                </div>
              </button>
            ),
          )}
        </div>

        <aside className="glass-panel rounded-2xl p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
                Selected gene
              </p>

              <h3 className="mt-2 text-3xl font-extrabold tracking-tight">
                {
                  selected.symbol
                }
              </h3>

              <p className="mt-1 text-sm text-muted-foreground">
                {
                  selected.name
                }
              </p>
            </div>

            <Dna className="size-6 text-cyan" />
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3">
            <MiniStat
              label="Chromosome"
              value={
                selected.chromosome
              }
            />

            <MiniStat
              label="Sequence length"
              value={
                selected.length
              }
            />

            <MiniStat
              label="Protein"
              value={
                selected.protein
              }
            />

            <MiniStat
              label="Curated variants"
              value={`${selected.variants}`}
            />
          </div>

          <p className="mt-5 text-xs leading-relaxed text-muted-foreground">
            {
              selected.description
            }
          </p>

          <Button
            className="mt-5 w-full bg-cyan text-primary-foreground hover:bg-cyan/90"
            onClick={() =>
              onOpenMirror(
                selected.symbol,
              )
            }
          >
            Open in Gene
            Mirror
            <GitCompareArrows />
          </Button>
        </aside>
      </div>

      <section className="glass-panel overflow-hidden rounded-2xl">
        <div className="flex flex-wrap items-center justify-between gap-3 p-5">
          <div>
            <h3 className="font-semibold">
              Curated variant
              table
            </h3>

            <p className="mt-1 font-mono text-[11px] text-muted-foreground">
              {
                selected.symbol
              }{" "}
              · curated research
              annotations
            </p>
          </div>

          <span className="font-mono text-[10px] text-cyan">
            {
              selectedVariants.length
            }{" "}
            visible records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-xs">
            <thead className="border-y border-foreground/5 bg-foreground/[0.02] font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-5 py-3 font-medium">
                  Variant ID
                </th>

                <th className="px-3 py-3 font-medium">
                  DNA Change
                </th>

                <th className="px-3 py-3 font-medium">
                  Protein Change
                </th>

                <th className="px-3 py-3 font-medium">
                  Type
                </th>

                <th className="px-3 py-3 font-medium">
                  Impact
                </th>

                <th className="px-3 py-3 text-right font-medium">
                  Confidence
                </th>

                <th className="px-5 py-3 text-right font-medium">
                  Analysis
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-foreground/5">
              {selectedVariants.map(
                (variant) => {
                  const analysis =
                    analysisByVariant[
                      variant.id
                    ];

                  const impact =
                    analysis
                      ? backendImpactToUi(
                          analysis
                            .prediction
                            .impact_class,
                        )
                      : null;

                  const confidence =
                    analysis
                      ? Math.round(
                          (
                            analysis
                              .prediction
                              .confidence_score ??
                            0
                          ) *
                            100,
                        )
                      : null;

                  const isLoading =
                    loadingVariantId ===
                    variant.id;

                  return (
                    <tr
                      key={
                        variant.id
                      }
                      className="hover:bg-cyan/[0.04]"
                    >
                      <td className="px-5 py-3 font-mono text-cyan">
                        {
                          variant.id
                        }
                      </td>

                      <td className="px-3 py-3 font-mono">
                        {
                          variant.dna
                        }
                      </td>

                      <td className="px-3 py-3 font-mono text-muted-foreground">
                        {
                          variant.protein
                        }
                      </td>

                      <td className="px-3 py-3 text-muted-foreground">
                        {
                          variant.type
                        }
                      </td>

                      <td className="px-3 py-3">
                        {impact ? (
                          <StatusPill
                            impact={
                              impact
                            }
                          />
                        ) : (
                          <span className="font-mono text-[11px] text-muted-foreground">
                            Not analyzed
                          </span>
                        )}
                      </td>

                      <td className="px-3 py-3 text-right font-mono text-cyan">
                        {confidence !== null
                          ? `${confidence}%`
                          : "—"}
                      </td>

                      <td className="px-5 py-3 text-right">
                        <Button
                          size="sm"
                          variant={
                            analysis
                              ? "outline"
                              : "default"
                          }
                          disabled={
                            isLoading
                          }
                          className={
                            analysis
                              ? "border-mint/30 bg-mint/5 text-mint hover:bg-mint/10 hover:text-mint"
                              : "bg-cyan text-primary-foreground hover:bg-cyan/90"
                          }
                          onClick={() =>
                            handleAnalyze(
                              variant,
                            )
                          }
                        >
                          {isLoading
                            ? "Analyzing..."
                            : analysis
                              ? "Re-analyze"
                              : "Analyze"}
                        </Button>
                      </td>
                    </tr>
                  );
                },
              )}
            </tbody>
          </table>
        </div>
      </section>

      {loadingVariantId && (
        <StatePanel
          tone="loading"
          icon={BrainCircuit}
          title="Analyzing curated variant"
          message={`Running the unified GeneMirror pipeline for ${loadingVariantId}. Keep the backend running while the request completes.`}
        />
      )}

      {analysisError && (
        <StatePanel
          tone="error"
          icon={CircleHelp}
          title="Variant analysis failed"
          message={analysisError}
          actionLabel={
            failedVariant
              ? "Retry variant"
              : undefined
          }
          onAction={
            failedVariant
              ? () =>
                  handleAnalyze(
                    failedVariant,
                  )
              : undefined
          }
        />
      )}

      {activeAnalysis && (
        <section className="glass-panel rounded-2xl p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
                Live backend
                analysis
              </p>

              <h3 className="mt-2 text-xl font-bold">
                {
                  activeAnalysis
                    .variant
                    .gene_symbol
                }{" "}
                ·{" "}
                {
                  activeAnalysis
                    .variant
                    .protein_change
                }
              </h3>
            </div>

            <StatusPill
              impact={backendImpactToUi(
                activeAnalysis
                  .prediction
                  .impact_class,
              )}
            />
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
            <MiniStat
              label="Raw model score"
              value={
                activeAnalysis
                  .prediction
                  .raw_model_score
                  .toFixed(
                    3,
                  )
              }
            />

            <MiniStat
              label="Calibrated probability"
              value={
                activeAnalysis
                  .prediction
                  .calibrated_probability !==
                null
                  ? `${(
                      activeAnalysis
                        .prediction
                        .calibrated_probability *
                      100
                    ).toFixed(
                      1,
                    )}%`
                  : "N/A"
              }
            />

            <MiniStat
              label="Confidence"
              value={
                activeAnalysis
                  .prediction
                  .confidence_score !==
                null
                  ? `${(
                      activeAnalysis
                        .prediction
                        .confidence_score *
                      100
                    ).toFixed(
                      1,
                    )}%`
                  : "N/A"
              }
            />

            <MiniStat
              label="Confidence band"
              value={
                activeAnalysis
                  .prediction
                  .confidence_band ??
                "N/A"
              }
            />

            <MiniStat
              label="Protein"
              value={
                activeAnalysis
                  .protein_context
                  .protein
                  .accession
              }
            />

            <MiniStat
              label="Scientist"
              value={
                activeAnalysis
                  .scientist
                  .execution
                  .provider_used
              }
            />
          </div>

          <div className="mt-5 rounded-xl border border-amber/20 bg-amber/[0.05] p-4">
            <div className="flex items-start gap-3">
              <Info className="mt-0.5 size-4 shrink-0 text-amber" />

              <p className="text-xs leading-relaxed text-muted-foreground">
                {
                  activeAnalysis.disclaimer
                }
              </p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}


// ============================================================
// Protein Explorer — live backend integration
// ============================================================

function ProteinPage({
  currentAnalysis,
}: {
  currentAnalysis:
    | UnifiedAnalysisResponse
    | null;
}) {
  const [
    rotation,
    setRotation,
  ] =
    useState(0);

  const [
    highlight,
    setHighlight,
  ] =
    useState(true);

  if (!currentAnalysis) {
    return (
      <div className="space-y-6">
        <PageHeader
          page="Protein Explorer"
          eyebrow="Structure context"
        />

        <StatePanel
          tone="empty"
          icon={Microscope}
          title="No protein context loaded"
          message="Analyze a missense variant in Gene Mirror first. Protein Explorer will then display the UniProt-backed context returned for that same analysis."
        />

        <p className="text-center font-mono text-[10px] text-muted-foreground">
          Protein context is intended for computational research and educational use only.
        </p>
      </div>
    );
  }

  if (
    !currentAnalysis.protein_context ||
    !currentAnalysis.protein_context.protein ||
    !currentAnalysis.protein_context.sequence_context
  ) {
    return (
      <div className="space-y-6">
        <PageHeader
          page="Protein Explorer"
          eyebrow="Structure context"
        />

        <StatePanel
          tone="error"
          icon={CircleHelp}
          title="Protein context unavailable"
          message="The analysis completed, but the protein-context payload is incomplete. Re-analyze the variant and verify that the backend is running correctly."
        />
      </div>
    );
  }

  const proteinContext =
    currentAnalysis.protein_context;

  const protein =
    proteinContext.protein;

  const sequenceContext =
    proteinContext.sequence_context;

  const variantMarker =
    proteinContext.variant_marker;

  const overlappingFeatures =
    proteinContext.overlapping_features;

  const nearbyFeatures =
    proteinContext.nearby_features;

  const tracks =
    proteinContext.visualization_tracks;

  const activeTrace =
    `${
      currentAnalysis.variant
        .gene_symbol
    } / ${
      currentAnalysis.variant
        .protein_change ??
      "Variant"
    }`;

  const formatFeatureType = (
    value: string,
  ) =>
    value
      .replace(/_/g, " ")
      .replace(/\b\w/g, (character) =>
        character.toUpperCase(),
      );

  return (
    <div className="space-y-6">
      <PageHeader
        page="Protein Explorer"
        eyebrow="Protein context"
        activeTrace={
          activeTrace
        }
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
        <section className="glass-panel relative min-h-[460px] overflow-hidden rounded-2xl bg-ink-2/70 p-6">
          <div className="pointer-events-none absolute inset-0 gm-grid opacity-50" />

          <div className="relative flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-cyan">
                PROTEIN CONTEXT
              </p>

              <h3 className="mt-2 text-xl font-bold">
                {
                  protein.protein_name
                }
              </h3>

              <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                {
                  protein.accession
                }{" "}
                ·{" "}
                {
                  protein.sequence_length
                }{" "}
                aa
              </p>
            </div>

            <span className="rounded-full border border-mint/30 bg-mint/10 px-2.5 py-1 font-mono text-[10px] text-mint">
              LIVE BACKEND DATA
            </span>
          </div>

          <div
            className="relative mx-auto mt-8 flex h-[300px] max-w-[620px] items-center justify-center"
            style={{
              transform:
                `rotate(${rotation}deg)`,
            }}
          >
            <div className="absolute h-40 w-[82%] rotate-12 rounded-[48%] border-2 border-cyan/40 shadow-[0_0_45px_color-mix(in_oklab,var(--color-cyan)_18%,transparent)]" />

            <div className="absolute h-32 w-[66%] -rotate-12 rounded-[48%] border-2 border-violet/50 shadow-[0_0_42px_color-mix(in_oklab,var(--color-violet)_22%,transparent)]" />

            <div className="absolute h-24 w-[48%] rotate-45 rounded-[48%] border-2 border-dna/50" />

            {highlight && (
              <div className="absolute -translate-x-24 -translate-y-12 size-5 rounded-full border-2 border-danger bg-danger/30 shadow-[0_0_28px_color-mix(in_oklab,var(--color-danger)_50%,transparent)]" />
            )}

            <div className="absolute translate-x-24 translate-y-14 size-3 rounded-full bg-cyan gm-pulse" />

            <div className="absolute -translate-x-40 translate-y-20 size-2 rounded-full bg-violet gm-pulse" />

            <div className="absolute translate-x-40 -translate-y-20 size-2 rounded-full bg-mint gm-pulse" />
          </div>

          <div className="relative flex flex-wrap justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="border-cyan/20 bg-foreground/5 text-cyan hover:bg-cyan/10 hover:text-cyan"
              onClick={() =>
                setRotation(
                  (
                    value,
                  ) =>
                    value +
                    45,
                )
              }
            >
              <RotateCcw />
              Rotate
            </Button>

            <Button
              variant="outline"
              size="sm"
              className="border-cyan/20 bg-foreground/5 text-cyan hover:bg-cyan/10 hover:text-cyan"
              onClick={() =>
                setRotation(
                  (
                    value,
                  ) =>
                    value +
                    90,
                )
              }
            >
              <ZoomIn />
              Zoom
            </Button>

            <Button
              variant="outline"
              size="sm"
              className="border-cyan/20 bg-foreground/5 text-cyan hover:bg-cyan/10 hover:text-cyan"
              onClick={() =>
                setRotation(
                  0,
                )
              }
            >
              <RotateCcw />
              Reset View
            </Button>

            <Button
              variant={
                highlight
                  ? "default"
                  : "outline"
              }
              size="sm"
              className={
                highlight
                  ? "bg-danger text-danger-foreground hover:bg-danger/90"
                  : "border-cyan/20 bg-foreground/5 text-cyan hover:bg-cyan/10 hover:text-cyan"
              }
              onClick={() =>
                setHighlight(
                  (
                    value,
                  ) =>
                    !value,
                )
              }
            >
              <Target />

              {highlight
                ? "Variant Highlighted"
                : "Highlight Variant"}
            </Button>
          </div>

          <div className="relative mt-6 rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
              Sequence window
            </p>

            <p className="mt-3 break-all font-mono text-sm tracking-[0.15em] text-foreground">
              {
                sequenceContext.sequence_window
              }
            </p>

            <div className="mt-3 flex flex-wrap gap-3 font-mono text-[10px] text-muted-foreground">
              <span>
                Window:{" "}
                {
                  sequenceContext.window_start
                }
                –
                {
                  sequenceContext.window_end
                }
              </span>

              <span>
                Variant position:{" "}
                {
                  sequenceContext.protein_position
                }
              </span>
            </div>
          </div>
        </section>

        <aside className="space-y-4">
          <div className="glass-panel rounded-2xl p-5">
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
              Protein information
            </p>

            <div className="mt-4 space-y-3">
              <InfoLine
                label="Protein name"
                value={
                  protein.protein_name
                }
              />

              <InfoLine
                label="Gene"
                value={
                  protein.gene_symbol
                }
              />

              <InfoLine
                label="Accession"
                value={
                  protein.accession
                }
              />

              <InfoLine
                label="Protein length"
                value={`${protein.sequence_length} aa`}
              />

              <InfoLine
                label="Variant position"
                value={`${sequenceContext.protein_position}`}
              />

              <InfoLine
                label="Amino acid change"
                value={
                  variantMarker.label
                }
                tone="text-danger"
              />

              <InfoLine
                label="Reviewed"
                value={
                  protein.reviewed
                    ? "Yes"
                    : "No"
                }
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <MiniStat
              label="Reference AA"
              value={
                sequenceContext.reference_amino_acid
              }
            />

            <MiniStat
              label="Alternate AA"
              value={
                sequenceContext.alternate_amino_acid
              }
            />

            <MiniStat
              label="Sequence AA"
              value={
                sequenceContext.sequence_reference_amino_acid
              }
            />

            <MiniStat
              label="Reference match"
              value={
                sequenceContext.position_matches_reference
                  ? "Yes"
                  : "No"
              }
            />
          </div>
        </aside>
      </div>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="glass-panel rounded-2xl p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-danger">
                Overlapping features
              </p>

              <h3 className="mt-2 text-lg font-bold">
                Features at the variant site
              </h3>
            </div>

            <span className="font-mono text-xl font-bold text-danger">
              {
                overlappingFeatures.length
              }
            </span>
          </div>

          <div className="mt-4 space-y-3">
            {overlappingFeatures.length >
            0 ? (
              overlappingFeatures.map(
                (
                  feature,
                  index,
                ) => (
                  <div
                    key={`${feature.feature_type}-${feature.start}-${feature.end}-${index}`}
                    className="rounded-xl border border-danger/10 bg-danger/[0.03] p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-sm font-semibold">
                        {formatFeatureType(
                          feature.feature_type,
                        )}
                      </p>

                      <span className="font-mono text-[10px] text-danger">
                        {
                          feature.start
                        }
                        –
                        {
                          feature.end
                        }
                      </span>
                    </div>

                    <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                      {
                        feature.description ??
                        "No description available."
                      }
                    </p>

                    <p className="mt-2 font-mono text-[10px] text-muted-foreground">
                      Distance to variant:{" "}
                      {
                        feature.distance_to_variant
                      }
                    </p>
                  </div>
                ),
              )
            ) : (
              <p className="text-sm text-muted-foreground">
                No overlapping UniProt
                features were returned for
                this variant.
              </p>
            )}
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-violet">
                Nearby features
              </p>

              <h3 className="mt-2 text-lg font-bold">
                Local protein context
              </h3>
            </div>

            <span className="font-mono text-xl font-bold text-violet">
              {
                nearbyFeatures.length
              }
            </span>
          </div>

          <div className="mt-4 space-y-3">
            {nearbyFeatures.length >
            0 ? (
              nearbyFeatures.map(
                (
                  feature,
                  index,
                ) => (
                  <div
                    key={`${feature.feature_type}-${feature.start}-${feature.end}-${index}`}
                    className="rounded-xl border border-violet/10 bg-violet/[0.03] p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-sm font-semibold">
                        {formatFeatureType(
                          feature.feature_type,
                        )}
                      </p>

                      <span className="font-mono text-[10px] text-violet">
                        {
                          feature.start
                        }
                        –
                        {
                          feature.end
                        }
                      </span>
                    </div>

                    <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                      {
                        feature.description ??
                        "No description available."
                      }
                    </p>

                    <p className="mt-2 font-mono text-[10px] text-muted-foreground">
                      Distance to variant:{" "}
                      {
                        feature.distance_to_variant
                      }
                    </p>
                  </div>
                ),
              )
            ) : (
              <p className="text-sm text-muted-foreground">
                No nearby UniProt features
                were returned.
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="glass-panel rounded-2xl p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
              Visualization tracks
            </p>

            <h3 className="mt-2 text-lg font-bold">
              Backend-generated protein
              feature tracks
            </h3>
          </div>

          <span className="font-mono text-2xl font-bold text-cyan">
            {
              tracks.length
            }
          </span>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {tracks.map(
            (
              track,
            ) => (
              <div
                key={
                  track.track_type
                }
                className="rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4"
              >
                <p className="text-sm font-semibold">
                  {
                    track.label
                  }
                </p>

                <p className="mt-1 font-mono text-[10px] text-muted-foreground">
                  {
                    track.track_type
                  }
                </p>

                <div className="mt-4">
                  <MiniStat
                    label="Features"
                    value={`${track.features.length}`}
                  />
                </div>
              </div>
            ),
          )}
        </div>
      </section>

      <section className="glass-panel rounded-2xl p-5">
        <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
          Protein interpretation
        </p>

        <p className="mt-4 text-sm leading-7 text-muted-foreground">
          {
            proteinContext.interpretation
          }
        </p>

        <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
          <MiniStat
            label="Protein version"
            value={
              proteinContext.protein_context_version
            }
          />

          <MiniStat
            label="Visualization version"
            value={
              proteinContext.visualization_version
            }
          />

          <MiniStat
            label="Overlapping features"
            value={`${overlappingFeatures.length}`}
          />

          <MiniStat
            label="Nearby features"
            value={`${nearbyFeatures.length}`}
          />
        </div>
      </section>

      <div className="rounded-2xl border border-amber/20 bg-amber/[0.04] p-4">
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 size-4 shrink-0 text-amber" />

          <p className="text-xs leading-relaxed text-muted-foreground">
            {
              proteinContext.disclaimer
            }
          </p>
        </div>
      </div>

      <p className="text-center font-mono text-[10px] text-muted-foreground">
        Protein context is derived from
        backend UniProt data and is not a
        clinical structural interpretation.
      </p>
    </div>
  );
}


function InfoLine({
  label,
  value,
  tone = "text-foreground",
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3 text-xs">
      <span className="text-muted-foreground">
        {label}
      </span>

      <span
        className={`text-right font-mono ${tone}`}
      >
        {value}
      </span>
    </div>
  );
}


// ============================================================
// Step 6 — XAI Lab live backend integration
// ============================================================

function XaiPage({
  currentAnalysis,
}: {
  currentAnalysis:
    | UnifiedAnalysisResponse
    | null;
}) {
  const formatFeatureName = (
    featureName: string,
  ) =>
    featureName
      .replace(/_/g, " ")
      .replace(/\b\w/g, (character) =>
        character.toUpperCase(),
      );

  if (!currentAnalysis) {
    return (
      <div className="space-y-6">
        <PageHeader
          page="XAI Lab"
          eyebrow="Model interpretability"
        />

        <StatePanel
          tone="empty"
          icon={BrainCircuit}
          title="No analysis loaded"
          message="Analyze a missense variant in Gene Mirror first. XAI Lab will then display the real feature-level explanation generated by the backend."
        />

        <p className="text-center font-mono text-[10px] text-muted-foreground">
          GeneMirror AI explanations are computational research outputs and are not clinical evidence.
        </p>
      </div>
    );
  }

  if (
    !currentAnalysis.xai ||
    !currentAnalysis.xai.result ||
    !currentAnalysis.xai.explanation
  ) {
    return (
      <div className="space-y-6">
        <PageHeader
          page="XAI Lab"
          eyebrow="Model interpretability"
        />

        <StatePanel
          tone="error"
          icon={CircleHelp}
          title="XAI explanation unavailable"
          message="The analysis completed, but the XAI payload is incomplete. Re-analyze the variant and verify the backend response before continuing."
        />
      </div>
    );
  }

  const xai =
    currentAnalysis.xai;

  const result =
    xai.result;

  const explanation =
    xai.explanation;

  const direction =
    explanation.direction_summary;

  const topFeatures =
    explanation.top_features.slice(
      0,
      5,
    );

  const impact =
    backendImpactToUi(
      result.impact_class,
    );

  const confidencePercent =
    result.confidence_score *
    100;

  const uncertaintyPercent =
    result.uncertainty_score *
    100;

  const calibratedPercent =
    result.calibrated_probability *
    100;

  const activeTrace =
    `${
      currentAnalysis.variant
        .gene_symbol
    } / ${
      currentAnalysis.variant
        .protein_change ??
      "Variant"
    }`;

  const impactTone =
    impact === "High"
      ? "text-danger"
      : impact === "Moderate"
        ? "text-amber"
        : "text-mint";

  return (
    <div className="space-y-6">
      <PageHeader
        page="XAI Lab"
        eyebrow="Model interpretability"
        activeTrace={
          activeTrace
        }
      />

      {/* ================================================== */}
      {/* Prediction overview */}
      {/* ================================================== */}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_0.9fr]">
        <section className="glass-panel rounded-2xl p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
                Prediction explanation
              </p>

              <div className="mt-3 flex items-center gap-3">
                <p className="text-3xl font-extrabold tracking-tight">
                  {
                    result.impact_class
                  }
                </p>

                <StatusPill
                  impact={
                    impact
                  }
                />
              </div>

              <p className="mt-2 font-mono text-[11px] text-muted-foreground">
                {
                  currentAnalysis
                    .variant
                    .gene_symbol
                }{" "}
                ·{" "}
                {
                  currentAnalysis
                    .variant
                    .protein_change
                }
              </p>
            </div>

            <div className="text-right">
              <p className="font-mono text-[10px] text-muted-foreground">
                MODEL CONFIDENCE
              </p>

              <p className="mt-1 text-3xl font-bold text-cyan">
                {confidencePercent.toFixed(
                  1,
                )}
                %
              </p>

              <p className="mt-1 font-mono text-[10px] text-muted-foreground">
                {
                  result.confidence_band
                }{" "}
                confidence band
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
            <MiniStat
              label="Raw model score"
              value={result.raw_model_score.toFixed(
                3,
              )}
            />

            <MiniStat
              label="Calibrated probability"
              value={`${calibratedPercent.toFixed(
                1,
              )}%`}
            />

            <MiniStat
              label="Confidence"
              value={`${confidencePercent.toFixed(
                1,
              )}%`}
            />

            <MiniStat
              label="Uncertainty"
              value={`${uncertaintyPercent.toFixed(
                1,
              )}%`}
            />
          </div>

          <div className="mt-5">
            <div className="mb-2 flex items-center justify-between text-xs">
              <span>
                Calibrated probability
              </span>

              <span
                className={`font-mono ${impactTone}`}
              >
                {calibratedPercent.toFixed(
                  1,
                )}
                %
              </span>
            </div>

            <ProgressBar
              value={
                calibratedPercent
              }
              tone={
                impact === "High"
                  ? "bg-danger"
                  : impact ===
                      "Moderate"
                    ? "bg-amber"
                    : "bg-mint"
              }
            />
          </div>
        </section>

        {/* ================================================== */}
        {/* Direction summary */}
        {/* ================================================== */}

        <section className="glass-panel rounded-2xl p-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-violet">
            Explanation direction
          </p>

          <h3 className="mt-2 text-lg font-bold">
            Local feature influence
          </h3>

          <div className="mt-5 space-y-5">
            <div>
              <div className="mb-2 flex items-center justify-between text-xs">
                <span>
                  Supports higher impact
                </span>

                <span className="font-mono text-danger">
                  {direction.supporting_higher_impact_percent.toFixed(
                    2,
                  )}
                  %
                </span>
              </div>

              <ProgressBar
                value={
                  direction.supporting_higher_impact_percent
                }
                tone="bg-danger"
              />
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between text-xs">
                <span>
                  Supports lower impact
                </span>

                <span className="font-mono text-mint">
                  {direction.supporting_lower_impact_percent.toFixed(
                    2,
                  )}
                  %
                </span>
              </div>

              <ProgressBar
                value={
                  direction.supporting_lower_impact_percent
                }
                tone="bg-mint"
              />
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between text-xs">
                <span>
                  Neutral
                </span>

                <span className="font-mono text-muted-foreground">
                  {direction.neutral_percent.toFixed(
                    2,
                  )}
                  %
                </span>
              </div>

              <ProgressBar
                value={
                  direction.neutral_percent
                }
                tone="bg-foreground/30"
              />
            </div>
          </div>

          <div className="mt-5 rounded-xl border border-violet/20 bg-violet/[0.05] p-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-violet">
              Important
            </p>

            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              These percentages describe
              the relative local
              perturbation magnitude of
              model features. They are not
              causal biological
              percentages.
            </p>
          </div>
        </section>
      </div>

      {/* ================================================== */}
      {/* Top features */}
      {/* ================================================== */}

      <section className="glass-panel rounded-2xl p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
              Top XAI features
            </p>

            <h3 className="mt-2 text-lg font-bold">
              Strongest local model
              drivers
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Ranked by normalized absolute
              local perturbation
              contribution.
            </p>
          </div>

          <div className="text-right">
            <p className="font-mono text-[10px] text-muted-foreground">
              FEATURES ANALYZED
            </p>

            <p className="mt-1 text-2xl font-bold text-cyan">
              {
                explanation.feature_count
              }
            </p>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          {topFeatures.map(
            (
              feature,
            ) => {
              const supportsHigher =
                feature.direction ===
                "supports_higher_impact";

              const supportsLower =
                feature.direction ===
                "supports_lower_impact";

              const directionLabel =
                supportsHigher
                  ? "Higher impact"
                  : supportsLower
                    ? "Lower impact"
                    : "Neutral";

              const directionTone =
                supportsHigher
                  ? "text-danger"
                  : supportsLower
                    ? "text-mint"
                    : "text-muted-foreground";

              const barTone =
                supportsHigher
                  ? "bg-danger"
                  : supportsLower
                    ? "bg-mint"
                    : "bg-foreground/30";

              return (
                <div
                  key={
                    feature.feature_name
                  }
                  className="rounded-xl border border-foreground/5 bg-foreground/[0.025] p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span className="grid size-7 shrink-0 place-items-center rounded-full border border-cyan/20 bg-cyan/[0.06] font-mono text-[10px] font-bold text-cyan">
                        {
                          feature.rank
                        }
                      </span>

                      <div>
                        <p className="text-sm font-semibold">
                          {formatFeatureName(
                            feature.feature_name,
                          )}
                        </p>

                        <p className="mt-1 font-mono text-[10px] text-muted-foreground">
                          Value:{" "}
                          {String(
                            feature.feature_value,
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="font-mono text-sm font-bold">
                        {feature.normalized_percent.toFixed(
                          2,
                        )}
                        %
                      </p>

                      <p
                        className={`mt-1 font-mono text-[10px] ${directionTone}`}
                      >
                        {
                          directionLabel
                        }
                      </p>
                    </div>
                  </div>

                  <div className="mt-3">
                    <ProgressBar
                      value={
                        feature.normalized_percent
                      }
                      tone={
                        barTone
                      }
                    />
                  </div>

                  <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 font-mono text-[10px] text-muted-foreground">
                    <span>
                      Raw contribution:{" "}
                      {feature.raw_contribution.toFixed(
                        5,
                      )}
                    </span>

                    <span>
                      Signed influence:{" "}
                      {feature.signed_normalized_percent.toFixed(
                        2,
                      )}
                      %
                    </span>
                  </div>
                </div>
              );
            },
          )}
        </div>
      </section>

      {/* ================================================== */}
      {/* XAI metadata */}
      {/* ================================================== */}

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="glass-panel rounded-2xl p-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
            Explanation method
          </p>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <MiniStat
              label="Model"
              value={
                explanation.model_name
              }
            />

            <MiniStat
              label="Model version"
              value={
                explanation.model_version
              }
            />

            <MiniStat
              label="Explanation version"
              value={
                explanation.explanation_version
              }
            />

            <MiniStat
              label="Features"
              value={`${explanation.feature_count}`}
            />
          </div>

          <div className="mt-4 rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
              Normalization method
            </p>

            <p className="mt-2 text-sm font-semibold">
              {
                explanation.normalization_method
              }
            </p>

            <p className="mt-2 font-mono text-[10px] leading-relaxed text-muted-foreground">
              {
                explanation.normalization_formula
              }
            </p>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
            Interpretation
          </p>

          <p className="mt-4 text-sm leading-7 text-muted-foreground">
            {
              explanation.percentage_interpretation
            }
          </p>

          <div className="mt-5 flex items-start gap-3 rounded-xl border border-amber/20 bg-amber/[0.05] p-4">
            <CircleHelp className="mt-0.5 size-4 shrink-0 text-amber" />

            <p className="text-xs leading-relaxed text-muted-foreground">
              Feature influence explains
              how this model behaved for
              this specific variant. It
              does not establish a causal
              biological mechanism or
              clinical conclusion.
            </p>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <MiniStat
              label="Total contribution"
              value={explanation.total_absolute_contribution.toFixed(
                4,
              )}
            />

            <MiniStat
              label="Test set used"
              value={
                explanation.test_set_used
                  ? "Yes"
                  : "No"
              }
            />
          </div>
        </div>
      </section>

      <div className="rounded-2xl border border-amber/20 bg-amber/[0.04] p-4">
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 size-4 shrink-0 text-amber" />

          <p className="text-xs leading-relaxed text-muted-foreground">
            {
              currentAnalysis.xai
                .disclaimer
            }
          </p>
        </div>
      </div>

      <p className="text-center font-mono text-[10px] text-muted-foreground">
        GeneMirror AI XAI outputs are
        intended for computational
        research and educational use only.
      </p>
    </div>
  );
}




// ============================================================
// AI Scientist — Step 8 live backend integration
// ============================================================

function ScientistPage({
  currentAnalysis,
}: {
  currentAnalysis:
    | UnifiedAnalysisResponse
    | null;
}) {
  if (!currentAnalysis) {
    return (
      <div className="space-y-6">
        <PageHeader
          page="AI Scientist"
          eyebrow="Interpretation assistant"
        />

        <StatePanel
          tone="empty"
          icon={BrainCircuit}
          title="No analysis loaded"
          message="Analyze a missense variant in Gene Mirror first. GeneMirror Scientist will then display the grounded explanation returned by the backend."
        />

        <p className="text-center font-mono text-[10px] text-muted-foreground">
          GeneMirror Scientist provides computational explanations for research and educational use only.
        </p>
      </div>
    );
  }

  if (
    !currentAnalysis.scientist ||
    !currentAnalysis.scientist.sections ||
    !currentAnalysis.scientist.execution
  ) {
    return (
      <div className="space-y-6">
        <PageHeader
          page="AI Scientist"
          eyebrow="Interpretation assistant"
        />

        <StatePanel
          tone="error"
          icon={CircleHelp}
          title="Scientist explanation unavailable"
          message="The analysis completed, but the grounded Scientist payload is incomplete. Re-analyze the variant and confirm that the backend Scientist stage completed successfully."
        />
      </div>
    );
  }

  const scientist =
    currentAnalysis.scientist;

  const sections =
    scientist.sections;

  const execution =
    scientist.execution;

  const groundedFacts =
    scientist.grounded_facts ?? [];

  const activeTrace =
    `${
      currentAnalysis.variant
        .gene_symbol
    } / ${
      currentAnalysis.variant
        .protein_change ??
      "Variant"
    }`;

  const providerLabel =
    execution.used_llm_response
      ? execution.provider_used
      : "deterministic";

  const validationLabel =
    execution.validation_errors.length > 0
      ? `${execution.validation_errors.length} issue(s)`
      : "Passed";

  const formatValue = (
    value: unknown,
  ) => {
    if (
      value === null ||
      value === undefined
    ) {
      return "N/A";
    }

    if (
      typeof value ===
      "string"
    ) {
      return value;
    }

    if (
      typeof value ===
        "number" ||
      typeof value ===
        "boolean"
    ) {
      return String(
        value,
      );
    }

    try {
      return JSON.stringify(
        value,
        null,
        2,
      );
    } catch {
      return String(
        value,
      );
    }
  };

  const isProteinAnnotationValue = (
    value: unknown,
  ): value is {
    feature_type?: string | null;
    start?: number | null;
    end?: number | null;
    description?: string | null;
    feature_id?: string | null;
    evidence?: unknown[];
    distance_to_variant?: number | null;
    overlaps_variant?: boolean | null;
  } => {
    if (
      !value ||
      typeof value !==
        "object" ||
      Array.isArray(
        value,
      )
    ) {
      return false;
    }

    const record =
      value as Record<
        string,
        unknown
      >;

    return (
      "feature_type" in record &&
      (
        "start" in record ||
        "end" in record ||
        "distance_to_variant" in record ||
        "overlaps_variant" in record
      )
    );
  };

  const sectionCards = [
    {
      label: "Overview",
      value: sections.overview,
      tone: "text-cyan",
      border: "border-cyan/15",
      background: "bg-cyan/[0.03]",
    },
    {
      label: "Prediction",
      value: sections.prediction,
      tone: "text-amber",
      border: "border-amber/15",
      background: "bg-amber/[0.03]",
    },
    {
      label: "Evidence",
      value: sections.evidence,
      tone: "text-violet",
      border: "border-violet/15",
      background: "bg-violet/[0.03]",
    },
    {
      label: "Protein Context",
      value: sections.protein_context,
      tone: "text-mint",
      border: "border-mint/15",
      background: "bg-mint/[0.03]",
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        page="AI Scientist"
        eyebrow="Grounded interpretation"
        activeTrace={
          activeTrace
        }
      />

      {/* ================================================== */}
      {/* Scientist summary */}
      {/* ================================================== */}

      <section className="glass-panel overflow-hidden rounded-2xl p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid size-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-cyan/20 to-violet/20 text-cyan ring-1 ring-cyan/20">
              <BrainCircuit className="size-5" />
            </div>

            <div className="min-w-0">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
                {
                  scientist.scientist_name
                }
              </p>

              <h3 className="mt-1 text-xl font-bold">
                Grounded variant explanation
              </h3>

              <p className="mt-1 break-words font-mono text-[11px] text-muted-foreground">
                {
                  currentAnalysis.variant
                    .gene_symbol
                }{" "}
                ·{" "}
                {
                  currentAnalysis.variant
                    .dna_change ??
                  "DNA change unavailable"
                }{" "}
                ·{" "}
                {
                  currentAnalysis.variant
                    .protein_change ??
                  "Protein change unavailable"
                }
              </p>
            </div>
          </div>

          <span className="inline-flex shrink-0 items-center gap-2 rounded-full border border-mint/30 bg-mint/10 px-3 py-1.5 font-mono text-[10px] text-mint">
            <span className="size-1.5 rounded-full bg-mint gm-pulse" />
            GROUNDED BACKEND OUTPUT
          </span>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
          <MiniStat
            label="Provider"
            value={
              providerLabel
            }
          />

          <MiniStat
            label="LLM response"
            value={
              execution.used_llm_response
                ? "Yes"
                : "No"
            }
          />

          <MiniStat
            label="Fallback used"
            value={
              execution.fallback_used
                ? "Yes"
                : "No"
            }
          />

          <MiniStat
            label="Grounded facts"
            value={`${groundedFacts.length}`}
          />

          <MiniStat
            label="Validation"
            value={
              validationLabel
            }
          />

          <MiniStat
            label="Contract version"
            value={
              scientist.contract_version
            }
          />
        </div>
      </section>

      {/* ================================================== */}
      {/* Explanation sections */}
      {/* ================================================== */}

      <section className="space-y-4">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
            Scientist explanation
          </p>

          <h3 className="mt-2 text-lg font-bold">
            Grounded interpretation sections
          </h3>

          <p className="mt-1 text-xs text-muted-foreground">
            Each section is generated from structured GeneMirror backend results.
          </p>
        </div>

        <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">
          {sectionCards.map(
            (
              section,
            ) => (
              <article
                key={
                  section.label
                }
                className={`glass-panel min-w-0 overflow-hidden rounded-2xl border p-5 ${section.border} ${section.background}`}
              >
                <p
                  className={`font-mono text-[10px] uppercase tracking-[0.18em] ${section.tone}`}
                >
                  {
                    section.label
                  }
                </p>

                <p className="mt-3 whitespace-pre-line break-words text-sm leading-7 text-muted-foreground">
                  {
                    section.value
                  }
                </p>
              </article>
            ),
          )}
        </div>

        <article className="glass-panel min-w-0 overflow-hidden rounded-2xl border border-danger/15 bg-danger/[0.03] p-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-danger">
            Limitations
          </p>

          <p className="mt-3 whitespace-pre-line break-words text-sm leading-7 text-muted-foreground">
            {
              sections.limitations
            }
          </p>
        </article>
      </section>

      {/* ================================================== */}
      {/* Execution metadata */}
      {/* ================================================== */}

      <section className="glass-panel overflow-hidden rounded-2xl p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-violet">
              Execution metadata
            </p>

            <h3 className="mt-2 text-lg font-bold">
              Scientist runtime details
            </h3>
          </div>

          <span className="rounded-full border border-violet/20 bg-violet/[0.05] px-3 py-1 font-mono text-[10px] text-violet">
            {
              scientist.scientist_version
            }
          </span>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <div className="min-w-0 rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4">
            <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
              Scientist
            </p>
            <p className="mt-2 break-words text-sm font-semibold">
              {
                scientist.scientist_name
              }
            </p>
          </div>

          <div className="min-w-0 rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4">
            <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
              Provider used
            </p>
            <p className="mt-2 break-words text-sm font-semibold">
              {
                execution.provider_used
              }
            </p>
          </div>

          <div className="min-w-0 rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4">
            <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
              Requested provider
            </p>
            <p className="mt-2 break-words text-sm font-semibold">
              {
                execution.requested_provider ??
                "None"
              }
            </p>
          </div>

          <div className="min-w-0 rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4">
            <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
              Language model
            </p>
            <p className="mt-2 break-words text-sm font-semibold">
              {
                scientist.language_model ??
                "Not used"
              }
            </p>
          </div>

          <div className="min-w-0 rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4">
            <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
              Fallback used
            </p>
            <p className="mt-2 break-words text-sm font-semibold">
              {
                execution.fallback_used
                  ? "Yes"
                  : "No"
              }
            </p>
          </div>

          <div className="min-w-0 rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4">
            <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
              Contract version
            </p>
            <p className="mt-2 break-words text-sm font-semibold">
              {
                scientist.contract_version
              }
            </p>
          </div>
        </div>

        {execution.fallback_used && (
          <div className="mt-4 rounded-xl border border-amber/20 bg-amber/[0.05] p-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-amber">
              Fallback reason
            </p>

            <p className="mt-2 break-words text-xs leading-relaxed text-muted-foreground">
              {
                execution.fallback_reason ??
                "Fallback was used by the backend."
              }
            </p>
          </div>
        )}
      </section>

      {/* ================================================== */}
      {/* Grounded facts */}
      {/* ================================================== */}

      <section className="glass-panel min-w-0 overflow-hidden rounded-2xl p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan">
              Grounded facts
            </p>

            <h3 className="mt-2 text-lg font-bold">
              Backend evidence used by the Scientist
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Structured evidence is shown separately from the generated explanation.
            </p>
          </div>

          <span className="font-mono text-3xl font-bold text-cyan">
            {
              groundedFacts.length
            }
          </span>
        </div>

        <div className="mt-5 grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">
          {groundedFacts.length >
          0 ? (
            groundedFacts.map(
              (
                fact,
                index,
              ) => (
                <article
                  key={`${fact.source}-${fact.category}-${index}`}
                  className="min-w-0 overflow-hidden rounded-xl border border-foreground/5 bg-foreground/[0.03] p-4"
                >
                  <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                    <span className="max-w-full rounded-full border border-cyan/20 bg-cyan/[0.05] px-2 py-1 font-mono text-[9px] uppercase tracking-wider text-cyan">
                      {
                        fact.category
                      }
                    </span>

                    <span className="max-w-full break-all font-mono text-[9px] text-muted-foreground">
                      {
                        fact.source
                      }
                    </span>
                  </div>

                  <p className="mt-3 break-words text-sm leading-6 text-foreground">
                    {
                      fact.statement
                    }
                  </p>

                  {isProteinAnnotationValue(
                    fact.value,
                  ) ? (
                    <div className="mt-3 rounded-xl border border-mint/15 bg-mint/[0.025] p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
                            Annotation type
                          </p>

                          <p className="mt-1 text-sm font-semibold text-mint">
                            {
                              fact.value.feature_type ??
                              "Protein annotation"
                            }
                          </p>
                        </div>

                        <span className="rounded-full border border-mint/20 bg-mint/[0.06] px-2 py-1 font-mono text-[9px] text-mint">
                          UniProt context
                        </span>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                        <MiniStat
                          label="Start"
                          value={
                            fact.value.start !==
                            null &&
                            fact.value.start !==
                            undefined
                              ? `${fact.value.start}`
                              : "N/A"
                          }
                        />

                        <MiniStat
                          label="End"
                          value={
                            fact.value.end !==
                            null &&
                            fact.value.end !==
                            undefined
                              ? `${fact.value.end}`
                              : "N/A"
                          }
                        />

                        <MiniStat
                          label="Distance"
                          value={
                            fact.value.distance_to_variant !==
                            null &&
                            fact.value.distance_to_variant !==
                            undefined
                              ? `${fact.value.distance_to_variant} aa`
                              : "N/A"
                          }
                        />

                        <MiniStat
                          label="Overlaps variant"
                          value={
                            fact.value.overlaps_variant ===
                            true
                              ? "Yes"
                              : fact.value.overlaps_variant ===
                                  false
                                ? "No"
                                : "N/A"
                          }
                        />
                      </div>

                      {fact.value.description && (
                        <div className="mt-3 rounded-lg border border-foreground/5 bg-ink/30 p-3">
                          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
                            Description
                          </p>

                          <p className="mt-2 break-words text-xs leading-6 text-foreground">
                            {
                              fact.value.description
                            }
                          </p>
                        </div>
                      )}

                      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                        <div className="rounded-lg border border-foreground/5 bg-ink/30 p-3">
                          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
                            Feature ID
                          </p>

                          <p className="mt-2 break-words font-mono text-[10px] text-foreground">
                            {
                              fact.value.feature_id ??
                              "Not provided"
                            }
                          </p>
                        </div>

                        <div className="rounded-lg border border-foreground/5 bg-ink/30 p-3">
                          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
                            Evidence records
                          </p>

                          <p className="mt-2 font-mono text-[10px] text-foreground">
                            {
                              Array.isArray(
                                fact.value.evidence,
                              )
                                ? `${fact.value.evidence.length}`
                                : "0"
                            }
                          </p>
                        </div>
                      </div>

                      {Array.isArray(
                        fact.value.evidence,
                      ) &&
                        fact.value.evidence.length >
                          0 && (
                          <details className="mt-3 rounded-lg border border-foreground/5 bg-ink/20 p-3">
                            <summary className="cursor-pointer font-mono text-[10px] text-cyan">
                              View evidence records
                            </summary>

                            <div className="mt-3 space-y-2">
                              {fact.value.evidence.map(
                                (
                                  evidence,
                                  evidenceIndex,
                                ) => (
                                  <div
                                    key={`${String(evidence)}-${evidenceIndex}`}
                                    className="break-all rounded-md border border-foreground/5 bg-foreground/[0.025] px-3 py-2 font-mono text-[10px] leading-5 text-muted-foreground"
                                  >
                                    {
                                      String(
                                        evidence,
                                      )
                                    }
                                  </div>
                                ),
                              )}
                            </div>
                          </details>
                        )}
                    </div>
                  ) : (
                    <div className="mt-3 rounded-lg border border-foreground/5 bg-ink/30 p-3">
                      <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
                        Value
                      </p>

                      <p className="mt-2 whitespace-pre-wrap break-words font-mono text-[10px] leading-5 text-muted-foreground">
                        {
                          formatValue(
                            fact.value,
                          )
                        }
                      </p>
                    </div>
                  )}

                  {fact.supports && (
                    <p className="mt-3 break-words font-mono text-[10px] text-violet">
                      Supports:{" "}
                      {
                        fact.supports
                      }
                    </p>
                  )}
                </article>
              ),
            )
          ) : (
            <p className="text-sm text-muted-foreground">
              No grounded facts were returned.
            </p>
          )}
        </div>
      </section>

      {execution.validation_errors.length >
        0 && (
        <section className="rounded-2xl border border-danger/25 bg-danger/[0.05] p-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-danger">
            Scientist validation warnings
          </p>

          <div className="mt-3 space-y-2">
            {execution.validation_errors.map(
              (
                error,
                index,
              ) => (
                <div
                  key={`${error}-${index}`}
                  className="rounded-lg border border-danger/10 bg-danger/[0.03] px-3 py-2 text-xs text-muted-foreground"
                >
                  {
                    error
                  }
                </div>
              ),
            )}
          </div>
        </section>
      )}

      <div className="rounded-2xl border border-amber/20 bg-amber/[0.04] p-4">
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 size-4 shrink-0 text-amber" />

          <p className="text-xs leading-relaxed text-muted-foreground">
            {
              scientist.disclaimer
            }
          </p>
        </div>
      </div>

      <p className="text-center font-mono text-[10px] text-muted-foreground">
        GeneMirror Scientist explains structured backend results only.
        It does not independently calculate predictions, establish
        causality, diagnose disease, or provide medical advice.
      </p>
    </div>
  );
}

// ============================================================
// Main application
// ============================================================

export function GeneMirrorApp() {
  const [
    page,
    setPage,
  ] =
    useState<Page>(
      "Overview",
    );

  const [
    mobileOpen,
    setMobileOpen,
  ] =
    useState(false);

  const [
    selectedGene,
    setSelectedGene,
  ] =
    useState(
      "TP53",
    );

  const [
    selectedVariant,
    setSelectedVariant,
  ] =
    useState(
      "GM-TP53-0743",
    );

  const [
    currentAnalysis,
    setCurrentAnalysis,
  ] =
    useState<
      UnifiedAnalysisResponse |
      null
    >(null);

  const navigate = (
    nextPage: Page,
  ) => {
    setPage(
      nextPage,
    );

    setMobileOpen(
      false,
    );

    window.scrollTo({
      top: 0,
      behavior:
        "smooth",
    });
  };

  const content =
    useMemo(
      () => {
        if (
          page ===
          "Overview"
        ) {
          return (
            <OverviewPage
              onNavigate={
                navigate
              }
            />
          );
        }

        if (
          page ===
          "Genome Explorer"
        ) {
          return (
            <ExplorerPage
              onOpenMirror={(
                gene,
              ) => {
                setSelectedGene(
                  gene,
                );

                const firstVariant =
                  variants.find(
                    (
                      variant,
                    ) =>
                      variant.gene ===
                      gene,
                  );

                if (
                  firstVariant
                ) {
                  setSelectedVariant(
                    firstVariant.id,
                  );
                }

                navigate(
                  "Gene Mirror",
                );
              }}
              onAnalysisComplete={
                setCurrentAnalysis
              }
            />
          );
        }

        if (
          page ===
          "Gene Mirror"
        ) {
          return (
            <MirrorPage
              selectedGene={
                selectedGene
              }
              selectedVariant={
                selectedVariant
              }
              onGeneChange={
                setSelectedGene
              }
              onVariantChange={
                setSelectedVariant
              }
              currentAnalysis={
                currentAnalysis
              }
              onAnalysisComplete={
                setCurrentAnalysis
              }
            />
          );
        }

        if (
          page ===
          "Protein Explorer"
        ) {
          return (
            <ProteinPage
              currentAnalysis={
                currentAnalysis
              }
            />
          );
        }

        if (
          page ===
          "XAI Lab"
        ) {
          return (
            <XaiPage
              currentAnalysis={
                currentAnalysis
              }
            />
          );
        }

        return (
          <ScientistPage
            currentAnalysis={
              currentAnalysis
            }
          />
        );
      },
      [
        page,
        selectedGene,
        selectedVariant,
        currentAnalysis,
      ],
    );

  return (
    <div className="relative min-h-screen overflow-hidden bg-ink text-foreground">
      <div
        className="pointer-events-none fixed inset-0"
        aria-hidden="true"
      >
        <div className="absolute -right-40 -top-40 size-[520px] rounded-full bg-cyan/10 blur-[120px] gm-float" />

        <div className="absolute -left-40 top-1/3 size-[460px] rounded-full bg-violet/10 blur-[120px] gm-float-slow" />

        <div className="absolute bottom-0 right-1/4 size-[380px] rounded-full bg-dna/[0.07] blur-[110px]" />
      </div>

      <div className="relative flex min-h-screen">
        <aside
          className={`${
            mobileOpen
              ? "flex"
              : "hidden"
          } fixed inset-y-0 left-0 z-40 w-64 shrink-0 flex-col border-r border-foreground/5 bg-ink-2/95 backdrop-blur-xl lg:sticky lg:top-0 lg:flex lg:h-screen`}
        >
          <div className="flex h-16 items-center gap-2.5 border-b border-foreground/5 px-5">
            <div className="grid size-8 place-items-center rounded-lg bg-gradient-to-br from-cyan to-violet font-mono font-bold text-primary-foreground shadow-[0_0_20px_color-mix(in_oklab,var(--color-cyan)_35%,transparent)]">
              GM
            </div>

            <div className="leading-tight">
              <p className="text-[13px] font-bold tracking-tight">
                GeneMirror
              </p>

              <p className="font-mono text-[10px] text-cyan/80">
                AI
              </p>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="ml-auto text-muted-foreground lg:hidden"
              onClick={() =>
                setMobileOpen(
                  false,
                )
              }
            >
              <Menu />
            </Button>
          </div>

          <nav className="flex-1 space-y-1 px-3 py-4">
            {navItems.map(
              ({
                label,
                icon: Icon,
                accent,
              }) => (
                <Button
                  key={
                    label
                  }
                  variant="ghost"
                  onClick={() =>
                    navigate(
                      label,
                    )
                  }
                  className={`h-auto w-full justify-start gap-3 rounded-lg px-3 py-2.5 text-[13px] ${
                    page ===
                    label
                      ? "border border-cyan/20 bg-foreground/[0.06] font-semibold text-foreground shadow-[inset_2px_0_0_0_var(--color-cyan)]"
                      : "text-muted-foreground hover:bg-foreground/5 hover:text-foreground"
                  }`}
                >
                  <span
                    className={`size-1.5 rounded-full bg-current ${
                      page ===
                      label
                        ? "gm-pulse"
                        : "opacity-40"
                    } ${accent}`}
                  />

                  <Icon
                    className={`size-4 ${accent}`}
                  />

                  {label}
                </Button>
              ),
            )}
          </nav>

          <div className="border-t border-foreground/5 px-5 py-4">
            <p className="text-[11px] text-muted-foreground">
              Research Prototype
            </p>

            <p className="font-mono text-[10px] text-cyan/70">
              v1.0.0 · API
              connected
            </p>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-foreground/5 bg-ink/70 px-4 backdrop-blur-xl lg:px-6">
            <Button
              variant="ghost"
              size="icon"
              className="text-muted-foreground lg:hidden"
              onClick={() =>
                setMobileOpen(
                  true,
                )
              }
            >
              <Menu />
            </Button>

            <div className="min-w-0">
              <h1 className="truncate text-sm font-bold tracking-tight">
                {page}
              </h1>

              <p className="truncate text-[11px] text-muted-foreground">
                {
                  pageSubtitles[
                    page
                  ]
                }
              </p>
            </div>

            <span className="ml-1 inline-flex items-center gap-1.5 rounded-full border border-violet/30 bg-violet/10 px-2.5 py-1 font-mono text-[10px] font-medium text-violet">
              <span className="gm-pulse size-1.5 rounded-full bg-violet" />

              Research Mode
            </span>

            <div className="ml-auto flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:bg-foreground/5 hover:text-foreground"
              >
                <Bell />
              </Button>

              <Button
                variant="ghost"
                size="icon"
                className="rounded-full bg-gradient-to-br from-cyan to-violet text-[11px] font-bold text-primary-foreground hover:opacity-90"
              >
                DR
              </Button>
            </div>
          </header>

          <main className="mx-auto max-w-[1480px] p-4 sm:p-6">
            {content}
          </main>
        </div>
      </div>
    </div>
  );
}