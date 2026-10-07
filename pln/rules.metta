;; PLN Inference Rules

;; Absolute value helper
(= (abs $x)
   (if (< $x 0.0) (* -1.0 $x) $x))

;; Conflict calculation
(= (conflict-level (stv $s1 $c1) (stv $s2 $c2))
   (abs (- $s1 $s2)))

;; Revision rule: Merges independent evidence
(= (revision (stv $s1 $c1) (stv $s2 $c2))
   (let $w1 (c2w $c1)
   (let $w2 (c2w $c2)
   (let $wTotal (+ $w1 $w2)
   (if (== $wTotal 0.0)
       (stv 0.5 0.0) ;; default when no confidence
       (let $sRev (/ (+ (* $s1 $w1) (* $s2 $w2)) $wTotal)
       (let $cRev (w2c $wTotal)
          (stv $sRev $cRev))))))))

;; Simplified probabilistic deduction
(= (deduction (stv $s1 $c1) (stv $s2 $c2))
   (stv (* $s1 $s2) (* $c1 $c2)))

;; Simplified probabilistic induction
(= (induction (stv $s1 $c1) (stv $s2 $c2))
   (stv (* $s1 $s2) (* (* $c1 $c2) 0.5)))

;; Simplified probabilistic abduction
(= (abduction (stv $s1 $c1) (stv $s2 $c2))
   (stv (* $s1 $s2) (* (* $c1 $c2) 0.5)))
