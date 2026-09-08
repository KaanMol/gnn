"""Normal browser runtime behind fixed DOM sensory/control commands."""
import json,os,subprocess,tempfile,threading,atexit,select,math
from pathlib import Path

class RenderedWebSurface:
    actions={'open':['url'],'click':['id'],'type':['id','text'],'submit':['id'],'back':[],'forward':[],
             'scroll':['dy'],'click_at':['x','y'],'type_text':['text'],'press':['key']}
    def __init__(self,store):
        self.store=store;self.process=None;self.page=None;self.lock=threading.Lock()
        self.shot=Path(tempfile.mkdtemp(prefix='graph-browser-'))/'page.png';atexit.register(self.close)
    def close(self):
        if self.process and self.process.poll() is None:self.process.terminate()
    def start(self):
        if self.process and self.process.poll() is None:return
        root=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node'
        node=os.environ.get('GRAPH_BROWSER_NODE',str(root/'bin/node'))
        env={**os.environ,'GRAPH_PLAYWRIGHT':os.environ.get('GRAPH_PLAYWRIGHT',str(root/'node_modules/playwright')),'GRAPH_BROWSER_SHOT':str(self.shot)}
        if not env.get('GRAPH_BROWSER_EXECUTABLE'):
            candidates=sorted((Path.home()/'Library/Caches/ms-playwright').glob('chromium_headless_shell-*/chrome-headless-shell-mac-arm64/chrome-headless-shell'))
            if candidates:env['GRAPH_BROWSER_EXECUTABLE']=str(candidates[-1])
        self.process=subprocess.Popen([node,str(Path(__file__).with_name('browser_engine.cjs'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,env=env)
    def observation(self):
        return self.page or {'url':'','title':'No page opened','nodes':[],'retrieved_at':None,'truncated':False,'mode':'rendered-dom'}
    def request(self,action,args):
        with self.lock:
            self.start();self.process.stdin.write(json.dumps({'action':action,'args':args})+'\n');self.process.stdin.flush()
            if not select.select([self.process.stdout],[],[],45)[0]:
                self.close();raise ValueError('Browser took too long. Retry opening the page.')
            line=self.process.stdout.readline()
            if not line:raise ValueError('Browser engine stopped. Retry opening the page.')
            result=json.loads(line)
            if not result['ok']:raise ValueError('Browser: '+result['error'])
            self.page=result['result'];return self.page
    def observe(self):
        if not self.page:return self.observation()
        return self.request('observe',{})
    def act(self,action,args):
        if action not in self.actions or set(args)!=set(self.actions[action]):raise ValueError('Use a declared browser action.')
        if any(k in args and (not isinstance(args[k],str) or len(args[k])>2000) for k in ('url','text','key')):raise ValueError('Browser input must be bounded text.')
        if action=='click_at' and not all(type(args[k]) in (int,float) and 0<=args[k]<=limit for k,limit in [('x',1100),('y',750)]):raise ValueError('Choose a point inside the browser viewport.')
        if action=='scroll' and (type(args['dy']) not in (int,float) or not math.isfinite(args['dy'])):raise ValueError('Scroll needs a finite distance.')
        return self.request(action,args)
