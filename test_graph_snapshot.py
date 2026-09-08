import unittest
from graph_store import GraphStore, GraphSnapshot
from graph_dsl import G
import foundation

class GraphSnapshotTests(unittest.TestCase):
    def test_frozen_roots_and_result_isolation(self):
        store=GraphStore(); library=store.map('knowledge.procedures')
        g=G(); library['example']={'graph':g.finish(g.data({'answer':[1]}))}
        snapshot=GraphSnapshot(library)
        g=G(); library['example']={'graph':g.finish(g.data({'answer':[2]}))}
        self.assertEqual(foundation.run(snapshot,'example',None)[0],{'answer':[1]})
        result=foundation.run(library,'example',None)[0];result['answer'].append(3)
        self.assertEqual(foundation.run(library,'example',None)[0],{'answer':[2]})
        del library['example']
        with self.assertRaises(ValueError):foundation.run(library,'example',None)
        self.assertEqual(foundation.run(snapshot,'example',None)[0],{'answer':[1]})

    def test_interface_index_tracks_new_snapshot(self):
        store=GraphStore();library=store.map('knowledge.procedures')
        g=G();library['one']={'graph':g.finish(g.input,interface='sample')}
        snapshot=GraphSnapshot(library)
        del library['one'];library['two']={'graph':g.finish(g.input,interface='sample')}
        self.assertEqual(snapshot.interface_names('sample'),['one'])
        self.assertEqual(GraphSnapshot(library).interface_names('sample'),['two'])
