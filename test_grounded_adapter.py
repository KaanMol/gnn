import tempfile,unittest
from pathlib import Path
from experiments.grounded_adapter import run
from graph_store import GraphStore
import foundation

class GroundedAdapterTests(unittest.TestCase):
 def test_feedback_ambiguity_rename_and_persistence(self):
  with tempfile.TemporaryDirectory() as directory:
   database=Path(directory)/'db.sqlite3'
   result=run(database,Path(directory)/'results')
   self.assertEqual([s['held_out_passed'] for s in result['scenarios']],[40,40])
   self.assertFalse(result['unseen_rename_prediction']['known'])
   store=GraphStore(database)
   try:
    library=store.map('knowledge.procedures')
    self.assertFalse(foundation.run(library,'learned_world_one',{'q7':False})[0])
    self.assertNotIn('should_not_be_saved',library)
   finally:store.close()

if __name__=='__main__':unittest.main()
