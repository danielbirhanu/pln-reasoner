# Education PLN Reasoning Engine

Technical report | MeTTa and Python | Verified with Hyperon 0.2.10

## 1. Problem and domain

The system reasons about student academic risk and possible academic support when assessments, assignment observations and teacher evidence are uncertain or conflicting. It can infer a supported conclusion, identify missing evidence and propose alternative explanations for low quiz performance. Probability strengths and evidential confidence express different aspects of uncertainty. The educational values are illustrative, and a teacher remains responsible for interpreting the results.

## 2. Knowledge representation and design

The knowledge base defines students, unary educational evaluations, probabilistic implications, population priors and explicit cohort conditional estimates. Every source record carries an STV and a stable evidence ID. Strength lies in [0,1], confidence in [0,1), and the equivalent evidence weight is w=c/(1-c), with k=1. The weights do not represent measured cohort sizes in this demonstration.

MeTTa implements validation, the probability operations and directional rule matching. A Python controller owns source records, constructs bounded relationship proofs and searches the same active knowledge base in both directions. Source observations are consolidated before inference. Each query rebuilds its owned active space, so changed or retracted evidence cannot leave stale conclusions. Rule and prior provenance remain attached to every downstream proof.

## 3. Inference and evidence policy

Revision merges independent support by evidence-weighted strength and summed weight. Modus ponens uses the reference mini-PLN background conditional 0.02 and strength-dependent confidence decay. Relationship deduction uses total probability through an intermediate concept and contextual priors. Induction generalizes from cohort conditional estimates under independence within the cohort and its complement. Diagnostic abduction combines the positive and negative Bayesian branches using an uncertain observed effect (a Jeffrey update).

The strength formulas are probability identities under the documented assumptions; confidence propagation is an evidential heuristic. Revision, modus ponens and relationship-deduction confidence follow the reference mini-PLN forms. Induction and diagnostic abduction additionally discount confidence by contextual-prior confidence. Both joint-probability bounds and STV ranges are validated; inconsistent inputs and undefined denominators are rejected rather than clamped.

Both searches enumerate bounded acyclic proofs. At each requested proposition, the highest-confidence proof is selected first; additional proofs are revised only when their complete support is disjoint. Shared observations, rules or priors prevent independent revision. Authored rules retain precedence over inferred alternatives for the same edge. New inferred edges are available to both directions. Hypotheses remain candidates rather than accepted facts.


---

## 4. Verified results

The eight asserted demonstrations cover the assignment scenarios and additional consistency checks. The following values are generated from the stored execution results; complete evidence sets and nested proof trees are included in results/scenarios.json.

| Scenario / outcome | Strength | Confidence |
|---|---|---|
| A: Hana intervention | 0.431720 | 0.075061 |
| B: Dawit risk - missing evidence | No supported proof | - |
| C: Risk from uncertain observation | 0.428000 | 0.054600 |
| D: Sara conceptual-difficulty hypothesis | 0.458333 | 0.295306 |
| E: Hana risk before new evidence | 0.568810 | 0.347673 |
| E: Hana risk after new evidence | 0.449621 | 0.293248 |
| F: True four-hop intervention | 0.429741 | 0.036383 |
| G: Induced LowQuiz -> WeakPrerequisite | 0.272222 | 0.297256 |
| G: Induced rule applied to Sara | 0.221778 | 0.048552 |

Scenario E consolidates assignment strengths 0.80 and 0.30 to <0.514286,0.875000> before rebuilding downstream proofs. The existing risk and intervention both change; repeating the run changes neither. Scenario F isolates the authored four-link pathway: confidence decreases 0.900000 -> 0.619650 -> 0.342146 -> 0.132964 -> 0.036383. Scenario G generates a new reverse relationship from cohort estimates and consumes it in a Sara query while preserving cohort and prior support.

Scenario H checks three forward/backward answers at depth four. Their STVs agree within 1e-12 and their evidence sets are identical. The verification suite passes 20 MeTTa assertions and 33 Python regression tests, including evidence corrections and retractions, partial overlap, source uniqueness, cycles, zero confidence, derived-rule use, scientific notation, invalid probabilities, resource bounds and intentionally failing assertions.

## 5. Limitations

Illustrative strengths are not calibrated forecasts. Independence is a modeling assumption, not something established by distinct evidence IDs. Greedy disjoint-proof selection is conservative and may omit useful partially overlapping information. Revision occurs after path enumeration at the queried statement; consolidated intermediate beliefs are not reused as independent source proofs. Hypothesis strengths are neither mutually exclusive nor normalized. The engine supports unary evaluations and concept implications rather than unrestricted first-order reasoning. Depth and proof budgets bound search, so an unsupported query does not establish falsity. No causal diagnosis or autonomous intervention decision is claimed.

Formula reference: TrueAGI PLN, lib_pln.metta, https://github.com/trueagi-io/PLN. The README states the adopted confidence formulas and the prior-confidence extensions explicitly.
