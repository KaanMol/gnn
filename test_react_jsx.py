"""Execute unchanged React Learn component source through graph procedures."""
from pathlib import Path
import unittest
import foundation
from build_programming_curriculum import build
from javascript import compile_source, display_value
from react_learn_corpus import blocks

ROOT=Path(__file__).parent

class ReactJSXTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.library=foundation.curriculum() | build()

    def execute(self, source):
        program=compile_source(source)
        value,evidence=foundation.run(self.library,'js_execute',{'program':program,'argument':None})
        return display_value(value['value'])

    def test_official_first_component_unchanged(self):
        source=next(b['code'] for b in blocks((ROOT/'react-learn-corpus/sources/your-first-component.md').read_text())
                    if b['code'].startswith('export default function Profile()'))
        self.assertEqual(self.execute(source),{'type':'img','props':{
            'src':'https://react.dev/images/docs/scientists/MK3eW3Am.jpg',
            'alt':'Katherine Johnson'},'children':[]})

    def test_official_quick_start_button_unchanged(self):
        source=next(b['code'] for b in blocks((ROOT/'react-learn-corpus/sources/index.md').read_text())
                    if b['code'].startswith('function MyButton()'))
        self.assertEqual(self.execute(source),{'type':'button','props':{},'children':["I'm a button"]})

    def test_expressions_lists_fragments_and_whitespace(self):
        tree=self.execute('''export default function List() {
          const title = "Tasks";
          return <><h1 className="title">{title}</h1><ul>{[1,2].map(n => <li key={n}>{n * 2}</li>)}</ul></>;
        }''')
        self.assertEqual(tree['children'][0],{'type':'h1','props':{'className':'title'},'children':['Tasks']})
        self.assertEqual(tree['children'][1]['children'][0][1],{'type':'li','props':{'key':2},'children':[4]})
        self.assertEqual(self.execute('function X() { return <p>\n Hello &amp;\n world\n</p>; }')['children'],['Hello & world'])
        self.assertEqual(self.execute('function X() { return <input disabled aria-label="Name" />; }')['props'],{'disabled':True,'aria-label':'Name'})

    def test_unsupported_and_malformed(self):
        for source in ['function X() { return <Counter />; }','function X() { return <p></div>; }',
                       'function X() { return <p>; }','function X() { return <p title={}/>; }']:
            with self.subTest(source=source),self.assertRaises(ValueError):compile_source(source)
        self.assertEqual(self.execute('function X() { const a=1; const b=2; return a<b; }'),True)
        self.assertEqual(self.execute('function X() { return "<img />"; }'),'<img />')

if __name__=='__main__':unittest.main()
