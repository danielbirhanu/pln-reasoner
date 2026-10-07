;; Tests for Truth Value representations


!(import! &self pln:truth-values)

;; Test: c2w (confidence to weight)
!(assertEqualToResult (c2w 0.5) (1.0))

!(assertEqualToResult (c2w 0.75) (3.0))

!(assertEqualToResult (c2w 0.8) (4.0))

!(assertEqualToResult (c2w 0.9) (9.0))

;; Test: w2c (weight to confidence)
!(assertEqualToResult (w2c 1.0) (0.5))

!(assertEqualToResult (w2c 3.0) (0.75))

!(assertEqualToResult (w2c (c2w 0.75)) (0.75))

;; Test: Extraction helpers
!(assertEqualToResult (get-strength (stv 0.8 0.6)) (0.8))
!(assertEqualToResult (get-confidence (stv 0.8 0.6)) (0.6))
