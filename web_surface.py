"""Bounded, public HTML sensory port. No page interpretation or domain rules."""
from html.parser import HTMLParser
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urljoin, urlsplit, urlencode, parse_qsl, urlunsplit
from datetime import datetime, timezone
import socket
import ipaddress


def public_url(url):
    if not isinstance(url,str) or len(url)>2000:raise ValueError('Use a public HTTP(S) address.')
    p=urlsplit(url)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or p.port not in (None,80,443):
        raise ValueError('This reader accepts public HTTP(S) pages on standard ports.')
    try:addresses=socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)
    except OSError:raise ValueError('Could not resolve that website.') from None
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Local and private network addresses are outside this web reader.')
    return url


class Redirects(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return super().redirect_request(req,fp,code,msg,headers,public_url(newurl))


class Tree(HTMLParser):
    void={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    ignored={'script','style','noscript','template','svg'}
    def __init__(self,url):
        super().__init__(convert_charrefs=True);self.url=url;self.nodes=[];self.stack=[];self.skipping=[];self.truncated=False
    def add(self,tag,attrs=None,text=''):
        if len(self.nodes)>=1800:self.truncated=True;return None
        n={'id':len(self.nodes),'parent':self.stack[-1] if self.stack else -1,'ancestors':list(self.stack[-40:]),'tag':tag,'attrs':attrs or {},'text':' '.join(text.split())[:2000],'raw_text':text[:6000]}
        self.nodes.append(n);return n['id']
    def handle_starttag(self,tag,attrs):
        if self.skipping:
            if tag not in self.void:self.skipping.append(tag)
            return
        if tag in self.ignored:self.skipping=[tag];return
        a={k:(v or '')[:2000] for k,v in attrs[:30] if not k.startswith('on')}
        for k in ('href','action'):
            if k in a:a[k]=urljoin(self.url,a[k])
        identifier=self.add(tag,a)
        if identifier is not None and tag not in self.void:self.stack.append(identifier)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in self.void:self.handle_endtag(tag)
    def handle_endtag(self,tag):
        if self.skipping:
            if tag in self.skipping:
                self.skipping=self.skipping[:self.skipping.index(tag)]
            return
        for i in range(len(self.stack)-1,-1,-1):
            if self.nodes[self.stack[i]]['tag']==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):
        if self.skipping:return
        if data.strip():self.add('#text',text=data)


class WebSurface:
    actions={'open':['url'],'click':['id'],'type':['id','text'],'submit':['id'],'back':[],'forward':[]}
    def __init__(self,store):
        self.store=store;self.page=None;self.history=[];self.position=-1;self.fields={}
    def observe(self):
        return self.page or {'url':'','title':'No page opened','nodes':[],'retrieved_at':None,'truncated':False,'mode':'static-html'}
    def node(self,identifier):
        if type(identifier) is not int or self.page is None or not 0<=identifier<len(self.page['nodes']):raise ValueError('Choose a node on the current page.')
        return self.page['nodes'][identifier]
    def open(self,url,remember=True):
        public_url(url)
        try:
            with build_opener(Redirects()).open(Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; GraphLearningReader/1.0)','Accept':'text/html,application/xhtml+xml,text/plain'}),timeout=15) as response:
                kind=response.headers.get_content_type()
                if kind not in ('text/html','application/xhtml+xml','text/plain'):raise ValueError('This port reads HTML or plain-text pages, not downloads.')
                raw=response.read(1000001)
                if len(raw)>1000000:raise ValueError('That page exceeds the one-megabyte reading limit.')
                text=raw.decode(response.headers.get_content_charset() or 'utf-8',errors='replace');final=response.geturl()
        except OSError as e:raise ValueError('Could not read the website: '+str(e)) from None
        tree=Tree(final)
        if kind=='text/plain':tree.add('#text',text=text)
        else:tree.feed(text)
        titles=[n['id'] for n in tree.nodes if n['tag']=='title']
        title=' '.join(n['text'] for n in tree.nodes if any(t in n['ancestors'] for t in titles))[:200]
        self.page={'url':final,'title':title or final,'nodes':tree.nodes,'retrieved_at':datetime.now(timezone.utc).isoformat(),'truncated':tree.truncated,'mode':'static-html'}
        self.fields={}
        if remember:
            self.history=self.history[:self.position+1]+[final];self.history=self.history[-30:];self.position=len(self.history)-1
        return self.observe()
    def act(self,action,args):
        if action not in self.actions or set(args)!=set(self.actions[action]):raise ValueError('Use the browser action and its declared fields.')
        if action=='open':return self.open(args['url'])
        if action in ('back','forward'):
            target=self.position+(-1 if action=='back' else 1)
            if not 0<=target<len(self.history):raise ValueError('No page in that direction.')
            result=self.open(self.history[target],False);self.position=target;return result
        node=self.node(args['id']);attrs=node['attrs']
        if action=='click':
            if node['tag']=='a' and attrs.get('href'):return self.open(attrs['href'])
            if node['tag'] in ('button','input') and attrs.get('type','submit')=='submit':
                forms=[i for i in node['ancestors'] if self.node(i)['tag']=='form']
                if forms:return self.act('submit',{'id':forms[-1]})
            raise ValueError('This node is not an HTML link or supported submit control.')
        if action=='type':
            if node['tag'] not in ('input','textarea') or attrs.get('type','text') not in ('text','search','email','url','number','') or 'disabled' in attrs:raise ValueError('Choose an editable text input.')
            if not isinstance(args['text'],str) or len(args['text'])>2000:raise ValueError('Enter at most 2000 characters.')
            self.fields[node['id']]=args['text'];return {'id':node['id'],'value':args['text'],'url':self.page['url']}
        if node['tag']!='form':raise ValueError('Choose a form node.')
        if attrs.get('method','get').lower()!='get':raise ValueError('This first web reader submits GET search forms only.')
        fields=[]
        for n in self.page['nodes']:
            a=n['attrs']
            if node['id'] not in n['ancestors'] or n['tag'] not in ('input','textarea') or not a.get('name') or 'disabled' in a:continue
            if a.get('type','text') in ('submit','button','file','password','reset'):continue
            if a.get('type') in ('checkbox','radio') and 'checked' not in a:continue
            fields.append((a['name'],self.fields.get(n['id'],a.get('value',''))))
        p=urlsplit(attrs.get('action') or self.page['url'])
        return self.open(urlunsplit((p.scheme,p.netloc,p.path,urlencode(parse_qsl(p.query)+fields),'')))
