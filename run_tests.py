import sys
import glob
from hyperon import MeTTa

def run_all_tests():
    
    test_files = glob.glob("tests/*.metta")
    all_passed = True
    
    for f in test_files:
        print(f"Running {f}...")
        try:
            metta = MeTTa()
            with open(f) as file:
                program = file.read()
            metta.run(program)
            print(f"[OK] {f}")
        except Exception as e:
            print(f"[FAIL] {f}\n{e}")
            all_passed = False

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
