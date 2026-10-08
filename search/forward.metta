;; Forward Chaining Step Definitions

!(import! &self pln:rules)

;; 1. Deduction Step
;; A(x) + (A -> B) => B(x)
(= (step-deduction (Fact (Evaluation $A $x) $tvFact $provFact)
                   (Rule (Implication $A $B) $tvRule))
   (let $newTv (deduction $tvFact $tvRule)
   (let $newProv (Derived Deduction 
                          (Fact (Evaluation $A $x) $tvFact $provFact) 
                          (Rule (Implication $A $B) $tvRule))
      (Fact (Evaluation $B $x) $newTv $newProv))))

;; Get all possible forward deduction steps from the current space
(= (forward-step)
   (match &self (Fact (Evaluation $A $x) $tvFact $provFact)
      (match &self (Rule (Implication $A $B) $tvRule)
         (step-deduction (Fact (Evaluation $A $x) $tvFact $provFact) (Rule (Implication $A $B) $tvRule))
      )
   )
)
