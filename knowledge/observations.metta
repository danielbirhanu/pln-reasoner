;; Student Observations / Evidence

;; Hana
(Fact (Evaluation WeakPrerequisiteTest Hana) (stv 0.90 0.90) (BaseEvidence quiz-001))
(Fact (Evaluation LowQuizPerformance Hana) (stv 0.85 0.85) (BaseEvidence quiz-002))
(Fact (Evaluation LowAssignmentCompletion Hana) (stv 0.80 0.75) (BaseEvidence assignment-001))

;; Abel
(Fact (Evaluation LowAttendance Abel) (stv 0.95 0.90) (BaseEvidence attendance-001))
(Fact (Evaluation LowParticipation Abel) (stv 0.85 0.80) (BaseEvidence teacher-001))

;; Sara
(Fact (Evaluation LowQuizPerformance Sara) (stv 0.80 0.75) (BaseEvidence quiz-003))

;; Dawit (Incomplete/Uncertain Evidence)
(Fact (Evaluation LowParticipation Dawit) (stv 0.65 0.25) (BaseEvidence teacher-002))

;; Miki
(Fact (Evaluation GoodQuizPerformance Miki) (stv 0.90 0.85) (BaseEvidence quiz-004))
(Fact (Evaluation GoodParticipation Miki) (stv 0.95 0.90) (BaseEvidence teacher-003))

;; Conflicting Evidence Example
(Fact (Evaluation TeacherEvidence ConflictingStudent) (stv 0.90 0.80) (BaseEvidence teacher-004))
(Fact (Evaluation AssessmentEvidence ConflictingStudent) (stv 0.30 0.70) (BaseEvidence assessment-001))
