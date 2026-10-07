;; Tests for Knowledge Base

!(import! &self knowledge:students)
!(import! &self knowledge:observations)
!(import! &self knowledge:education-rules)

;; Ensure facts and rules loaded correctly by matching them out of the Space
!(assertEqual (match &self (Fact (Evaluation WeakPrerequisiteTest Hana) $tv) $tv) (stv 0.90 0.90))
!(assertEqual (match &self (Rule (Implication ConceptualDifficulty AcademicRisk) $tv) $tv) (stv 0.80 0.70))
