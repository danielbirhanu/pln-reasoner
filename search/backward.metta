;; Backward Chaining Step Definitions

!(import! &self pln:rules)

;; Given a target B(x), what A(x) do we need to prove it via A -> B?
(= (backward-step (Evaluation $B $x))
   (match &self (Rule (Implication $A $B) $tvRule)
      (Evaluation $A $x)
   )
)
