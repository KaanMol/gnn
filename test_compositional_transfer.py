import tempfile,unittest
from pathlib import Path
from graph_runtime import execute_graph,ExecutionCache
from experiments.adaptive_reuse import graph
from experiments.compositional_transfer import prepare
from experiments.transfer_tasks import VOCABULARIES,execute

class CompositionalTransferTests(unittest.TestCase):
 def test_callable_composition_and_expanded_guard_across_environments(self):
  with tempfile.TemporaryDirectory() as tmp:
   store,lib,hub,_=prepare(Path(tmp)/'test.sqlite3','compositional')
   try:
    fixtures=[
     ('text',['text_split','text_clean','text_join'],['text_lower'],' A  B2 '),
     ('tree',['tree_left','tree_mark','tree_up'],['tree_swap'],{'focus':{'label':'root','children':[{'label':'L','children':[]},{'label':'R','children':[]}]},'crumbs':[]}),
     ('planning',['plan_east','plan_pick'],['plan_west','plan_drop'],{'id':0,'x':0,'energy':8,'carrying':False,'gate':False,'log':[]})]
    for domain,primitives,suffix,value in fixtures:
     name='fixture_'+domain
     retained,_=graph(lib,hub,'manager_retain',{'ops':primitives,'name':name,'base':VOCABULARIES[domain],'validation':[{'input':value,'expected':execute(primitives,value)}],'predicate':'unused','projector':'unused'})
     self.assertTrue(retained['retained'])
     catalog=store.map('knowledge.economics')['catalog']
     ops=[name]+suffix
     args={'ops':ops,'catalog':catalog,'max_depth':5,'examples':[{'input':value,'expected':execute(primitives+suffix,value)}],'predicate':'unused','projector':'unused'}
     answer,_=graph(lib,hub,'composition_evaluate',args)
     self.assertTrue(answer['evaluation']['accepted']);self.assertEqual(answer['expanded'],primitives+suffix)
     # The actual rank enumerator can generate the mixed callable program.
     p,_=graph(lib,hub,'composition_prepare',{'base':VOCABULARIES[domain],'compose':True})
     rank=0
     for op in ops:rank=rank*len(p['vocabulary'])+p['vocabulary'].index(op)
     state={**args,'vocabulary':p['vocabulary'],'rank':rank,'depth':len(ops),'evaluated':0}
     result,_=graph(lib,hub,'composition_search_step',state)
     self.assertEqual(result['found'],ops)
     rejected,_=graph(lib,hub,'composition_evaluate',{**args,'max_depth':len(primitives+suffix)-1})
     self.assertFalse(rejected['allowed']);self.assertFalse(rejected['evaluation']['accepted'])
     # A discovered composition can be retained and called in another composition.
     r,_=graph(lib,hub,'manager_retain',{'ops':ops,'name':name+'_next','base':VOCABULARIES[domain],'validation':args['examples'],'predicate':'unused','projector':'unused'})
     self.assertTrue(r['retained'])
     entry=store.map('knowledge.economics')['catalog'][-1]
     self.assertEqual(entry['ops'],primitives+suffix)
     c,_=graph(lib,hub,'manager_canonicalize',{'ops':[entry['name']]+suffix,'catalog':store.map('knowledge.economics')['catalog']})
     self.assertEqual(c['ops'],primitives+suffix+suffix)
   finally:store.close()
 def test_nested_cached_work_is_charged(self):
  with tempfile.TemporaryDirectory() as tmp:
   store,lib,hub,_=prepare(Path(tmp)/'test.sqlite3','compositional')
   try:
    graph(lib,hub,'bench_promote',{'name':'fixture_macro','ops':['text_split','text_clean','text_join'],'vocabulary':[]})
    args={'ops':['fixture_macro','text_lower'],'argument':{'items':' A  B2 ','predicate':'unused','projector':'unused'}}
    cache=ExecutionCache();counts=[]
    for _ in range(2):
     meter={};value,_=execute_graph(lib['synth_execute_candidate']['graph'],args,lib,limit=1000000,sensors=hub,execution_cache=cache,meter=meter)
     self.assertEqual(value,'a b2');counts.append(meter['logical_steps'])
    self.assertEqual(counts[0],counts[1]);self.assertGreater(counts[0],4)
    with self.assertRaises(ValueError):execute_graph(lib['synth_execute_candidate']['graph'],args,lib,limit=counts[0]-1,sensors=hub,execution_cache=cache,meter={})
   finally:store.close()

if __name__=='__main__':unittest.main()
