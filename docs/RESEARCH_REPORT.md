# Research report: a validation-ready prototype

## Research question and evidence status

When, and for which needs segments, can LLM-generated product feedback approximate held-out consumer evaluations well enough to inform early innovation research?

This repository implements the experiment infrastructure. It has **no real consumer validation findings** and makes no claim that AI can replace respondents. The included demonstration uses fictional tissue concepts, four authored needs archetypes, rule-generated reference ratings and rule-generated predictions. It is an independent application portfolio project for the Essity thesis topic, not company research.

## Design

Twenty fictional respondents per archetype evaluate all three concepts (80 respondents, 240 pairs). Synthetic reference ratings combine authored utility weights, a respondent-level random effect and item noise. Predictions use the same utility family with a small positive offset and separate random noise. Ratings are rounded and bounded to 1–5. This shared structure is deliberately transparent and limits the meaning of good fit.

Three simulation runs are evaluated per pair. The paid adapter uses only persona needs, concept description and the common question; reference ratings and reference text are excluded. Repeated calls for different respondents in the same segment have identical prompt content, so individual differences are not modeled. Metadata captures source/manifest hashes, authored design, prompt version, seed and selected model; predictions capture returned model and request ID for live API runs.

## Operational definitions

Let y be one reference rating and p-bar the mean prediction across runs for that respondent/concept pair.

- **Error:** MAE = mean(|p-bar − y|), RMSE = sqrt(mean((p-bar − y)^2)). Units are rating points. Averaging predictions can reduce error and must not be confused with single-draw performance.
- **Bias:** mean(p-bar − y), plus each persona/concept cell's mean difference and the maximum absolute cell difference. Positive means overprediction. These are descriptive segment errors, not proof of demographic fairness.
- **Consistency:** mean single-draw exact agreement and within-one agreement against references; Spearman correlation of concept means uses average ranks for ties and returns null if ranks are constant. With only three concepts, ranking evidence is weak.
- **Stability:** sample SD across repeated predictions within each pair, averaged over pairs; and exact agreement over all within-pair draw combinations. A single run yields null. Stability does not imply accuracy.
- **Uncertainty:** 500 respondent-cluster bootstrap resamples produce a percentile MAE interval, preserving the respondent's multiple concepts. It reflects sampling variation conditional on the current simulator and predictions, not population coverage or model-training uncertainty. Fewer than two respondents yields null.

The numeric treatment of a 1–5 ordinal scale assumes equally spaced categories. Report agreement metrics alongside distance metrics. Do not pool distinct questions or scales.

## Demonstration results

See the versioned [metrics JSON](../examples/demo/metrics.json), [chart](../examples/demo/concept_means.svg), and [HTML report](../examples/demo/report.html). These are executable outputs of the synthetic study, not human evidence. The report labels provenance and provider explicitly. No paid model was run to generate the committed example.

Free-text outputs are provided for inspection, but templated offline text does not demonstrate natural-language model quality. Automated lexical similarity would not establish insight validity; qualitative validation is a future study component.

## Proposed real validation study

Freeze persona definitions and prompts using a development sample; split by respondent before tuning. Use identical stimuli, questions and language for humans and the LLM. Preserve a held-out final test set and preregister evaluation criteria. Set sample size using a pilot variance estimate and a decision-relevant precision/power calculation; this prototype does not prescribe an unsupported universal minimum.

Compare needs personas to generic-consumer and simple mean baselines, using development-only estimates for any fitted baseline. Repeat across model versions, prompt paraphrases and sampling settings. The current CLI measures repeated-run stability only; paraphrase/model sensitivity requires separate runs and an added cross-run comparison. Audit subgroup coverage and unequal exposure. Add blind human coding of benefits, concerns, contradictions and novel claims, report inter-rater agreement, and resolve disagreements without viewing condition labels.

Define acceptance thresholds with the business decision owner before reading held-out results. A concept-screening tool may tolerate different errors from a launch decision. Keep human research in the loop; do not turn a single aggregate correlation into a substitution claim.

## Limitations and next evidence

No real sample, no independent persona derivation, no live API execution, no evidence of representativeness, no semantic validity scoring, no complete fairness audit, and no cross-model robustness study are available in the shipped project. Public reviews may have selection bias and different outcome constructs; they are not interchangeable with randomized concept tests. Real data licensing and provenance declarations require manual verification.

The next concrete deliverable is a documented, deidentified, held-out public dataset compatible with the exact study stimuli—or a separately documented redesign around an appropriate dataset. See [DATA_CONTRACT.md](DATA_CONTRACT.md).

## Implementation reference

The optional API adapter follows the [official OpenAI Chat Completions API](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create), checked 2026-10-20. JSON-mode responses are schema-checked locally; API failures are surfaced without silent substitution.
