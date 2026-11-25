# Nepali-English AI Benchmark — Protocol v0.1

**Status:** Proposed protocol. No benchmark results are claimed.

## Objective

Create a small, carefully reviewed evaluation set to measure how AI systems handle Nepali and English language tasks, code-switching, and evidence-grounded questions over documents.

## Evaluation slices

1. Standard written Nepali (Devanagari).
2. Romanized Nepali.
3. Nepali-English code-switching.
4. Common spelling variation and informal phrasing.
5. Short factual questions and multi-step instructions.
6. Document-grounded questions with answerable and unanswerable cases.
7. Citation support: whether the cited passage actually supports the answer.
8. Safety and privacy: requests for secrets, personal data and disallowed disclosure.

## Initial scale

Start with a pilot of approximately 200 reviewed examples. Expand only after the annotation process is stable. A future 1,000+ example set is a goal, not an existing dataset.

## Required record fields

- Stable example ID.
- Language/slice label.
- Prompt and task description.
- Expected answer or scoring rubric.
- Supporting source passage and source identifier when applicable.
- Answerability label (answerable / insufficient evidence).
- Safety label where applicable.
- Provenance, consent and licence record.
- Reviewer and adjudication status (kept private if reviewer identity is personal data).

## Data governance

- Use original examples, public-domain material, or material with explicit permission and compatible licences.
- Obtain informed consent for contributions containing personal or sensitive information; preferably exclude such information entirely.
- Do not scrape private groups, personal accounts or customer workspaces.
- Remove names, phone numbers, addresses, credentials and other unnecessary identifiers.
- Keep a deletion and correction process.
- Publish only examples cleared for public distribution; keep restricted examples in access-controlled evaluation environments.
- Document source and licence for every example. If provenance is unknown, exclude it.

## Annotation and quality

- Write a rubric before annotation.
- Have two reviewers independently label a pilot subset.
- Adjudicate disagreements and record the reason.
- Report agreement and the number of excluded examples.
- Include native or highly proficient Nepali reviewers; machine translation alone is not ground truth.
- Review dialect, register and regional coverage without claiming complete coverage.

## Metrics

- Task accuracy / rubric score.
- Groundedness and citation precision for document tasks.
- Correct abstention rate on unanswerable questions.
- False-answer rate on unanswerable questions.
- Language quality, scored separately for Nepali, Romanized Nepali and code-switching.
- Safety-policy adherence.
- Latency and estimated cost per task, with provider/model and date.

Do not collapse all measures into a single score unless the weighting is pre-registered and justified.

## Experiment reporting

Every result must include:
- Dataset version and checksum.
- Model/provider and exact model identifier.
- Prompt and system-instruction version.
- Sampling settings and tool configuration.
- Number of examples and exclusions.
- Metrics with confidence intervals where appropriate.
- Error analysis and known limitations.
- Run date and reproducible evaluation code.

## Baseline plan

1. Freeze and review the pilot set.
2. Evaluate at least one model per supported provider under identical tasks.
3. Record raw outputs in a privacy-safe way.
4. Score blind where feasible.
5. Publish error categories and limitations before making performance claims.

## Non-goals

This benchmark does not establish that a model is safe for medical, legal, financial or other high-stakes decisions. It does not prove general intelligence, dialect coverage or production readiness.
