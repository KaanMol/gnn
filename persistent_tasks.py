"""Transport for task plans; graph lessons own task state and execution."""
from uuid import uuid4
import foundation
from sequences import catalog, schema, decode
from skill_system import preflight
from graph_store import GraphSnapshot


def create(session, request, translator, steps=None):
    if not isinstance(request,str) or not request.strip() or len(request)>2000:
        raise ValueError('Describe the task in up to 2,000 characters.')
    library=session.core.procedures
    bindings={'speaker':session.speaker,'assistant':session.assistant_name}
    question=''
    if steps is None:
        if session.store.map('session.language').get('mode','hybrid')=='symbolic':
            steps=foundation.run(library,'sequence_interpret',request)[0]
            if steps is None:steps=[];question='This request needs a taught plan. Supply steps in Tasks or enable Gemma fallback.'
        else:
            rows=catalog(session);methods=[r['name'] for r in rows]
            policy=foundation.run(library,'task_plan_policy',None)[0]
            context={'speaker':session.speaker,'addressee':session.assistant_name,'procedures':{r['name']:{'input':r['graph'].get('sequence_input',r['graph']['input_type']),'meaning':r['graph'].get('description','')[:220]} for r in rows}}
            proposal=translator.translate_sequence(request,context,policy,schema(methods))
            steps=decode(proposal);question=proposal['clarification'].strip()
            if question:steps=[]
    if not isinstance(steps,list) or len(steps)>8:
        raise ValueError('Use a list of at most eight steps.')
    if steps:
        if any(not isinstance(step,dict) or set(step)!={'id','method','argument'} or not isinstance(step['id'],str) or not isinstance(step['method'],str) for step in steps):
            raise ValueError('Each step needs a text id, a text method and an argument.')
        snapshot=GraphSnapshot(library)
        try:
            foundation.run(snapshot,'sequence_prepare',{'steps':steps,'bindings':bindings,'methods':list(snapshot)})
            for step in steps:preflight(step['method'],snapshot)
        except (ValueError,KeyError) as error:
            question=str(error);steps=[]
    return session.run_skill('task_create',{'id':str(uuid4()),'title':request.strip()[:90],'original':request,'steps':steps,'question':question or ('No executable steps supplied.' if not steps else ''),'bindings':bindings},'Task: '+request)[0]
