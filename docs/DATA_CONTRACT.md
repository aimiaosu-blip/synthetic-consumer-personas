# Real public consumer data contract

The shipped data are synthetic. This document defines future input requirements; it does not claim a real dataset has been obtained.

## CSV

UTF-8 CSV with exactly these columns:

`respondent_id,persona_id,concept_id,rating,feedback,source_type`

- `respondent_id`: deidentified study key; one stable key across concepts. Do not use a name, email or public username.
- `persona_id`: `value`, `comfort`, `eco`, or `convenience`, mapped using pre-outcome needs information. Never infer a segment from the held-out rating being predicted.
- `concept_id`: `essential`, `gentle`, or `refill`; only use these when the source actually evaluated the corresponding stimuli. For other products, deliberately adapt `personas/design.py` and document mapping.
- `rating`: integer 1–5 with the exact purchase-intent anchors in `design.py`. Star ratings of a purchased product are not purchase-intent concept-test responses.
- `feedback`: deidentified response, or empty if unavailable. It is retained only in the input and not sent to the API. It is not currently semantically scored.
- `source_type`: `real_public` for all rows. Synthetic fixtures must remain `synthetic_demo`.

One observation per respondent/concept; missing ratings and unknown IDs fail validation. Missing concept coverage is allowed but comparisons reflect observed samples and may be confounded by unequal respondent composition. Retain balanced exposure or analyze separately.

## Manifest

Create `data/imported/manifest.json` using actual source details, never invented values:

```json
{
  "source_type": "real_public",
  "source_url": "https://PUBLIC-SOURCE-URL",
  "license": "Actual license and permitted research use",
  "collected_at": "Actual collection date or documented interval",
  "population": "Recruitment, country, language and sampling limitations",
  "question": "Exact survey wording, anchors and response context",
  "persona_mapping": "Pre-outcome assignment rule and held-out split procedure",
  "concept_mapping": "Exact stimulus correspondence or documented design adaptation",
  "deidentified": true,
  "holdout": true
}
```

The example is a schema guide, not evidence of permission or provenance. Verify source authenticity, reuse terms, consent scope, redaction, and the held-out split yourself. Nonempty fields do not prove validity.

## What still needs collecting

1. Public, lawfully reusable consumer responses to identical product stimuli and questions, with documented sampling and sufficient observations per segment/concept.
2. Non-sensitive needs variables collected before outcomes, enabling pre-specified persona assignment and disjoint development/test respondents.
3. Exact stimuli, scale anchors, dates, language, and collection mode.
4. Deidentified free-text responses plus an independently developed qualitative coding rubric and at least two blinded coders.
5. A separate final test set or replication sample, and documented permission for any API processing or public reporting.

Public product reviews can support a separate exploratory benchmark, but cannot establish validity for these fictional concepts. Do not fabricate mappings to make an unrelated dataset fit. Once appropriate data are identified, record excluded rows and selection criteria in a separate source audit; this strict importer fails rather than silently dropping records.
