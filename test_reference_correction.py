import unittest
import foundation
from knowledge import Knowledge
from build_reference_correction_curriculum import build
from build_meaning_curriculum import build as meanings

class ReferenceCorrectionTests(unittest.TestCase):
 def setUp(self):
  self.core=Knowledge();self.core.procedures.update(meanings());self.core.procedures.update(build(self.core.procedures))
 def tearDown(self):self.core.store.close()
 def prepare(self):
  self.core.assert_fact('Austria','world bank listed capital','Vienna',False,'Geography source')
  self.core.assert_fact('Julia','has sister','Vienna',False,'User family source')
 def test_separation_preserves_evidence_and_other_entities(self):
  self.prepare();before=dict(self.core.assertions)
  self.core.separate_person_city('Vienna','Explicit user correction')
  self.assertEqual(dict(self.core.assertions),before)
  self.assertIn(('has sister','Julia','Vienna (person)'),self.core.facts)
  self.assertIn(('world bank listed capital','Austria','Vienna (city)'),self.core.facts)
  self.assertIn('Which one',self.core.query('Julia','has sister','Vienna'))
  self.assertIn('Which one',self.core.describe('Vienna'))
  with self.assertRaisesRegex(ValueError,'Which one'):self.core.assert_fact('Vienna','like','Music',False,'ambiguous')
  self.assertEqual(dict(self.core.assertions),before)
  self.core.assert_fact('Vienna (person)','like','Music',False,'explicit person')
  self.assertIn(('like','Vienna (person)','Music'),self.core.facts)
 def test_unmatched_request_is_atomic(self):
  self.core.assert_fact('Julia','has sister','Paris',False,'User family source')
  before=self.core.procedures['meaning_policy']
  with self.assertRaisesRegex(ValueError,'identifiable family and city'):
   self.core.separate_person_city('Paris','correction')
  self.assertEqual(self.core.procedures['meaning_policy'],before)
 def test_legacy_subject_scope_and_negative_evidence(self):
  lib=self.core.procedures.to_dict();policy=foundation.run(lib,'meaning_policy',None)[0]
  policy['source_scopes']=[{'name':'Mercury','scope':'Mercury (planet)','source_contains':'astronomy'}]
  from graph_dsl import G
  g=G();lib['meaning_policy']={'graph':g.finish(g.data(policy))}
  rows=[{'fact':['is','Mercury','planet'],'negative':True,'source':'astronomy evidence'}]
  result=foundation.run(lib,'meaning_assertions',rows)[0]
  self.assertEqual(result,[{'fact':['is','Mercury (planet)','planet'],'negative':True,'source':'astronomy evidence'}])
 def test_clarify_never_claims_success(self):
  result=foundation.run(self.core.procedures,'dialogue_clarification_response','I have updated my memory.')[0]
  self.assertIn("haven't changed memory",result)
  self.assertNotIn('have updated',result)
  with_question=foundation.run(self.core.procedures,'dialogue_clarification_response','I have updated my memory. Anything else?')[0]
  self.assertEqual(with_question,result)

if __name__=='__main__':unittest.main()
