;; Educational Rules and Probabilistic Implications

;; Expected logical chain for inference testing:
(Rule (Implication WeakPrerequisiteTest WeakPrerequisiteKnowledge) (stv 0.90 0.85))
(Rule (Implication WeakPrerequisiteKnowledge ConceptualDifficulty) (stv 0.85 0.80))
(Rule (Implication ConceptualDifficulty AcademicRisk) (stv 0.80 0.70))
(Rule (Implication AcademicRisk AcademicIntervention) (stv 0.75 0.65))

;; Additional pathways to risk
(Rule (Implication LowEngagement AcademicRisk) (stv 0.75 0.60))
(Rule (Implication LowAssignmentCompletion AcademicRisk) (stv 0.70 0.65))

;; Rules for Abduction (competing hypotheses for LowQuizPerformance)
(Rule (Implication WeakPrerequisiteKnowledge LowQuizPerformance) (stv 0.85 0.80))
(Rule (Implication LowEngagement LowQuizPerformance) (stv 0.75 0.70))
(Rule (Implication ConceptualDifficulty LowQuizPerformance) (stv 0.90 0.85))
