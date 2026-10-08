"""MeTTa algebra and matching, with deterministic bounded Python search."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, replace
from itertools import combinations
import math
from pathlib import Path
import re
import sys

from hyperon import MeTTa, ExpressionAtom, GroundedAtom, SymbolAtom

SOURCE_ROOT = Path(__file__).resolve().parents[1]
ROOT = SOURCE_ROOT if (SOURCE_ROOT / "pln").is_dir() else Path(sys.prefix) / "share" / "education-pln-reasoner"
TV = tuple[float, float]


def validate_stv(tv: TV) -> TV:
    if len(tv) != 2 or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in tv):
        raise ValueError("STV must contain two numeric values")
    s, c = map(float, tv)
    if not (math.isfinite(s) and math.isfinite(c) and 0 <= s <= 1 and 0 <= c < 1):
        raise ValueError(f"Invalid STV {tv}: require finite 0<=s<=1 and 0<=c<1")
    return s, c


def symbol(text: str) -> str:
    if not isinstance(text, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", text):
        raise ValueError(f"Expected a simple domain symbol, received {text!r}")
    return text


def children(atom, head=None, count=None):
    if not isinstance(atom, ExpressionAtom):
        raise ValueError(f"Expected an expression, received {atom}")
    parts = atom.get_children()
    if head is not None and (not parts or str(parts[0]) != head):
        raise ValueError(f"Expected {head}, received {atom}")
    if count is not None and len(parts) != count:
        raise ValueError(f"Wrong arity for {atom}")
    return parts


def numeric(atom):
    if not isinstance(atom, GroundedAtom):
        raise ValueError(f"Expected a numeric atom, received {atom}")
    value = atom.get_object().value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Expected a number, received {value!r}")
    return float(value)


def atom_stv(atom) -> TV:
    _, s, c = children(atom, "stv", 3)
    return validate_stv((numeric(s), numeric(c)))


def tv_text(tv: TV) -> str:
    s, c = validate_stv(tv)
    return f"(stv {s:.17g} {c:.17g})"


@dataclass(frozen=True)
class Record:
    kind: str
    args: tuple[str, ...]
    tv: TV
    evidence_id: str


@dataclass(frozen=True)
class Proof:
    statement: str
    stv: TV
    evidence: frozenset[str]
    visited: frozenset[str]
    hops: int
    provenance: str

    @property
    def atom(self):
        return f"(Fact {self.statement} {tv_text(self.stv)} {self.provenance})"

    def as_dict(self):
        return {"statement": self.statement, "strength": self.stv[0],
                "confidence": self.stv[1], "support": sorted(self.evidence),
                "hops": self.hops, "proof": self.atom}


@dataclass(frozen=True)
class RuleProof:
    nodes: tuple[str, ...]
    stv: TV
    evidence: frozenset[str]
    provenance: str
    operation: str = "Base"

    @property
    def hops(self):
        return len(self.nodes) - 1

    @property
    def atom(self):
        return (f"(Rule (Implication {self.nodes[0]} {self.nodes[-1]}) "
                f"{tv_text(self.stv)} {self.provenance})")


class PLNSearchEngine:
    def __init__(self, load_domain=True, max_paths=10000):
        if not isinstance(max_paths, int) or isinstance(max_paths, bool) or max_paths < 1:
            raise ValueError("max_paths must be a positive integer")
        self.max_paths = max_paths
        self.records: dict[str, Record] = {}
        self.canonical_beliefs = {}
        self.proofs: dict[str, Proof] = {}
        self.learned_rules: list[RuleProof] = []
        self._rule_cache = {}
        self._reset_space()
        if load_domain:
            for filename in ("students.metta", "education-rules.metta", "observations.metta"):
                self.load_knowledge(ROOT / "knowledge" / filename)

    def _reset_space(self):
        self.metta = MeTTa()
        for filename in ("pln/truth-values.metta", "pln/rules.metta",
                         "search/forward.metta", "search/backward.metta"):
            results = self.metta.run((ROOT / filename).read_text())
            self._check_errors(results)

    @staticmethod
    def _check_errors(results):
        for group in results:
            for atom in group:
                if isinstance(atom, ExpressionAtom) and atom.get_children() and str(atom.get_children()[0]) == "Error":
                    raise ValueError(str(atom))

    def calculate(self, operation: str, *truth_values: TV) -> TV:
        if operation not in {"revision", "modus-ponens", "relationship-deduction", "induction", "abduction"}:
            raise ValueError("Unknown inference operation")
        arities = {"revision": 2, "modus-ponens": 2, "relationship-deduction": 5,
                   "induction": 5, "abduction": 4}
        if len(truth_values) != arities[operation]:
            raise ValueError(f"{operation} needs {arities[operation]} STVs")
        query = f"!({operation} {' '.join(tv_text(v) for v in truth_values)})"
        results = self.metta.run(query)
        self._check_errors(results)
        flat = [a for group in results for a in group]
        if len(flat) != 1:
            raise ValueError(f"Inference did not return exactly one STV: {results}")
        return atom_stv(flat[0])

    def _extract_stv(self, expression: str) -> TV:
        """Compatibility helper; parse structurally and fail explicitly."""
        atoms = self.metta.parse_all(expression)
        if len(atoms) != 1:
            raise ValueError("Expected exactly one expression")
        top = children(atoms[0])
        if str(top[0]) == "stv":
            return atom_stv(atoms[0])
        if str(top[0]) in {"Fact", "Rule"} and len(top) == 4:
            return atom_stv(top[2])
        raise ValueError("No top-level STV found")

    def _put(self, record: Record):
        validate_stv(record.tv)
        for arg in record.args:
            symbol(arg)
        symbol(record.evidence_id)
        old = self.records.get(record.evidence_id)
        if old is not None and old != record:
            raise ValueError("Evidence ID already exists; use replace_observation to correct a record")
        self.records[record.evidence_id] = record
        self.proofs = {}
        self.canonical_beliefs = {}

    def load_knowledge(self, path: Path):
        """Read literal source atoms without executing uploaded knowledge as code."""
        for atom in self.metta.parse_all(Path(path).read_text()):
            p = children(atom)
            head = str(p[0])
            if head in {"Type", "Student"}:
                continue
            if head not in {"Fact", "Rule", "CohortConditional"}:
                raise ValueError(f"Unsupported source record {atom}")
            if head == "CohortConditional":
                if len(p) != 5:
                    raise ValueError("CohortConditional needs cohort, concept, STV and provenance")
                args, tv_atom, prov = (str(p[1]), str(p[2])), p[3], p[4]
                kind = "Cohort"
            else:
                if len(p) != 4:
                    raise ValueError("All facts and rules require explicit evidence provenance")
                statement = children(p[1])
                tag = str(statement[0])
                if head == "Rule" and tag == "Implication" and len(statement) == 3:
                    kind, args = "Rule", (str(statement[1]), str(statement[2]))
                elif head == "Fact" and tag == "Evaluation" and len(statement) == 3:
                    kind, args = "Observation", (str(statement[1]), str(statement[2]))
                elif head == "Fact" and tag == "Prior" and len(statement) == 2:
                    kind, args = "Prior", (str(statement[1]),)
                else:
                    raise ValueError(f"Unsupported statement {p[1]}")
                tv_atom, prov = p[2], p[3]
            evidence = children(prov, "BaseEvidence", 2)
            self._put(Record(kind, args, atom_stv(tv_atom), str(evidence[1])))
        self._validate_domain()

    def add_observation(self, concept, entity, strength, confidence, evidence_id):
        self._put(Record("Observation", (concept, entity), validate_stv((strength, confidence)), evidence_id))

    def replace_observation(self, evidence_id, strength, confidence):
        old = self.records.get(evidence_id)
        if old is None or old.kind != "Observation":
            raise ValueError("Unknown observation evidence ID")
        self.records[evidence_id] = replace(old, tv=validate_stv((strength, confidence)))
        self.proofs = {}
        self.canonical_beliefs = {}

    def remove_observation(self, evidence_id):
        if evidence_id not in self.records or self.records[evidence_id].kind != "Observation":
            raise ValueError("Unknown observation evidence ID")
        del self.records[evidence_id]
        self.proofs = {}
        self.canonical_beliefs = {}

    def add_rule(self, source, target, strength, confidence, evidence_id):
        if source == target:
            raise ValueError("Self implications are not useful source rules")
        record = Record("Rule", (source, target), validate_stv((strength, confidence)), evidence_id)
        self._check_record_conditional(record)
        self._put(record)

    def add_prior(self, concept, strength, confidence, evidence_id):
        if any(r.kind == "Prior" and r.args == (concept,) for r in self.records.values()):
            raise ValueError("One contextual prior per concept is supported")
        record = Record("Prior", (concept,), validate_stv((strength, confidence)), evidence_id)
        symbol(concept); symbol(evidence_id)
        proposed = {**self.records, evidence_id: record}
        self._validate_domain(proposed)
        self._put(record)

    def add_cohort(self, cohort, concept, strength, confidence, evidence_id):
        if any(r.kind == "Cohort" and r.args == (cohort, concept) for r in self.records.values()):
            raise ValueError("One conditional estimate per cohort/concept is supported")
        record = Record("Cohort", (cohort, concept), validate_stv((strength, confidence)), evidence_id)
        self._check_record_conditional(record)
        self._put(record)

    def _priors(self, records=None):
        return {r.args[0]: r for r in (self.records if records is None else records).values() if r.kind == "Prior"}

    def _check_record_conditional(self, r, records=None):
        priors = self._priors(records)
        a, b = r.args
        if a in priors and b in priors:
            pA, pB, q = priors[a].tv[0], priors[b].tv[0], r.tv[0]
            joint = pA * q
            if not max(0.0, pA + pB - 1.0) - 1e-12 <= joint <= min(pA, pB) + 1e-12:
                raise ValueError(f"Inconsistent conditional for {a}->{b}")

    def _validate_domain(self, records=None):
        records = self.records if records is None else records
        priors = [r.args for r in records.values() if r.kind == "Prior"]
        if len(priors) != len(set(priors)):
            raise ValueError("Duplicate contextual priors")
        for r in records.values():
            if r.kind in {"Rule", "Cohort"}:
                self._check_record_conditional(r, records)

    @staticmethod
    def _rank(p):
        return (-p.stv[1], p.hops, tuple(sorted(p.evidence)), p.provenance)

    def _combine(self, candidates: list[Proof]) -> Proof | None:
        """Greedy deterministic disjoint selection, starting with best confidence.

        Partially overlapping alternatives are retained as candidates but not
        independently revised. Shared rule/prior IDs also count as overlap.
        """
        selected = None
        for candidate in sorted(candidates, key=self._rank):
            if candidate.stv[1] == 0:
                continue
            if selected is None:
                selected = candidate
            elif selected.evidence.isdisjoint(candidate.evidence):
                selected = Proof(selected.statement,
                                 self.calculate("revision", selected.stv, candidate.stv),
                                 selected.evidence | candidate.evidence,
                                 selected.visited | candidate.visited,
                                 max(selected.hops, candidate.hops),
                                 f"(Revised {selected.atom} {candidate.atom})")
        return selected

    @staticmethod
    def _prior_atom(r):
        return f"(Fact (Prior {r.args[0]}) {tv_text(r.tv)} (BaseEvidence {r.evidence_id}))"

    def _base_beliefs(self):
        grouped = defaultdict(list)
        for r in self.records.values():
            if r.kind != "Observation":
                continue
            statement = f"(Evaluation {r.args[0]} {r.args[1]})"
            grouped[statement].append(Proof(statement, r.tv, frozenset({r.evidence_id}),
                                            frozenset({statement}), 0, f"(BaseEvidence {r.evidence_id})"))
        return {stmt: p for stmt, values in sorted(grouped.items()) if (p := self._combine(values)) is not None}

    def _build_rules(self, max_depth):
        cache_key = (max_depth, tuple(sorted((r for r in self.records.values()
                                              if r.kind != "Observation"), key=lambda r: r.evidence_id)))
        if cache_key in self._rule_cache:
            active, learned = self._rule_cache[cache_key]
            self.learned_rules = learned
            self._rule_by_atom = {str(self.metta.parse_single(r.atom)): r for r in active}
            for atom in sorted(self._rule_by_atom):
                self.metta.space().add_atom(self.metta.parse_single(atom))
            return
        priors = self._priors()
        base_edges = set()
        rules = {}

        def put(r):
            key = (r.nodes, r.evidence, tuple(round(v, 14) for v in r.stv), r.operation)
            if r.stv[1] > 0 and key not in rules:
                if len(rules) >= self.max_paths:
                    raise RuntimeError("Rule budget exceeded; narrow the KB or depth")
                rules[key] = r
                return True
            return False

        for r in sorted(self.records.values(), key=lambda r: r.evidence_id):
            if r.kind == "Rule":
                base_edges.add(r.args)
                put(RuleProof(r.args, r.tv, frozenset({r.evidence_id}), f"(BaseEvidence {r.evidence_id})"))

        cohorts = defaultdict(list)
        for r in self.records.values():
            if r.kind == "Cohort":
                cohorts[r.args[0]].append(r)
        for cohort, estimates in sorted(cohorts.items()):
            for left, right in combinations(sorted(estimates, key=lambda r: r.args), 2):
                for a, b in ((left, right), (right, left)):
                    names = (cohort, a.args[1], b.args[1])
                    if not all(n in priors for n in names):
                        raise ValueError("Cohort induction requires cohort and both concept priors")
                    ps = [priors[n] for n in names]
                    tv = self.calculate("induction", a.tv, b.tv, *(p.tv for p in ps))
                    provenance = (f"(Derived Induction (CohortConditional {cohort} {a.args[1]} {tv_text(a.tv)} "
                                  f"(BaseEvidence {a.evidence_id})) (CohortConditional {cohort} {b.args[1]} "
                                  f"{tv_text(b.tv)} (BaseEvidence {b.evidence_id})) "
                                  + " ".join(self._prior_atom(p) for p in ps) + ")")
                    put(RuleProof((a.args[1], b.args[1]), tv,
                                  frozenset({a.evidence_id, b.evidence_id, *(p.evidence_id for p in ps)}),
                                  provenance, "Induction"))

        while True:
            additions = False
            snapshot = list(rules.values())
            usable = [r for r in snapshot if r.operation == "Base" or (r.nodes[0], r.nodes[-1]) not in base_edges]
            for ab in usable:
                for bc in usable:
                    if ab.nodes[-1] != bc.nodes[0] or ab.hops + bc.hops > max_depth:
                        continue
                    if set(ab.nodes[:-1]) & set(bc.nodes[1:]):
                        continue 
                    if not ab.evidence.isdisjoint(bc.evidence):
                        continue
                    names = (ab.nodes[0], ab.nodes[-1], bc.nodes[-1])
                    if not all(n in priors for n in names):
                        continue
                    ps = [priors[n] for n in names]
                    try:
                        tv = self.calculate("relationship-deduction", ab.stv, bc.stv, *(p.tv for p in ps))
                    except ValueError as exc:
                        if "InconsistentProbabilities" in str(exc) or "UndefinedConditional" in str(exc):
                            continue 
                        raise
                    provenance = f"(Derived RelationshipDeduction {ab.atom} {bc.atom} " + " ".join(self._prior_atom(p) for p in ps) + ")"
                    additions |= put(RuleProof(ab.nodes + bc.nodes[1:], tv,
                                               ab.evidence | bc.evidence | frozenset(p.evidence_id for p in ps),
                                               provenance, "RelationshipDeduction"))
            if not additions:
                break
        self.learned_rules = sorted((r for r in rules.values() if r.operation != "Base"), key=self._rank)
        active = [r for r in rules.values() if r.operation == "Base" or (r.nodes[0], r.nodes[-1]) not in base_edges]
        self._rule_cache[cache_key] = (active, self.learned_rules)
        self._rule_by_atom = {str(self.metta.parse_single(r.atom)): r for r in active}
        for atom in sorted(self._rule_by_atom):
            self.metta.space().add_atom(self.metta.parse_single(atom))

    @staticmethod
    def _depth(value):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("max_depth must be a non-negative integer")

    def _prepare(self, max_depth):
        self._depth(max_depth)
        self._validate_domain()
        self._reset_space()
        self._bases = self._base_beliefs()
        for r in self.records.values():
            if r.kind == "Prior":
                self.metta.space().add_atom(self.metta.parse_single(self._prior_atom(r)))
            elif r.kind == "Observation":
                atom = f"(Observation (Evaluation {r.args[0]} {r.args[1]}) {tv_text(r.tv)} (BaseEvidence {r.evidence_id}))"
                self.metta.space().add_atom(self.metta.parse_single(atom))
        self._build_rules(max_depth)

    def _matching_rules(self, concept, backward=False):
        function = "backward-candidates" if backward else "forward-candidates"
        results = self.metta.run(f"!({function} {symbol(concept)})")
        self._check_errors(results)
        return sorted((self._rule_by_atom[str(a)] for group in results for a in group), key=self._rank)

    def _apply(self, premise: Proof, rule: RuleProof, entity: str):
        targets = frozenset(f"(Evaluation {n} {entity})" for n in rule.nodes[1:])
        if premise.visited & targets or not premise.evidence.isdisjoint(rule.evidence):
            return None
        tv = self.calculate("modus-ponens", premise.stv, rule.stv)
        if tv[1] == 0:
            return None
        statement = f"(Evaluation {rule.nodes[-1]} {entity})"
        return Proof(statement, tv, premise.evidence | rule.evidence,
                     premise.visited | targets, premise.hops + rule.hops,
                     f"(Derived ModusPonens {premise.atom} {rule.atom})")

    def _publish(self, beliefs):
        self.proofs = beliefs
        self.canonical_beliefs = {stmt: {"stv": p.stv, "evidence": set(p.evidence), "fact_str": p.atom}
                                 for stmt, p in beliefs.items()}
        for p in beliefs.values():
            self.metta.space().add_atom(self.metta.parse_single(p.atom))

    def forward_chain(self, max_depth=4, verbose=False):
        self._prepare(max_depth)
        candidates = defaultdict(list)
        queue = deque(self._bases.values())
        seen = set()
        while queue:
            proof = queue.popleft()
            key = (proof.statement, proof.evidence, proof.visited, proof.hops, proof.stv)
            if key in seen:
                continue
            seen.add(key)
            if len(seen) > self.max_paths:
                raise RuntimeError("Fact proof budget exceeded; narrow the query or depth")
            candidates[proof.statement].append(proof)
            _, concept, entity = children(self.metta.parse_single(proof.statement), "Evaluation", 3)
            for rule in self._matching_rules(str(concept)):
                if proof.hops + rule.hops <= max_depth:
                    if (new := self._apply(proof, rule, str(entity))) is not None:
                        queue.append(new)
        beliefs = {stmt: p for stmt, values in sorted(candidates.items()) if (p := self._combine(values)) is not None}
        self._publish(beliefs)
        if verbose:
            for p in beliefs.values():
                print(f"{p.statement}: <{p.stv[0]:.6f}, {p.stv[1]:.6f}> [{p.hops} hops]")
        return beliefs

    def backward_chain(self, target_expr, max_depth=4, verbose=False):
        atoms = self.metta.parse_all(target_expr)
        if len(atoms) != 1:
            raise ValueError("Expected one target expression")
        _, concept, entity = children(atoms[0], "Evaluation", 3)
        symbol(str(concept)); symbol(str(entity))
        target_expr = str(atoms[0])
        self._prepare(max_depth)
        count = 0

        def solve(goal, remaining, active):
            nonlocal count
            if goal in active:
                return []
            active = active | {goal}
            answers = [self._bases[goal]] if goal in self._bases else []
            if remaining == 0:
                return answers
            _, b, who = children(self.metta.parse_single(goal), "Evaluation", 3)
            for rule in self._matching_rules(str(b), backward=True):
                if rule.hops > remaining:
                    continue
                intermediate = {f"(Evaluation {n} {who})" for n in rule.nodes[1:-1]}
                if intermediate & active:
                    continue
                subgoal = f"(Evaluation {rule.nodes[0]} {who})"
                for subproof in solve(subgoal, remaining - rule.hops, active | intermediate):
                    count += 1
                    if count > self.max_paths:
                        raise RuntimeError("Backward proof budget exceeded")
                    if (new := self._apply(subproof, rule, str(who))) is not None:
                        answers.append(new)
            return answers

        result = self._combine(solve(target_expr, max_depth, frozenset()))
        self._publish({target_expr: result} if result else {})
        if verbose:
            print(result.atom if result else f"No supported proof for {target_expr}")
        return result

    def abduce(self, effect, entity, max_depth=4):
        """Return alternative hypotheses, never automatically accept them as facts."""
        effect, entity = symbol(effect), symbol(entity)
        observation = self.backward_chain(f"(Evaluation {effect} {entity})", max_depth)
        if observation is None:
            return []
        priors = self._priors()
        hypotheses = []
        for rule in self._matching_rules(effect, backward=True):
            a = rule.nodes[0]
            if a not in priors or effect not in priors or not observation.evidence.isdisjoint(rule.evidence):
                continue
            pa, pb = priors[a], priors[effect]
            tv = self.calculate("abduction", observation.stv, rule.stv, pa.tv, pb.tv)
            support = observation.evidence | rule.evidence | {pa.evidence_id, pb.evidence_id}
            statement = f"(Evaluation {a} {entity})"
            prov = f"(Hypothesis Abduction {observation.atom} {rule.atom} {self._prior_atom(pa)} {self._prior_atom(pb)})"
            hypotheses.append(Proof(statement, tv, frozenset(support), frozenset({statement}), 1, prov))
        grouped = defaultdict(list)
        for proof in hypotheses:
            grouped[proof.statement].append(proof)
        results = [p for values in grouped.values() if (p := self._combine(values)) is not None]
        return sorted(results, key=self._rank)


if __name__ == "__main__":
    engine = PLNSearchEngine()
    engine.forward_chain(verbose=True)
    engine.backward_chain("(Evaluation AcademicIntervention Hana)", verbose=True)
