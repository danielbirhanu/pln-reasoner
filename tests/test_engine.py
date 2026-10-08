import math
from pathlib import Path
import tempfile
import unittest

from run_tests import run_metta_files
from search.engine import PLNSearchEngine, Proof, ROOT, validate_stv


class AlgebraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = PLNSearchEngine(load_domain=False)

    def test_source_revision(self):
        s, c = self.e.calculate("revision", (.8, .75), (.3, .8))
        self.assertAlmostEqual(s, 18/35)
        self.assertAlmostEqual(c, .875)

    def test_scientific_notation(self):
        self.assertEqual(self.e._extract_stv('(stv 1e-05 0.8)'), (1e-5, .8))

    def test_parser_never_fabricates_zero_belief(self):
        for text in ('(stv NaN 0.8)', '(stv -0.1 0.8)', '(stv 0.1 1.5)', 'broken', '(stv 0.1 0.2) extra'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.e._extract_stv(text)

    def test_non_finite_and_bounds(self):
        for tv in ((math.nan,.8),(.2,math.inf),(-.1,.8),(1.1,.8),(.1,1),(.1,-.1),(True,.1)):
            with self.subTest(tv=tv), self.assertRaises(ValueError):
                validate_stv(tv)

    def test_abduction_both_joint_bounds(self):
        for values in [((.8,.9),(.85,.9),(.5,.9),(.2,.9)),
                       ((.8,.9),(.1,.9),(.9,.9),(.9,.9))]:
            with self.assertRaisesRegex(ValueError, 'InconsistentProbabilities'):
                self.e.calculate('abduction', *values)

    def test_induction_rejects_inconsistent_priors(self):
        with self.assertRaises(ValueError):
            self.e.calculate('induction', (.9,.9),(.9,.9),(.5,.9),(.1,.9),(.1,.9))

    def test_undefined_conditionals_rejected(self):
        with self.assertRaises(ValueError):
            self.e.calculate('abduction', (.8,.9),(.8,.9),(0,.9),(0,.9))
        with self.assertRaises(ValueError):
            self.e.calculate('induction', (.8,.9),(.8,.9),(.5,.9),(0,.9),(.5,.9))

    def test_prior_confidence_affects_induction(self):
        high = self.e.calculate('induction', (.8,.9),(.85,.8),(.4,.9),(.5,.9),(.6,.9))
        low = self.e.calculate('induction', (.8,.9),(.85,.8),(.4,.2),(.5,.9),(.6,.9))
        self.assertEqual(high[0],low[0]); self.assertGreater(high[1],low[1])


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.e = PLNSearchEngine(load_domain=False)
        self.e.add_rule('Assignment', 'Risk', .7,.65,'rule-assignment-risk')
        self.e.add_rule('Risk', 'Support', .75,.65,'rule-risk-support')
        self.e.add_observation('Assignment','Learner',.8,.75,'obs-one')

    def test_rerun_is_idempotent(self):
        first = {k:p.as_dict() for k,p in self.e.forward_chain(3).items()}
        second = {k:p.as_dict() for k,p in self.e.forward_chain(3).items()}
        self.assertEqual(first,second)
        self.assertEqual(self.e.records['rule-assignment-risk'].tv,(.7,.65))

    def test_new_evidence_updates_source_and_downstream(self):
        before = self.e.forward_chain(3)
        self.e.add_observation('Assignment','Learner',.3,.8,'teacher-extra')
        after = self.e.forward_chain(3)
        source = after['(Evaluation Assignment Learner)']
        self.assertAlmostEqual(source.stv[0],18/35)
        self.assertAlmostEqual(source.stv[1],.875)
        for statement in ('(Evaluation Risk Learner)','(Evaluation Support Learner)'):
            self.assertNotEqual(before[statement].stv,after[statement].stv)
            self.assertIn('teacher-extra',after[statement].evidence)
        expected = self.e.calculate('modus-ponens',source.stv,(.7,.65))
        self.assertEqual(after['(Evaluation Risk Learner)'].stv, expected)

    def test_active_space_has_only_one_current_source_fact(self):
        self.e.forward_chain(3)
        self.e.add_observation('Assignment','Learner',.3,.8,'teacher-extra')
        self.e.forward_chain(3)
        values = self.e.metta.run('!(match &self (Fact (Evaluation Assignment Learner) $tv $prov) $tv)')[0]
        self.assertEqual(len(values),1)
        self.assertAlmostEqual(self.e._extract_stv(str(values[0]))[0],18/35)

    def test_correction_with_same_evidence_ids_recomputes(self):
        before = self.e.forward_chain(3)
        self.e.replace_observation('obs-one', .2,.8)
        after = self.e.forward_chain(3)
        key='(Evaluation Support Learner)'
        self.assertEqual(before[key].evidence,after[key].evidence)
        self.assertNotEqual(before[key].stv,after[key].stv)

    def test_retraction_removes_unsupported_descendants(self):
        self.e.forward_chain(3)
        self.e.remove_observation('obs-one')
        self.assertEqual(self.e.forward_chain(3),{})

    def test_duplicate_evidence_does_not_increase_confidence(self):
        self.e.add_observation('Assignment','Learner',.8,.75,'obs-one')
        self.assertEqual(self.e.forward_chain(0)['(Evaluation Assignment Learner)'].stv,(.8,.75))
        with self.assertRaises(ValueError):
            self.e.add_observation('Assignment','Learner',.3,.8,'obs-one')

    def test_zero_confidence_is_not_a_supported_conclusion(self):
        self.e.add_observation('Assignment','Nobody',.9,0,'zero')
        beliefs=self.e.forward_chain(3)
        self.assertFalse(any('Nobody' in statement for statement in beliefs))

    def test_known_fact_at_zero_depth(self):
        result=self.e.backward_chain('(Evaluation Assignment Learner)',0)
        self.assertEqual(result.stv,(.8,.75))
        self.assertIsNone(self.e.backward_chain('(Evaluation Risk Learner)',0))

    def test_cycle_terminates_and_does_not_amplify_observation(self):
        self.e.add_rule('Risk','Assignment',.8,.8,'rule-cycle')
        beliefs=self.e.forward_chain(8)
        self.assertEqual(beliefs['(Evaluation Assignment Learner)'].stv,(.8,.75))
        self.assertIsNotNone(self.e.backward_chain('(Evaluation Support Learner)',8))

    def test_partial_overlap_is_not_revised_as_independent(self):
        a=Proof('P',(.7,.8),frozenset({'one','two'}),frozenset({'P'}),1,'A')
        b=Proof('P',(.2,.7),frozenset({'two','three'}),frozenset({'P'}),1,'B')
        selected=self.e._combine([a,b])
        self.assertEqual(selected,a)
        self.assertEqual(self.e._combine([b,a]),a)

    def test_disjoint_proofs_are_revised(self):
        a=Proof('P',(.7,.8),frozenset({'one'}),frozenset({'P'}),1,'A')
        b=Proof('P',(.2,.7),frozenset({'two'}),frozenset({'P'}),1,'B')
        combined=self.e._combine([a,b])
        self.assertGreater(combined.stv[1],.8)
        self.assertEqual(combined.evidence,frozenset({'one','two'}))

    def test_input_symbols_are_not_executable_expressions(self):
        with self.assertRaises(ValueError):
            self.e.add_observation('A) !(clear)', 'Learner',.5,.5,'unsafe')


class DomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=PLNSearchEngine()
        cls.forward=cls.e.forward_chain(4)

    def test_supported_conclusion(self):
        self.assertIn('(Evaluation AcademicIntervention Hana)', self.forward)

    def test_forward_backward_agreement(self):
        for target in ('(Evaluation AcademicRisk Hana)', '(Evaluation AcademicIntervention Hana)',
                       '(Evaluation LowQuizPerformance Hana)'):
            with self.subTest(target=target):
                backward=self.e.backward_chain(target,4)
                for a,b in zip(self.forward[target].stv,backward.stv):
                    self.assertAlmostEqual(a,b,places=12)
                self.assertEqual(self.forward[target].evidence,backward.evidence)

    def test_incomplete_evidence(self):
        self.assertIsNone(self.e.backward_chain('(Evaluation AcademicRisk Dawit)',4))

    def test_competing_hypotheses_not_promoted_to_facts(self):
        hypotheses=self.e.abduce('LowQuizPerformance','Sara',4)
        self.assertGreaterEqual(len(hypotheses),3)
        self.assertEqual(len({h.statement for h in hypotheses}),len(hypotheses))
        self.assertTrue(all('Hypothesis Abduction' in h.provenance for h in hypotheses))
        self.assertNotIn('(Evaluation AcademicRisk Sara)',self.e.proofs)

    def test_rule_provenance_includes_population_priors(self):
        rule=next(r for r in self.e.learned_rules if r.nodes==('WeakPrerequisiteKnowledge','ConceptualDifficulty','AcademicRisk'))
        self.assertTrue({'prior-prerequisite','prior-difficulty','prior-risk'} <= rule.evidence)
        self.assertAlmostEqual(rule.stv[0],.71)

    def test_original_rules_remain_authoritative(self):
        self.e._prepare(4)
        active=self.e._matching_rules('WeakPrerequisiteKnowledge')
        to_quiz=[r for r in active if r.nodes[-1]=='LowQuizPerformance']
        self.assertEqual(len(to_quiz),1)
        self.assertEqual(to_quiz[0].stv,(.85,.8))


class InductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=PLNSearchEngine()
        cls.e.load_knowledge(ROOT/'knowledge/cohort.metta')
        cls.forward=cls.e.forward_chain(4)

    def test_kb_induction_is_stored_and_consumed(self):
        rule=next(r for r in self.e.learned_rules if r.operation=='Induction' and r.nodes==('LowQuizPerformance','WeakPrerequisiteKnowledge'))
        self.assertAlmostEqual(rule.stv[0],.2722222222222222)
        proof=self.forward['(Evaluation WeakPrerequisiteKnowledge Sara)']
        self.assertIn('Induction',proof.provenance)
        self.assertTrue({'cohort-prerequisite','cohort-quiz','prior-cohort','quiz-003'} <= proof.evidence)

    def test_backward_can_use_induced_rule(self):
        backward=self.e.backward_chain('(Evaluation WeakPrerequisiteKnowledge Sara)',4)
        self.assertEqual(backward.stv,self.forward[backward.statement].stv)
        self.assertIn('Induction',backward.provenance)

    def test_shared_cohort_support_prevents_double_counting(self):
        proof=self.forward['(Evaluation AcademicRisk Sara)']
        self.assertTrue({'cohort-prerequisite','cohort-quiz'} <= proof.evidence)
        self.assertNotIn('Revised',proof.provenance)


class RunnerTests(unittest.TestCase):
    def test_empty_discovery_fails(self):
        with self.assertRaises(ValueError):
            run_metta_files([])

    def test_intentionally_failing_assertion_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.metta';path.write_text('!(assertEqual 1 2)')
            with self.assertRaises(AssertionError):
                run_metta_files([path])

    def test_path_budget_is_enforced(self):
        e=PLNSearchEngine(load_domain=False,max_paths=1)
        e.add_observation('A','X',.9,.8,'first')
        e.add_observation('B','X',.9,.8,'second')
        with self.assertRaisesRegex(RuntimeError,'budget'):
            e.forward_chain(1)

    def test_domain_rejects_impossible_rule(self):
        e=PLNSearchEngine(load_domain=False)
        e.add_prior('A',.9,.9,'prior-a');e.add_prior('B',.9,.9,'prior-b')
        with self.assertRaises(ValueError):
            e.add_rule('A','B',.1,.9,'impossible')


if __name__=='__main__':
    unittest.main()
