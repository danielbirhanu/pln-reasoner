;; Tests for PLN Inference Rules

!(import! &self pln:truth-values)
!(import! &self pln:rules)

;; Test: absolute value helper
!(assertEqualToResult (abs -0.5) (0.5))
!(assertEqualToResult (abs 0.3) (0.3))

;; Test: Conflict level
!(assertEqualToResult (conflict-level (stv 0.9 0.8) (stv 0.3 0.7)) (0.6))
!(assertEqualToResult (conflict-level (stv 0.3 0.7) (stv 0.9 0.8)) (0.6))

;; Test: Deduction
!(assertEqualToResult (deduction (stv 0.9 0.9) (stv 0.85 0.8)) (stv 0.765 0.72))

;; Test: Induction and Abduction 
!(assertEqualToResult (induction (stv 0.9 0.9) (stv 0.85 0.8)) (stv 0.765 0.36))
!(assertEqualToResult (abduction (stv 0.9 0.9) (stv 0.85 0.8)) (stv 0.765 0.36))

;; Test: Revision
;; Case 1: Identical confidence
!(assertEqualToResult (revision (stv 1.0 0.5) (stv 0.0 0.5)) (stv 0.5 (/ 2.0 3.0)))

;; Case 2: Different confidence pulls strength towards the higher confidence
!(assertEqualToResult (revision (stv 1.0 0.75) (stv 0.0 0.5)) (stv 0.75 0.8))
