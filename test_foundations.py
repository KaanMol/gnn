import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from interface import Session
from graph_dsl import G
from graph_runtime import execute_graph
import foundation


class NoModel:
    def translate(self, *args):
        raise AssertionError('These tests must execute without a language model')


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.s = Session()
        self.addCleanup(self.s.store.close)

    def test_inference_and_retraction_execute_taught_methods(self):
        s=self.s
        s.core.assert_fact('Iris','meets','Leon',False,'observed')
        s.core.symmetry('meets','teacher')
        self.assertTrue(s.core.query('Leon','meets','Iris').startswith('Yes'))
        saved=copy.deepcopy(s.core.procedures['horn_join'])
        s.forget_graph('horn_join')
        self.assertNotIn(('meets','Leon','Iris'),s.core.facts)
        self.assertIn(('meets','Iris','Leon'),s.core.facts)
        self.assertIn('horn_join',s.core.reasoning_error)
        s.core.procedures['horn_join']=saved
        self.assertIn(('meets','Leon','Iris'),s.core.facts)
        s.core.retract('Iris','meets','Leon',False)
        self.assertNotIn(('meets','Leon','Iris'),s.core.facts)

    def test_taught_calendar_vocabulary_and_clock_binding_can_be_forgotten(self):
        s=self.s
        with self.assertRaises(ValueError): s.core.invoke('calendar_parse','3 Frost 2002')
        graph=copy.deepcopy(s.core.procedures['calendar_vocabulary']['graph'])
        graph['nodes'][1]['value']['months']['frost']=12
        s.teach_graph('calendar_vocabulary',graph,replace=True)
        self.assertEqual(s.core.invoke('calendar_parse','3 Frost 2002'),[2002,12,3])
        age=json.loads((Path(__file__).parent/'examples/age_years.graph.json').read_text())
        s.teach_graph('age_years',age)
        s.forget_graph('clock_calendar')
        with patch('date_tools.call_tool') as clock:
            with self.assertRaisesRegex(ValueError,'binding'):
                execute_graph(age,[2000,2,24],s.core.procedures)
            clock.assert_not_called()

    def test_counting_and_correction_policies_are_lessons(self):
        s=self.s
        self.assertIn('4, 3, 2',s.chat('Count from 4 to 2',NoModel()))
        s.chat('Nia was born on 20 July 2001',NoModel())
        s.chat('Nia was born on 21 July 2001',NoModel())
        self.assertEqual([f[2] for f,n in s.core.assertions if f[0]=='birth date'],['2001-07-21'])
        policy=copy.deepcopy(s.core.procedures['memory_policy']['graph'])
        policy['nodes'][1]['value']['functional_relations']=[]
        s.teach_graph('memory_policy',policy,replace=True)
        s.chat('Nia was born on 20 July 2001',NoModel())
        self.assertEqual(len([f for f,n in s.core.assertions if f[0]=='birth date']),2)
        s.forget_graph('count_sequence')
        self.assertIn('count_sequence',s.chat('Count to 4',NoModel()))

    def test_foundations_do_not_resurrect_on_restart(self):
        s=self.s;s.forget_graph('world_choose_experiment');s.forget_graph('pattern_match')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'memory.json';s.save(path)
            with patch('foundation.curriculum',side_effect=AssertionError('Reloaded source lessons')):
                restored=Session.load(path)
                try:
                    self.assertNotIn('pattern_match',restored.core.procedures)
                    self.assertIsNone(restored.explorer.choose())
                finally: restored.store.close()

    def test_new_skill_family_planning_checks_revision_and_forgetting(self):
        s=self.s
        package=json.loads((Path(__file__).parent/'examples/temperature.skills.json').read_text())
        s.teach_graph_package(package,'test teacher')
        request={'have':['fahrenheit_reading'],'want':['temperature_assessed'],'input':{'fahrenheit':86},'check':'temperature_check'}
        run=s.skills.achieve(request)
        self.assertEqual(run['plan']['plan'],['temperature_convert','temperature_assess'])
        self.assertEqual(run['result'],{'celsius':30,'warm':True})
        self.assertEqual(run['status'],'verified')
        self.assertEqual(s.skills.achieve({**request,'input':{'fahrenheit':32}})['result'],{'celsius':0,'warm':False})
        # Alter the claimed skill while retaining an independent old checker.
        graph=copy.deepcopy(package['temperature_assess']['graph'])
        for node in graph['nodes']:
            if node['op']=='data_literal' and node.get('value')==25: node['value']=50
        s.teach_graph('temperature_assess',graph,replace=True)
        self.assertEqual(s.skills.achieve(request)['status'],'check_failed')
        s.forget_graph('temperature_convert')
        self.assertEqual(s.skills.achieve(request)['status'],'missing_knowledge')
        self.assertGreaterEqual(len(s.store.map('skills.goals')),4)

    def test_plan_contracts_do_not_claim_verified_success(self):
        s=self.s;g=G()
        s.teach_graph('claim_done',g.finish(g.input,skill={'requires':['start'],'provides':['done']}))
        result=s.skills.achieve({'have':['start'],'want':['done'],'input':{'unchanged':True}})
        self.assertEqual(result['status'],'executed_unverified')
        s.forget_graph('plan_search')
        with self.assertRaisesRegex(ValueError,'plan_search'):
            s.skills.achieve({'have':['start'],'want':['done'],'input':None})

    def test_memory_interface_read_revise_and_forget(self):
        s=self.s;g=G();s.teach_graph('new_skill',g.finish(g.data('first')))
        target={'namespace':'knowledge.procedures','key':'new_skill'}
        read=s.skills.run('workspace_read',target)['result']
        read['graph']['nodes'][1]['value']='revised'
        s.skills.run('workspace_write',{**target,'value':read})
        self.assertEqual(s.skills.run('new_skill',None)['result'],'revised')
        s.skills.run('workspace_forget',target)
        with self.assertRaisesRegex(ValueError,'new_skill'): s.skills.run('new_skill',None)
        s.forget_graph('workspace_read')
        with self.assertRaisesRegex(ValueError,'workspace_read'): s.skills.run('workspace_read',target)
        self.assertTrue(any(e.get('action')=='write' for e in s.sensors.events))

    def test_generic_runner_has_no_rich_sudoku_adapter(self):
        s=self.s;g=G();s.teach_graph('peek',g.finish(g.op('observe',g.input,surface='sudoku-canvas')))
        with self.assertRaisesRegex(ValueError,'Unknown perception'): s.skills.run('peek',None)
        self.assertEqual(s.sensors.events,[])

    def test_generic_runner_serializes_numeric_results_exactly(self):
        s=self.s;g=G('Number')
        result=g.op('divide',g.input,g.number(3),kind='Number')
        s.teach_graph('third',g.finish(result,'Number'))
        answer,run=s.run_skill('third',1)
        self.assertEqual(run['result'],'1/3')
        self.assertEqual(json.loads(json.dumps(run))['result'],'1/3')

    def test_goal_selects_taught_sudoku_and_checks_actual_board(self):
        s=self.s;s.teach_sudoku_suite()
        request={'have':['sudoku_canvas'],'want':['filled_sudoku_canvas'],'input':None,'check':'sudoku_goal_check'}
        run=s.skills.achieve(request)
        self.assertEqual(run['status'],'verified')
        self.assertEqual(run['plan']['plan'],['sudoku_observe_solve'])
        self.assertTrue(run['result']['correct'])
        s.forget_graph('sudoku_goal_check')
        before=len(s.sensors.events)
        with self.assertRaisesRegex(ValueError,'checker'): s.skills.achieve(request)
        self.assertEqual(before,len(s.sensors.events))

    def test_static_dependency_failure_precedes_any_action(self):
        s=self.s;g=G();s.teach_graph('removed',g.finish(g.input))
        g=G();effect=g.call('workspace_write',g.input);result=g.call('removed',effect)
        s.teach_graph('write_then_call',g.finish(result,skill={'requires':['before'],'provides':['after']}))
        s.forget_graph('removed')
        request={'have':['before'],'want':['after'],'input':{'namespace':'knowledge.notes','key':'probe','value':42}}
        with self.assertRaisesRegex(ValueError,'removed'): s.skills.achieve(request)
        self.assertNotIn('probe',s.store.map('knowledge.notes'))
        self.assertEqual(s.sensors.events,[])


if __name__=='__main__': unittest.main()
