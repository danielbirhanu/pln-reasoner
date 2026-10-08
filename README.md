# Education Probabilistic Logic Network

A mini PLN engine for **reasoning about student academic risk and possible support**, using MeTTa for STV arithmetic and knowledge matching, and Python for bounded forward/backward search. Educational values are illustrative. This project demonstrates uncertain reasoning; it does not claim predictive accuracy or make automated decisions about students.

## Run in three commands

Use Python **3.12 or later** with Hyperon **0.2.10**. Extract the ZIP, open a terminal inside `pln-reasoner`, and run:

```bash
python -m pip install -r requirements.txt
python run_tests.py
python tests/scenarios.py
```

Recommended isolation:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell instead:
# .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The verification environment was Python 3.12.14 and Hyperon 0.2.10 on Linux. Platform-specific installation behavior beyond that environment is not claimed. No model download, API key or training dataset is needed. The report PDF is already included; ReportLab is not a runtime dependency.

Run complete results export:

```bash
python tests/scenarios.py --output results/scenarios.json
python -m search.engine
```

The test runner exits with a nonzero status for failed assertions, failed regression tests or empty discovery. It works when invoked by absolute path from another working directory. The stored `results/` files contain results from the verified submission.

## Example domain queries

```python
from search.engine import PLNSearchEngine

engine = PLNSearchEngine()
beliefs = engine.forward_chain(max_depth=4)
print(beliefs['(Evaluation AcademicRisk Hana)'].stv)
# (0.5688096320703258, 0.3476728315191026)

answer = engine.backward_chain('(Evaluation AcademicRisk Hana)', max_depth=4)
print(answer.stv)  # same bounded belief as forward search
print(answer.atom) # complete proof tree with evidence IDs

engine.add_observation('LowAssignmentCompletion', 'Hana', 0.3, 0.8,
                       'teacher-assignment-new')
updated = engine.forward_chain(max_depth=4)
print(updated['(Evaluation AcademicRisk Hana)'].stv)
# (0.44962083632419575, 0.29324800182300864)

print(engine.abduce('LowQuizPerformance', 'Sara')) # alternative hypotheses
```

The controller owns the raw records. Add evidence with `add_observation`; correct an existing record with `replace_observation(id, s, c)`; retract it with `remove_observation(id)`. An identical duplicate ID is idempotent; using that ID for a different record raises an error. Mutating `engine.metta` directly is not an ingestion API: the next query rebuilds its active space from the controller's records.

## Files and architecture

| File | Responsibility |
|---|---|
| `knowledge/students.metta` | Student entities |
| `knowledge/observations.metta` | Individual evidence records |
| `knowledge/education-rules.metta` | Probabilistic implications and contextual priors |
| `knowledge/cohort.metta` | Conditional cohort estimates used by Scenario G |
| `knowledge/README.md` | Entity, relation and evidence semantics |
| `pln/truth-values.metta` | STVs, weights, bounds and consistency checks |
| `pln/rules.metta` | Revision, modus ponens, relationship deduction, induction, abduction |
| `search/forward.metta`, `search/backward.metta` | Directional rule matching in the same active KB |
| `search/engine.py` | Evidence records, rule construction, proof traversal and selection |
| `run_tests.py`, `tests/` | Arithmetic assertions, behavioral regressions and demonstrations |
| `report.pdf`, `report.md` | Two-page report and editable report text |
| `results/` | Recorded STVs, full provenance and verification output |

`main.metta` is a standalone arithmetic entry point. The main domain demonstrations use `tests/scenarios.py`. All mathematical inference calls execute MeTTa definitions rather than duplicate Python formulas.

## STVs and the implemented algebra

An STV is `<s,c>`, with finite `0 <= s <= 1` and `0 <= c < 1`. Strength expresses support for the proposition; confidence expresses evidential support, not classification accuracy. Using `k=1`, evidence weight is `w=c/(1-c)` and `c=w/(w+1)`. The source values are illustrative estimates, so `w` is an equivalent evidence weight, not a measured student count.

The modern reference is [TrueAGI PLN](https://github.com/trueagi-io/PLN), particularly [its truth functions](https://github.com/trueagi-io/PLN/blob/main/lib_pln.metta). This is an independent educational mini implementation, not a wrapper around that repository. The following explains the selected formula lineage and extensions explicitly.

Let `pBA=P(B|A)`, `pBC=P(C|B)` when used in the deduction chain, and `q` be an uncertain observation strength.

| Operation | Strength | Confidence policy |
|---|---|---|
| Revision | `(w1*s1+w2*s2)/(w1+w2)` | `(w1+w2)/(1+w1+w2)`; no evidence gives `<0.5,0>` |
| Modus ponens | `q*pBA + (1-q)*0.02` | `q*pBA*cq*cBA` |
| Relationship deduction A->B->C | `pBA*pCB+(1-pBA)*(pC-pB*pCB)/(1-pB)` | `pBA*pCB*cBA*cCB` |
| Induction from cohort C | `pAC*pBC*pC/pA + (1-pAC*pC/pA)*(pB-pC*pBC)/(1-pC)` | `w2c(pBC*cBC*cAC)*cC*cA*cB` |
| Diagnostic abduction | `q*(pBA*pA/pB)+(1-q)*((1-pBA)*pA/(1-pB))` | `w2c(pBA*cBA*cq)*cA*cB` |

Revision, modus-ponens and relationship-deduction confidence follow the corresponding reference mini-PLN forms. Induction uses its evidential confidence form with an additional conservative multiplication by prior confidences. Diagnostic abduction specializes Bayesian inversion to uncertain individual evidence (a Jeffrey update) and similarly discounts by prior confidences. These confidence formulas are explicit heuristics, not uniquely determined by probability-strength algebra.

Modus ponens adopts the reference's fixed background `P(B|not A)=0.02`. This is a modeling assumption, not the marginal `P(B)`. Relationship deduction instead uses the supplied population priors and assumes independence of the endpoint properties conditional on the intermediate property and its complement. Induction assumes independence of A and B conditional on the cohort and its complement. Abduction assumes new evidence about B does not additionally inform A once B is specified. The confidence of deduction's contextual priors does not enter its chosen reference confidence heuristic; those priors still appear in its proof support.

Inputs must obey both joint-probability bounds:

`max(0,pA+pB-1) <= pA*P(B|A) <= min(pA,pB)`.

Undefined denominators and inconsistent probabilities raise explicit errors. Invalid values are not clamped into plausible-looking results. Source conditionals with available population priors are checked at ingestion; inadmissible inferred relationships are excluded from closure. Structural atom parsing supports scientific notation and rejects malformed or non-finite STVs.

## Evidence accounting and search policy

1. Keep each raw observation under one stable evidence ID. Consolidate distinct observations of the same proposition with revision.
2. Rebuild the active, owned MeTTa space for each query. Raw inputs appear as `Observation` atoms; only current conclusions appear as `Fact` atoms. Replaced and retracted evidence therefore cannot leave stale active facts.
3. Induce relationships from explicit `CohortConditional` records, then construct bounded, acyclic relationship deductions. All rules use `(Rule (Implication A B) STV provenance)`. Derived rules carry the complete source rule, cohort and prior evidence.
4. Explicitly authored base rules remain authoritative for an already declared edge. Induced/deduced alternatives are retained for inspection but do not silently overwrite that authored relationship. New edges are usable by both directions.
5. Forward search expands simple fact paths from consolidated observations. Backward search recursively finds those paths for a requested goal. The depth limit counts original implication edges, including edges inside a derived shortcut. A known observation needs zero hops. Both directions also enforce a finite proof budget and reject cycles.
6. At a requested statement, rank proofs by confidence, then hop count and stable support/provenance keys. Select the best and revise only subsequent proofs whose complete support is disjoint. Shared rule or prior IDs count as overlap, not merely shared observations. Partially overlapping alternatives are not treated as independent evidence.

This is a deterministic greedy policy, not an optimization over every possible independent subset. Revision occurs at the queried proposition after path enumeration; a revised intermediate conclusion is not fed back as another independent raw proof. Consequently a downstream STV need not equal modus ponens applied to the independently consolidated intermediate STV. Both searches apply the same policy at the same depth. Re-running with unchanged records cannot manufacture evidence or increase confidence.

## Evaluation and expected output

The package includes **20 MeTTa assertions, 33 Python regression tests and eight asserted scenarios**. Behavioral tests cover source revision, downstream recomputation, correction with unchanged IDs, retraction, active-space uniqueness, idempotence, overlap, cycles, zero confidence, derived-rule use, provenance, both probability bounds, depth limits, budget limits and failing/empty test discovery.

| Scenario | Verified outcome |
|---|---|
| A: Supported conclusion | Hana intervention `<0.431720,0.075061>` |
| B: Incomplete evidence | Dawit risk has no supported proof |
| C: Uncertain evidence | Risk `<0.428000,0.054600>` |
| D: Alternative explanations | Sara has four hypothesis candidates; they are not promoted to facts |
| E: Conflicting evidence | Hana risk changes from `<0.568810,0.347673>` to `<0.449621,0.293248>` |
| F: Genuine four-hop path | Intervention `<0.429741,0.036383>`; confidence falls at each hop |
| G: KB induction and use | New LowQuizPerformance->WeakPrerequisiteKnowledge rule `<0.272222,0.297256>` supports a Sara query |
| H: Search agreement | Three forward/backward STVs and support sets match to tolerance `1e-12` |

Scenario F uses a focused subset of the authored domain chain without population priors, so shortcut relationship deduction is unavailable; its five rows show an actual zero-to-four-hop progression. Scenario G loads the additional cohort file and consumes a new induced edge; it does not overwrite the existing opposite-direction educational rule.

## Limitations

The engine handles unary educational evaluations and probabilistic concept implications, not unrestricted first-order logic, arbitrary hypergraphs, continuous grades or temporal causality. Sample sizes and calibration are not claimed. Distinct evidence IDs are assumed independent for revision; assigning different IDs to correlated observations does not establish statistical independence. Conservative overlap selection can leave useful information uncombined. Finite depth and budget bounds mean a failed query indicates no supported proof within the model and resource bounds, not that the proposition is false. Hypothesis strengths are not mutually exclusive probabilities and do not sum to one. A teacher must interpret the output alongside actual student evidence.

## Assignment coverage

| Requirement | Deliverable / demonstration |
|---|---|
| Domain and uncertainty problem | README introduction; report section 1 |
| Entities, facts, STVs, interconnected relations | `knowledge/` and its semantic README |
| Deduction, induction, abduction, revision | MeTTa algebra; Scenarios A/D/E/F/G |
| Forward and backward chaining on the same KB | Directional MeTTa matching; Scenarios A/B/H and G |
| Required evaluation situations and numerical analysis | Eight asserted scenarios; `results/`; report section 4 |
| Modular code, README, KB and 1-2-page report | Source folders, this README, `report.pdf` (2 pages) |
