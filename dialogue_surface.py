"""A local text port. Stored programs choose prompts and continuation state."""
from uuid import uuid4
from graph_runtime import bounded_data


class DialogueSurface:
    actions = {'say': ['text'], 'ask': ['text','resume','state'], 'wait': ['resume','state']}

    def __init__(self, store):
        self.store=store

    def observe(self):
        return {'waiting': self.store.map('interaction.state').get('waiting'), 'actions':self.actions}

    def act(self, action, arguments):
        if action not in self.actions or set(arguments)!=set(self.actions[action]):
            raise ValueError('Use the declared dialogue operation and its fields.')
        text=arguments.get('text','')
        if not isinstance(text,str) or len(text)>8000:
            raise ValueError('Dialogue text must be bounded text.')
        if action=='say':
            result={'status':'spoken','text':text}
        else:
            resume=arguments['resume']
            if not isinstance(resume,str) or len(resume)>60:
                raise ValueError('A continuation needs a stored procedure name.')
            # A missing continuation is retained visibly; it is never repaired
            # by loading source lessons or silently choosing another behavior.
            request={'id':str(uuid4()),'text':text,'resume':resume,'state':bounded_data(arguments['state'])}
            self.store.map('interaction.state')['waiting']=request
            result={'status':'waiting_for_input','text':text,'request':request}
        self.store.sequence('interaction.messages').append(result)
        return result
