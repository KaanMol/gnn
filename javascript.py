"""Transport and presentation for graph-owned JavaScript source processing.

Tokenization, grammar recognition, JSX construction and lowering are stored
procedures. No Python source parser or compiler is available in this module.
"""
import json
import re
from pathlib import Path

LIMIT = 9007199254740991
UNDEFINED = {'__js_type':'undefined'}


def source_curriculum():
    root=Path(__file__).parent/'curriculum'
    return (json.loads((root/'source-reader.json').read_text())
            | json.loads((root/'source-compiler.json').read_text())
            | json.loads((root/'source-learning.json').read_text())
            | json.loads((root/'programming-workbench.json').read_text()))


def compile_source(source):
    """Offline tools also compile exclusively through executable graph data."""
    import foundation
    from build_programming_curriculum import build
    return foundation.run(foundation.curriculum() | build() | source_curriculum(),
                          'javascript_compile_source',source)[0]


def run_source(session, source, supplied=None, has_input=False, original=None):
    _,run=session.run_skill('javascript_run_source',{
        'source':source,'argument':argument(supplied),'has_input':has_input}, original or source)
    payload=run['result']
    return {**run,'result':payload['execution'],'compiled_program':payload['compiled_program']}


def argument(value, depth=0):
    if depth>8:raise ValueError('Input data exceeds eight nested levels.')
    if type(value) in {bool,type(None)}: return value
    if type(value) is int and abs(value)<=LIMIT: return value
    if type(value) is str and len(value)<=1000:return value
    if isinstance(value,list) and len(value)<=64:return [argument(x,depth+1) for x in value]
    if isinstance(value,dict) and len(value)<=64 and all(type(k) is str and len(k)<=1000 for k in value):
        return {'__js_type':'object','properties':{k:argument(v,depth+1) for k,v in value.items()}}
    raise ValueError('Use safe integers, Booleans, null, short strings, or bounded arrays/objects of these values.')


def display_value(value):
    """Presentation only: unwrap graph object records; preserve undefined tags."""
    if isinstance(value,list):return [display_value(x) for x in value]
    if isinstance(value,dict) and value.get('__js_type')=='object':
        return {k:display_value(v) for k,v in value['properties'].items()}
    return value


def handle(session, text):
    raw=text.strip()
    official=re.fullmatch(r'read react example\s*:\s*([a-z0-9_/#-]+)',raw,re.I)
    if official:
        _,run=session.run_skill('react_learn_example',official[1],text);example=run['result']
        return 'Official React Learn source (reference, not executed):\n'+''.join(example['code_chunks'])+'\n\nParser audit: '+json.dumps(example['audit'])+'\nSource: '+example['source_url']
    if raw.rstrip('.!?').casefold()=='react learn coverage':
        _,run=session.run_skill('react_learn_coverage',None,text)
        return json.dumps(run['result'],indent=2)
    exercise=re.fullmatch(r'run react state queue\s*:\s*(\{.*\})',raw,re.I|re.S)
    if exercise:
        _,run=session.run_skill('react_state_queue',json.loads(exercise[1]),text)
        return 'React state-queue exercise: '+json.dumps(run['result'],indent=2)
    effect=re.fullmatch(r'run react effect\s*:\s*(\{.*\})',raw,re.I|re.S)
    if effect:
        _,run=session.run_skill('react_effect_lifecycle',json.loads(effect[1]),text)
        return 'React effect lifecycle exercise: '+json.dumps(run['result'],indent=2)
    topic={'teach me react':'overview','teach me html':'html_structure','teach me jsx':'jsx'}.get(raw.rstrip('.!?').casefold())
    explain=re.fullmatch(r'explain react\s*:\s*([a-z_]+)',raw,re.I)
    if explain:topic=explain[1].lower()
    if topic:
        _,run=session.run_skill('react_explain',topic,text);lesson=run['result']
        return lesson['title']+'\n\n'+lesson['explanation']+'\n\n'+lesson['example']+'\n\nSource: '+lesson['source']
    fence=re.fullmatch(r'```(?:javascript|js|jsx)?\s*\n([\s\S]*?)\n?```',raw,re.I)
    if fence:raw=fence[1].strip()
    if re.match(r'^(?:export\s+default\s+function\b|function\b|(?:let|const|for|while|if|do)\b|console\s*\.)',raw):
        text='Run JavaScript: '+json.dumps({'source':raw})
    match=re.fullmatch(r'\s*(run|explain|write|fix) javascript\s*:\s*(\{.*\})\s*',text,re.I|re.S)
    if not match:return None
    mode=match[1].lower();request=json.loads(match[2])
    if mode=='explain':
        _,run=session.run_skill('javascript_analyze_source',request['source'],text)
        return json.dumps(run['result'],indent=2,ensure_ascii=False)
    if mode=='write' and 'pipeline' in request:
        supplied={**request,'tests':[{'input':argument(t['input']),'expected':argument(t['expected'])} for t in request.get('tests',[])]}
        _,run=session.run_skill('javascript_write_pipeline',supplied,text)
        result=run['result']
        return result['verification']+' Tests passed: '+str(result['tests_passed'])+'\n```javascript\n'+result['source']+'\n```'
    if mode=='run':
        run=run_source(session,request['source'],request.get('input'),'input' in request,text)
        logs=run['result'].get('logs',[])
        logtext='\nConsole output (captured argument values):\n'+'\n'.join(json.dumps(display_value(line),ensure_ascii=False) for line in logs) if logs else ''
        resulttext='undefined' if run['result']['value']==UNDEFINED else json.dumps(display_value(run['result']['value']))
        return 'JavaScript subset result: '+resulttext+logtext+'\nExecuted steps:\n'+ '\n'.join(
            f"{r['step']}: {r['operation']} → {json.dumps(r['variables'])}" for r in run['result']['steps'])
    entries=session.store.map('knowledge.javascript_examples')
    if mode=='write':
        task=request['task']
        if task not in entries:raise ValueError('Known starter tasks: '+', '.join(entries))
        candidates=list(entries[task]['candidates'])
        tests=request.get('tests',entries[task]['tests'])
    else:
        source=request['source'];session.run_skill('javascript_compile_source',source,text)
        policy=session.store.map('knowledge.javascript_examples').get('repair_policy')
        if policy is None:raise ValueError('Missing taught JavaScript repair policy.')
        candidates=[source]
        for old,new in policy['replacements']:
            if old in source:candidates.append(source.replace(old,new,1))
        tests=request['tests']
    if not isinstance(tests,list) or not 1<=len(tests)<=12:raise ValueError('Supply 1–12 input/output examples.')
    prepared=[]
    for candidate in candidates:
        _,compiled=session.run_skill('javascript_compile_source',candidate,text)
        prepared.append({'source':candidate,'program':compiled['result']})
    cases=[{'input':argument(t['input']),'expected':argument(t['expected'])} for t in tests]
    failures=[]
    for candidate in prepared:
        # The host contains failed executions; graph lessons decide whether
        # completed executions satisfy the supplied examples.
        try:
            _,run=session.run_skill('js_choose_program',{'candidates':[candidate],'tests':cases},text)
        except ValueError as error:
            failures.append(str(error));continue
        matches=run['result']
        if matches:
            return 'Candidate passed all '+str(len(cases))+' examples (not a proof for all inputs):\n```javascript\n'+matches[0]['source']+'\n```'
    return 'No taught candidate passed every supplied example.'+(' Execution failures: '+'; '.join(failures[:2]) if failures else '')
