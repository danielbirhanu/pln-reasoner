# Domain knowledge semantics

The reference population is students in an illustrative education setting. Values are chosen to demonstrate inference under uncertainty; no historical dataset or calibration is claimed.

## Entities and propositions

Students are Hana, Abel, Sara, Dawit and Miki. `CohortA`, used only in the induction demonstration, is a subpopulation rather than an individual student. New student symbols are allowed in evidence-ingestion calls.

| Concept | Meaning of a high proposition strength |
|---|---|
| WeakPrerequisiteTest | Evidence from a prerequisite assessment suggests a weakness |
| WeakPrerequisiteKnowledge | The student may lack prerequisite knowledge |
| ConceptualDifficulty | The student may struggle with the current concepts |
| AcademicRisk | The student may need attention because of academic difficulty |
| AcademicIntervention | Additional academic support may be appropriate |
| LowEngagement | Evidence suggests limited engagement |
| LowAssignmentCompletion | Evidence supports incomplete assignment work |
| LowQuizPerformance | Evidence supports difficulty in quiz performance |
| LowAttendance / LowParticipation | Observed attendance/participation concerns; no risk implications are supplied |
| GoodQuizPerformance / GoodParticipation | Positive observed performance/participation; no automatic negation of risk |

Absence of an implication is intentional missing model knowledge, not a negative conclusion. For example, Dawit's participation observation cannot establish risk without a relevant relationship.

## Source representation

```lisp
(Fact (Evaluation LowAssignmentCompletion Hana)
      (stv 0.8 0.75) (BaseEvidence assignment-001))
(Rule (Implication LowAssignmentCompletion AcademicRisk)
      (stv 0.7 0.65) (BaseEvidence rule-assignment-risk))
(Fact (Prior AcademicRisk)
      (stv 0.35 0.9) (BaseEvidence prior-risk))
```

The evaluation strength is belief that the named proposition holds for that learner; it is not an assignment percentage. The rule strength is the contextual conditional estimate `P(AcademicRisk|LowAssignmentCompletion)`. The prior strength is the population marginal `P(AcademicRisk)`. Confidence describes evidential support for each estimate. With `k=1`, confidence `.75` represents weight `3`, and `.9` represents weight `9`; these are illustrative equivalent weights, not actual sample sizes.

Every raw fact, prior and rule has a globally unique, stable evidence identifier. IDs on observations distinguish records, not people. A corrected record retains its identity; a genuinely independent additional observation gets a new ID. Repeated use of the same rule or prior retains its support ID throughout a proof.

## Cohort representation

```lisp
(Fact (Prior CohortA) (stv 0.10 0.90) (BaseEvidence prior-cohort))
(CohortConditional CohortA WeakPrerequisiteKnowledge
                   (stv 0.85 0.90) (BaseEvidence cohort-prerequisite))
(CohortConditional CohortA LowQuizPerformance
                   (stv 0.80 0.90) (BaseEvidence cohort-quiz))
```

The first strength means 10% of the reference population belongs to the cohort. The next two mean `P(WeakPrerequisiteKnowledge|CohortA)=.85` and `P(LowQuizPerformance|CohortA)=.80`. These aggregate estimates and the population priors support induction under the stated conditional-independence assumptions. No automatic dataset mining or cohort-size estimation is implemented.

## Evidence and assumptions

All conditional estimates with supplied priors must satisfy both joint-probability bounds. Revision assumes independent observational support; rule and prior support are also tracked to reject overlapping proof revision conservatively. Deduction and induction use the conditional-independence assumptions in the main README. Modus ponens uses an explicit background `.02`. Abduction returns possible explanations rather than confirmed causes. Full numerical results and nested proof trees are available in `results/scenarios.json`.
