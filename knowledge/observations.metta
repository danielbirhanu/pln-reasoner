;; Student Observations / Evidence

;; Hana
(Fact (Evaluation WeakPrerequisiteTest Hana) (stv 0.90 0.90))
(Fact (Evaluation LowQuizPerformance Hana) (stv 0.85 0.85))
(Fact (Evaluation LowAssignmentCompletion Hana) (stv 0.80 0.75))

;; Abel
(Fact (Evaluation LowAttendance Abel) (stv 0.95 0.90))
(Fact (Evaluation LowParticipation Abel) (stv 0.85 0.80))

;; Sara
(Fact (Evaluation LowQuizPerformance Sara) (stv 0.80 0.75))

;; Dawit (Incomplete/Uncertain Evidence)
(Fact (Evaluation LowParticipation Dawit) (stv 0.65 0.25))

;; Miki
(Fact (Evaluation GoodQuizPerformance Miki) (stv 0.90 0.85))
(Fact (Evaluation GoodParticipation Miki) (stv 0.95 0.90))

;; Conflicting Evidence Example
(Fact (Evaluation TeacherEvidence ConflictingStudent) (stv 0.90 0.80))
(Fact (Evaluation AssessmentEvidence ConflictingStudent) (stv 0.30 0.70))
