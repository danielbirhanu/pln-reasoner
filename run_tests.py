"""Fail on no discovery, MeTTa assertion errors or Python regression failures."""
from pathlib import Path
import sys
import unittest
from hyperon import MeTTa, ExpressionAtom

ROOT = Path(__file__).resolve().parent


def run_metta_files(files):
    if not files:
        raise ValueError("No MeTTa test files discovered")
    assertions = 0
    for file in files:
        file = Path(file)
        source = file.read_text()
        count = source.count("!(assertEqual ")
        if count == 0:
            raise ValueError(f"No assertions found in {file.name}")
        m = MeTTa()
        for module in ("pln/truth-values.metta", "pln/rules.metta"):
            m.run((ROOT / module).read_text())
        source = "\n".join(line for line in source.splitlines() if not line.startswith("!(import!"))
        results = m.run(source)
        if len(results) != count:
            raise AssertionError(f"Expected {count} assertion results, received {len(results)}")
        for group in results:
            if not group or any(isinstance(a, ExpressionAtom) and a.get_children()
                                and str(a.get_children()[0]) == "Error" for a in group):
                raise AssertionError(f"MeTTa assertion failed in {file.name}: {group}")
        assertions += count
        print(f"[OK] {file.name}: {count} assertions")
    return assertions


def main():
    try:
        count = run_metta_files(sorted((ROOT / "tests").glob("*-tests.metta")))
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
        if suite.countTestCases() == 0:
            raise ValueError("No Python regression tests discovered")
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            return 1
        print(f"PASS: {count} MeTTa assertions and {result.testsRun} Python regression tests")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
