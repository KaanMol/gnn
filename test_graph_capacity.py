import unittest
from graph_runtime import execute_graph, validate_graph, MAX_GRAPH_NODES


def wide_graph(count):
    nodes=[{'id':f'n{i}','op':'data_literal','inputs':[],'type':'Data','value':i} for i in range(count-1)]
    nodes.append({'id':'result','op':'data_list','inputs':[n['id'] for n in nodes],'type':'Data'})
    return {'input_type':'Unit','output_type':'Data','nodes':nodes,'output':'result'}


class GraphCapacityTests(unittest.TestCase):
    def test_full_capacity_executes_every_node(self):
        graph=wide_graph(MAX_GRAPH_NODES)
        validate_graph(graph)
        result,_=execute_graph(graph)
        self.assertEqual(result,list(range(MAX_GRAPH_NODES-1)))

    def test_excess_capacity_and_runtime_budget_are_separate(self):
        with self.assertRaisesRegex(ValueError,'500 nodes'):
            validate_graph(wide_graph(MAX_GRAPH_NODES+1))
        with self.assertRaisesRegex(ValueError,'budget'):
            execute_graph(wide_graph(MAX_GRAPH_NODES),limit=100)
