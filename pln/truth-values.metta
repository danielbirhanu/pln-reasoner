;; Truth Value Representation and Utilities

;; Convert confidence to evidence weight
(= (c2w $c)
   (/ $c (- 1.0 $c)))

;; Convert evidence weight to confidence
(= (w2c $w)
   (/ $w (+ $w 1.0)))

;; Helper to extract strength and confidence from an STV
(= (get-strength (stv $s $c)) $s)
(= (get-confidence (stv $s $c)) $c)
