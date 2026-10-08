(= (forward-candidates $A)
   (match &self (Rule (Implication $A $B) $tv $prov)
      (Rule (Implication $A $B) $tv $prov)))
