# Education Probabilistic Logic Network

A lightweight Probabilistic Logic Network (PLN) engine for reasoning about student academic risk and support. It uses **MeTTa** for truth-value arithmetic and knowledge representation, and **Python** for bounded forward and backward search.

> **Note**: This is an illustrative educational project demonstrating uncertain reasoning. It does not claim predictive accuracy or make automated decisions about students.

## Quick Start

### Requirements
- **Python 3.12+**
- **Hyperon 0.2.10**

### Setup & Run
Open a terminal in the `pln-reasoner` directory and run:

```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Run the test suite and scenarios
python run_tests.py
python tests/scenarios.py
```

## Example Usage

You can use the engine programmatically in Python to query beliefs, add new evidence, and trace reasoning paths:

```python
from search.engine import PLNSearchEngine

engine = PLNSearchEngine()

# Forward chain to deduce conclusions based on existing knowledge
beliefs = engine.forward_chain(max_depth=4)
print(beliefs['(Evaluation AcademicRisk Hana)'].stv)

# Backward chain to verify a specific hypothesis
answer = engine.backward_chain('(Evaluation AcademicRisk Hana)', max_depth=4)
print(answer.stv)
print(answer.atom)  # Complete proof tree with evidence IDs

# Add new observation and observe revised belief
engine.add_observation('LowAssignmentCompletion', 'Hana', 0.3, 0.8, 'teacher-assignment-new')
updated = engine.forward_chain(max_depth=4)
print(updated['(Evaluation AcademicRisk Hana)'].stv)
```

## Project Structure

| Area | Description |
|---|---|
| `knowledge/` | Educational rules, entities, and cohort observations. |
| `pln/` | Core logic modules (`rules.metta`, `truth-values.metta`). |
| `search/` | Python controller (`engine.py`) and MeTTa matchers (`forward.metta`, `backward.metta`). |
| `tests/` | Comprehensive test suite and demonstration scenarios. |
| `report.pdf` | Detailed technical report on inference operations and mathematics. |

## Core Features

- **Evidence Accounting**: Consolidates multiple independent observations via Belief Revision, while automatically pruning overlapping proof paths to prevent double-counting.
- **Four Inference Operations**: Natively supports Modus Ponens, Relationship Deduction, Induction (from cohort datasets), and Diagnostic Abduction.
- **Mathematical Rigor**: Strictly enforces conditional probability bounds, rejects inconsistent priors, and safely handles undefined probabilities (e.g. division by zero).
- **Forward & Backward Agreement**: Forward searches consolidate all available evidence, while backward searches efficiently extract individual sufficient proof pathways. 

*For a deep dive into the mathematical algebra and exact testing scenarios, please refer to the `report.pdf` or the source code.*
