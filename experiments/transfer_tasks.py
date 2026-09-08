"""Independent environment oracles and frozen tasks; never used to select programs."""
import copy,random,json
VOCABULARIES={
 'text':['text_lower','text_split','text_join','text_reverse','text_clean','text_dash'],
 'tree':['tree_left','tree_right','tree_up','tree_swap','tree_mark'],
 'planning':['plan_east','plan_west','plan_pick','plan_drop','plan_charge']}
TARGETS={
 'text':{'lower':['text_lower'],'normalize':['text_split','text_clean','text_join'],'reverse_words':['text_split','text_reverse','text_join'],'lower_normalize':['text_lower','text_split','text_clean','text_join'],'dash_normalize':['text_dash','text_split','text_clean','text_join'],'remove_digits':None},
 'tree':{'swap':['tree_swap'],'mark':['tree_mark'],'left_swap':['tree_left','tree_swap','tree_up'],'right_mark':['tree_right','tree_mark','tree_up'],'deep_mark':['tree_left','tree_left','tree_mark','tree_up','tree_up'],'mirror_all':None},
 'planning':{'charge':['plan_charge'],'round_trip':['plan_east','plan_west'],'pickup':['plan_east','plan_pick'],'deliver':['plan_east','plan_pick','plan_west','plan_drop'],'reach_goal':None,'unlock':None}}

def execute(ops,value):
 value=copy.deepcopy(value)
 for op in ops:
  if op=='text_lower':value=value.lower()
  elif op=='text_split':value=value.split(' ')
  elif op=='text_join':value=' '.join(value)
  elif op=='text_reverse':value=list(reversed(value))
  elif op=='text_clean':value=[x for x in value if x!='']
  elif op=='text_dash':value=value.replace('-',' ')
  elif op in ['tree_left','tree_right']:
   index=0 if op=='tree_left' else 1
   if len(value['focus']['children'])!=2:raise ValueError('Leaf')
   parent=value['focus'];value['crumbs'].append({'parent':copy.deepcopy(parent),'index':index});value['focus']=copy.deepcopy(parent['children'][index])
  elif op=='tree_up':
   crumb=value['crumbs'].pop();parent=crumb['parent'];parent['children'][crumb['index']]=value['focus'];value['focus']=parent
  elif op=='tree_swap':value['focus']['children'].reverse()
  elif op=='tree_mark':value['focus']['label']='*'
  elif op in ['plan_east','plan_west']:
   delta=1 if op=='plan_east' else -1
   if value['energy']<=0 or not 0<=value['x']+delta<=3:raise ValueError('Illegal move')
   value['x']+=delta;value['energy']-=1;value['log'].append(op)
  elif op=='plan_pick':
   if value['x']!=1 or value['carrying']:raise ValueError('Illegal pickup')
   value['carrying']=True;value['log'].append(op)
  elif op=='plan_drop':
   if value['x']!=0 or not value['carrying']:raise ValueError('Illegal drop')
   value['carrying']=False;value['log'].append(op)
  elif op=='plan_charge':value['energy']+=2;value['log'].append(op)
  else:raise ValueError(op)
 return value

def target(domain,family,value):
 ops=TARGETS[domain][family]
 if ops is not None:return execute(ops,value)
 if family=='remove_digits':return ''.join(x for x in value if not x.isdigit())
 if family=='mirror_all':
  def mirror(node):return {'label':node['label'],'children':[mirror(c) for c in reversed(node['children'])]}
  return {'focus':mirror(value['focus']),'crumbs':[]}
 if family=='reach_goal':return execute(['plan_east']*(3-value['x']),value)
 if family=='unlock':return {**value,'gate':True}
 raise ValueError(family)

def stream(domain,seed):
 rng=random.Random(seed);seen=set();tasks=[];families=list(TARGETS[domain])
 order=[]
 for _ in range(5):
  block=families.copy();rng.shuffle(block);order+=block
 serial=0
 def sample(family):
  nonlocal serial
  serial+=1
  if domain=='text':
   words=[rng.choice(['Alpha','bETA','Gamma','dELta','Echo'])+str(rng.randrange(1000)) for _ in range(rng.randint(2,5))]
   return ' '*rng.randrange(3)+rng.choice([' ','  ',' - ']).join(words)+' '*rng.randrange(3)
  if domain=='tree':
   def tree(depth,path='r'):
    return {'label':f'{serial}:{path}:{rng.randrange(10000)}','children':[] if depth==0 else [tree(depth-1,path+'L'),tree(depth-1,path+'R')]}
   return {'focus':tree(rng.choice([2,3])),'crumbs':[]}
  return {'id':serial,'x':serial%3 if family=='reach_goal' else 0,'energy':rng.randint(4,12),'carrying':False,'gate':False,'log':[]}
 for index,family in enumerate(order):
  examples=[]
  while len(examples)<26:
   value=sample(family);key=json.dumps(value,sort_keys=True)
   if key in seen:continue
   seen.add(key);examples.append({'input':value,'expected':target(domain,family,value)})
  tasks.append({'id':index,'domain':domain,'family':family,'witness':TARGETS[domain][family],'expected_boundary':('missing_primitive' if family in ['unlock','remove_digits'] else 'variable_structure' if family in ['reach_goal','mirror_all'] else None),'request':{'examples':examples[:4],'predicate':'unused','projector':'unused'},'validation':examples[4:10],'audit':examples[10:]})
 return tasks
