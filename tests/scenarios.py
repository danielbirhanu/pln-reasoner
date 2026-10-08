"""Assignment demonstrations with assertions and reproducible JSON results."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from search.engine import PLNSearchEngine, ROOT


def run_scenarios():
    output = []
    engine = PLNSearchEngine()
    forward = engine.forward_chain(4)
    risk = '(Evaluation AcademicRisk Hana)'
    support = '(Evaluation AcademicIntervention Hana)'
    assert risk in forward and support in forward
    output.append({'scenario': 'A - Supported conclusion', 'question': 'Does Hana need academic support?',
                   'result': forward[support].as_dict(), 'risk': forward[risk].as_dict(),
                   'explanation': 'Assignment and prerequisite evidence support risk; overlapping intervention paths are not independently revised.'})

    missing = engine.backward_chain('(Evaluation AcademicRisk Dawit)',4)
    assert missing is None
    output.append({'scenario': 'B - Incomplete evidence', 'question': 'Can AcademicRisk(Dawit) be established?',
                   'result': None, 'explanation': 'LowParticipation has no matching risk rule. Missing evidence does not imply that risk is false.'})

    uncertain = PLNSearchEngine()
    uncertain.add_observation('LowAssignmentCompletion','UncertainStudent',.6,.2,'uncertain-assignment')
    weak = uncertain.backward_chain('(Evaluation AcademicRisk UncertainStudent)',4)
    assert weak and 0 < weak.stv[1] < .2
    output.append({'scenario': 'C - Uncertain evidence', 'question': 'How strongly does an uncertain assignment observation support risk?',
                   'result': weak.as_dict(), 'explanation': 'Confidence is reduced by the uncertain observation and implication strength/confidence.'})

    hypotheses = engine.abduce('LowQuizPerformance','Sara',4)
    assert len(hypotheses) >= 3
    output.append({'scenario': 'D - Competing explanations', 'question': 'What could explain Sara\'s low quiz performance?',
                   'hypotheses': [p.as_dict() for p in hypotheses],
                   'explanation': 'Bayesian inversion yields alternative explanations. They are candidates, not confirmed diagnoses, and their strengths need not sum to one.'})

    updated = PLNSearchEngine()
    before = updated.forward_chain(4)
    updated.add_observation('LowAssignmentCompletion','Hana',.3,.8,'teacher-assignment-new')
    after = updated.forward_chain(4)
    assert after[risk].stv != before[risk].stv
    assert after[support].stv != before[support].stv
    assert 'teacher-assignment-new' in after[risk].evidence
    rerun = updated.forward_chain(4)
    assert {k:p.as_dict() for k,p in after.items()} == {k:p.as_dict() for k,p in rerun.items()}
    output.append({'scenario': 'E - New conflicting evidence', 'question': 'Does a teacher observation change Hana\'s existing risk belief?',
                   'before': before[risk].as_dict(), 'after': after[risk].as_dict(),
                   'source_after': after['(Evaluation LowAssignmentCompletion Hana)'].as_dict(),
                   'intervention_before': before[support].as_dict(), 'intervention_after': after[support].as_dict(),
                   'explanation': 'Independent observations are consolidated, then all affected proofs are rebuilt. A repeat run changes nothing.'})

    chain = PLNSearchEngine(load_domain=False)
    wanted = ['WeakPrerequisiteTest','WeakPrerequisiteKnowledge','ConceptualDifficulty','AcademicRisk','AcademicIntervention']
    for a,b in zip(wanted,wanted[1:]):
        record = next(r for r in engine.records.values() if r.kind=='Rule' and r.args==(a,b))
        chain.add_rule(a,b,*record.tv,record.evidence_id)
    chain.add_observation(wanted[0],'Hana',.9,.9,'quiz-001')
    chained = chain.forward_chain(4)
    hops = [chained[f'(Evaluation {concept} Hana)'].as_dict() for concept in wanted]
    assert [p['hops'] for p in hops] == list(range(5))
    assert all(a['confidence'] > b['confidence'] for a,b in zip(hops,hops[1:]))
    output.append({'scenario': 'F - Four-hop uncertainty propagation', 'question': 'How does confidence change along the prerequisite-to-intervention path?',
                   'hops': hops, 'explanation': 'The authored four-link domain subset demonstrates a true four-hop proof with decreasing confidence at each hop.'})

    induction = PLNSearchEngine()
    induction.load_knowledge(ROOT/'knowledge/cohort.metta')
    learned = induction.forward_chain(4)
    target = '(Evaluation WeakPrerequisiteKnowledge Sara)'
    inferred = learned[target]
    backward_induced = induction.backward_chain(target,4)
    assert inferred.stv == backward_induced.stv and 'Induction' in inferred.provenance
    rule = next(r for r in induction.learned_rules if r.operation=='Induction' and r.nodes==('LowQuizPerformance','WeakPrerequisiteKnowledge'))
    output.append({'scenario': 'G - Knowledge-base induction', 'question': 'Can cohort co-occurrence generate and apply a new educational relationship?',
                   'induced_rule': {'from': rule.nodes[0], 'to': rule.nodes[-1], 'strength': rule.stv[0],
                                    'confidence': rule.stv[1], 'support': sorted(rule.evidence), 'proof': rule.atom},
                   'result': inferred.as_dict(),
                   'explanation': 'Cohort conditional estimates generate LowQuizPerformance -> WeakPrerequisiteKnowledge. Both search directions use it for Sara, carrying cohort and prior support.'})

    comparisons = []
    for statement in (risk,support,'(Evaluation LowQuizPerformance Hana)'):
        backward = engine.backward_chain(statement,4)
        assert all(abs(a-b)<1e-12 for a,b in zip(forward[statement].stv,backward.stv))
        assert forward[statement].evidence == backward.evidence
        comparisons.append({'statement':statement,'forward':list(forward[statement].stv),'backward':list(backward.stv),
                            'support':sorted(backward.evidence)})
    output.append({'scenario':'H - Forward/backward agreement','comparisons':comparisons,
                   'explanation':'Both directions enumerate bounded acyclic proofs and apply the same deterministic disjoint-evidence selection policy.'})
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,help='Optional path for complete machine-readable results')
    args=parser.parse_args()
    results=run_scenarios()
    for item in results:
        print('\n'+item['scenario'])
        if 'question' in item:
            print(item['question'])
        for label in ('result','before','after','source_after'):
            if label in item:
                result=item[label]
                print(f"  {label}: " + (f"<{result['strength']:.6f}, {result['confidence']:.6f}>" if result else 'NO SUPPORTED PROOF'))
        for hypothesis in item.get('hypotheses',[]):
            print(f"  {hypothesis['statement']}: <{hypothesis['strength']:.6f}, {hypothesis['confidence']:.6f}>")
        for hop in item.get('hops',[]):
            print(f"  hop {hop['hops']}: {hop['statement']} <{hop['strength']:.6f}, {hop['confidence']:.6f}>")
        if 'induced_rule' in item:
            r=item['induced_rule'];print(f"  induced {r['from']} -> {r['to']}: <{r['strength']:.6f}, {r['confidence']:.6f}>")
        for comparison in item.get('comparisons',[]):
            print(f"  MATCH: {comparison['statement']} {comparison['forward']}")
        print(item['explanation'])
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(results,indent=2)+'\n')
    print('\nPASS: all eight scenario assertions completed.')


if __name__=='__main__':
    main()
