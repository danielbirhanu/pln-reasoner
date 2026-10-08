import os
from hyperon import MeTTa

class PLNSearchEngine:
    def __init__(self):
        self.metta = MeTTa()
        
        # Load the entire KB and rules
        self._load_file("main.metta")
        self._load_file("search/forward.metta")
        self._load_file("search/backward.metta")
        
        self.derived_facts = set()

    def _load_file(self, filepath):
        with open(filepath) as f:
            self.metta.run(f.read())

    def forward_chain(self, max_depth=3):
        
        print("\n--- FORWARD CHAINING ---")
        
        for depth in range(max_depth):
            print(f"\nDepth {depth+1}:")
            # Ask MeTTa to compute the next frontier of deductive steps
            results = self.metta.run("!(forward-step)")
            
            new_inferences = 0
            for expr_list in results:
                for fact in expr_list:
                    # Convert to string to easily check duplicates and add to space
                    fact_str = str(fact)
                    
                    # Avoid duplicates/cycles
                    if fact_str not in self.derived_facts and "Derived" in fact_str:
                        self.derived_facts.add(fact_str)
                        new_inferences += 1
                        
                        # Add the new fact back into the MeTTa space so it can be used in the next depth
                        self.metta.run(f"!(add-atom &self {fact_str})")
                        print(f"Derived: {fact_str}")
            
    def backward_chain(self, target_expr, max_depth=3):
        
        print(f"\n--- BACKWARD CHAINING for: {target_expr} ---")
        proof = self._backward_search(target_expr, depth=0, max_depth=max_depth)
        if proof:
            print(f"\nProof Found: {proof}")
        else:
            print("\nProof Failed.")
            
    def _backward_search(self, target_expr, depth, max_depth):
        if depth >= max_depth:
            return None
            
        # First, check if the target is already a known fact in the space
        known_results = self.metta.run(f"!(match &self (Fact {target_expr} $tv $prov) (Fact {target_expr} $tv $prov))")
        for res_list in known_results:
            for fact in res_list:
                return str(fact)
                
        # If not known, ask MeTTa what premises would imply this target
        premises = self.metta.run(f"!(backward-step {target_expr})")
        
        for premise_list in premises:
            for premise in premise_list:
                premise_str = str(premise)
                # Recursively try to prove the premise
                sub_proof = self._backward_search(premise_str, depth + 1, max_depth)
                if sub_proof:
                    # If we proved the premise, we have found a proof path
                    return f"Derived via Rule -> {sub_proof}"
                    
        return None

if __name__ == "__main__":
    engine = PLNSearchEngine()
    engine.forward_chain()
    engine.backward_chain("(Evaluation AcademicIntervention Hana)", max_depth=5)
