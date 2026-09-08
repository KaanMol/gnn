"""Author decimal arithmetic as symbolic graph programs, never used at run time.

The generated lessons use text, lists, table lookup, structural equality and
control flow. They contain no numeric arithmetic instructions. Digit tables are
explicit teacher-supplied knowledge; algorithms propagate carries and borrows.
"""
import json
from pathlib import Path
from graph_dsl import G


class N(G):
    def empty(self,x): return self.eq(x,self.data([]))
    def nonempty(self,x): return self.inverse(self.empty(x))
    def first(self,x): return self.item(x,self.data(0))
    def rest(self,x): return self.op('slice',x,start=1)
    def chars(self,x): return self.op('characters',x)
    def join(self,x): return self.op('join_text',x,self.data(''))
    def pair(self,a,b): return self.record(a=a,b=b)
    def binary(self,name,a,b): return self.call(name,self.pair(a,b))
    def fallback(self,x): return self.choose(self.empty(x),self.data('0'),self.first(x))


def build():
    suite={}
    def save(name,g,out,description,kind='Data'):
        suite[name]={'graph':g.finish(out,kind,trace_mode='explicit',internal=True,description=description),
                     'source':'Explicit number curriculum: '+description}
    table={}
    for op in ('add','subtract','multiply'):
        values={}
        for a in range(10):
            for b in range(10):
                for carry in range(10 if op=='multiply' else 2):
                    value=a+b+carry if op=='add' else a-b-carry if op=='subtract' else a*b+carry
                    values[f'{a}{b}{carry}']={'digit':str(value%10),'carry':str(int(value<0) if op=='subtract' else value//10)}
        table[op]=values
    table['compare']={str(a)+str(b):'lt' if a<b else 'gt' if a>b else 'eq' for a in range(10) for b in range(10)}
    table['digits']=list('0123456789')
    table['quantities']={str(i):[None]*i for i in range(10)}
    g=N();save('number_symbols',g,g.data(table),'Decimal symbols, single-digit carry/borrow facts, ordering and example quantities are supplied teaching data.')
    g=N();save('quantity_zero',g,g.data([]),'Represent zero by an empty collection of unit marks.')
    g=N();save('quantity_successor',g,g.op('concat',g.input,g.data([None])),'Represent the next natural quantity by appending one unit mark.')
    g=N();save('quantity_add',g,g.op('concat',g.get(g.input,'a'),g.get(g.input,'b')),'Add quantities by concatenating their unit collections.')
    b=N();unit=b.data(None)
    g=N();save('quantity_count',g,g.map(g.input,b.finish(unit)),'Associate one unit mark with each observed item; the resulting collection represents its count.')
    g=N();save('quantity_symbol',g,g.item(g.get(g.call('number_symbols',g.input),'quantities'),g.input),'Interpret a digit glyph by looking up its taught unit collection.')
    # Canonical unsigned decimal text, with zero retained as one glyph.
    guard=N();xs=guard.input;again=guard.choose(guard.empty(xs),guard.eq(guard.data(1),guard.data(0)),guard.eq(guard.first(xs),guard.data('0')),kind='Bool')
    body=N();out=body.rest(body.input)
    g=N();xs=g.loop(g.chars(g.input),guard.finish(again,'Bool'),body.finish(out))
    save('uint_trim',g,g.choose(g.empty(xs),g.data('0'),g.join(xs)),'Remove leading zero glyphs, retaining one zero for an empty result.')
    # Right-to-left digit processing; carry/borrow values come only from tables.
    for operation in ('add','subtract'):
        guard=N();s=guard.input;again=guard.either(guard.nonempty(guard.get(s,'a')),guard.either(guard.nonempty(guard.get(s,'b')),guard.inverse(guard.eq(guard.get(s,'carry'),guard.data('0')))))
        body=N();s=body.input;a=body.get(s,'a');b=body.get(s,'b')
        key=body.textcat(body.fallback(a),body.fallback(b),body.get(s,'carry'))
        entry=body.item(body.get(s,'table'),key)
        out=body.record(a=body.rest(a),b=body.rest(b),carry=body.get(entry,'carry'),digits=body.append(body.get(s,'digits'),body.get(entry,'digit')),table=body.get(s,'table'))
        g=N();a=g.get(g.input,'a');b=g.get(g.input,'b')
        if operation=='subtract':
            a=g.op('require',g.inverse(g.eq(g.binary('uint_compare',a,b),g.data('lt'))),a,message='Unsigned subtraction requires enough units.')
        initial=g.record(a=g.op('reverse',g.chars(a)),b=g.op('reverse',g.chars(b)),carry=g.data('0'),digits=g.data([]),table=g.get(g.call('number_symbols',g.input),operation))
        loop=g.loop(initial,guard.finish(again,'Bool'),body.finish(out))
        save('uint_'+operation,g,g.call('uint_trim',g.join(g.op('reverse',g.get(loop,'digits')))),('Add with carries' if operation=='add' else 'Subtract with borrows')+' by walking decimal glyphs from right to left.')
    guard=N();s=guard.input;again=guard.either(guard.nonempty(guard.get(s,'a')),guard.nonempty(guard.get(s,'b')))
    body=N();s=body.input;a=body.get(s,'a');b=body.get(s,'b');comparison=body.item(body.get(s,'table'),body.textcat(body.fallback(a),body.fallback(b)))
    out=body.record(a=body.rest(a),b=body.rest(b),table=body.get(s,'table'),comparison=body.choose(body.eq(comparison,body.data('eq')),body.get(s,'comparison'),comparison))
    g=N();loop=g.loop(g.record(a=g.op('reverse',g.chars(g.get(g.input,'a'))),b=g.op('reverse',g.chars(g.get(g.input,'b'))),comparison=g.data('eq'),table=g.get(g.call('number_symbols',g.input),'compare')),guard.finish(again,'Bool'),body.finish(out))
    save('uint_compare',g,g.get(loop,'comparison'),'Compare padded decimal digits, letting the highest differing place decide order.')
    guard=N();s=guard.input;again=guard.either(guard.nonempty(guard.get(s,'a')),guard.inverse(guard.eq(guard.get(s,'carry'),guard.data('0'))))
    body=N();s=body.input;a=body.get(s,'a');entry=body.item(body.get(s,'table'),body.textcat(body.fallback(a),body.get(s,'b'),body.get(s,'carry')))
    out=body.record(a=body.rest(a),b=body.get(s,'b'),carry=body.get(entry,'carry'),digits=body.append(body.get(s,'digits'),body.get(entry,'digit')),table=body.get(s,'table'))
    g=N();loop=g.loop(g.record(a=g.op('reverse',g.chars(g.get(g.input,'a'))),b=g.get(g.input,'b'),carry=g.data('0'),digits=g.data([]),table=g.get(g.call('number_symbols',g.input),'multiply')),guard.finish(again,'Bool'),body.finish(out))
    save('uint_digit_product',g,g.call('uint_trim',g.join(g.op('reverse',g.get(loop,'digits')))),'Multiply by one digit with the taught product/carry table.')
    guard=N();again=guard.nonempty(guard.get(guard.input,'pending'))
    body=N();s=body.input;pending=body.get(s,'pending');part=body.binary('uint_digit_product',body.get(s,'a'),body.first(pending));shifted=body.call('uint_trim',body.textcat(body.get(s,'value'),body.data('0')))
    out=body.record(a=body.get(s,'a'),pending=body.rest(pending),value=body.binary('uint_add',shifted,part))
    g=N();loop=g.loop(g.record(a=g.get(g.input,'a'),pending=g.chars(g.get(g.input,'b')),value=g.data('0')),guard.finish(again,'Bool'),body.finish(out))
    save('uint_multiply',g,g.get(loop,'value'),'Multiply by place-value expansion, shifted partial products and taught addition.')
    guard=N();s=guard.input;again=guard.inverse(guard.eq(guard.binary('uint_compare',guard.get(s,'r'),guard.get(s,'d')),guard.data('lt')))
    body=N();s=body.input;out=body.record(r=body.binary('uint_subtract',body.get(s,'r'),body.get(s,'d')),d=body.get(s,'d'),q=body.binary('uint_add',body.get(s,'q'),body.data('1')))
    g=N();d=g.op('require',g.inverse(g.eq(g.get(g.input,'b'),g.data('0'))),g.get(g.input,'b'),message='Division by zero is undefined.')
    loop=g.loop(g.record(r=g.get(g.input,'a'),d=d,q=g.data('0')),guard.finish(again,'Bool'),body.finish(out))
    save('uint_division_digit',g,g.record(q=g.get(loop,'q'),r=g.get(loop,'r')),'Find one quotient digit by repeated subtraction while enough units remain.')
    guard=N();again=guard.nonempty(guard.get(guard.input,'pending'))
    body=N();s=body.input;pending=body.get(s,'pending');r=body.call('uint_trim',body.textcat(body.get(s,'r'),body.first(pending)))
    step=body.binary('uint_division_digit',r,body.get(s,'d'))
    out=body.record(pending=body.rest(pending),d=body.get(s,'d'),r=body.get(step,'r'),q=body.textcat(body.get(s,'q'),body.get(step,'q')))
    g=N();d=g.op('require',g.inverse(g.eq(g.get(g.input,'b'),g.data('0'))),g.get(g.input,'b'),message='Division by zero is undefined.')
    loop=g.loop(g.record(pending=g.chars(g.get(g.input,'a')),d=d,r=g.data('0'),q=g.data('')),guard.finish(again,'Bool'),body.finish(out))
    save('uint_divmod',g,g.record(q=g.call('uint_trim',g.get(loop,'q')),r=g.get(loop,'r')),'Long division: bring down each digit, choose its quotient digit, retain the remainder.')
    guard=N();again=guard.inverse(guard.eq(guard.get(guard.input,'b'),guard.data('0')))
    body=N();s=body.input;out=body.pair(body.get(s,'b'),body.get(body.binary('uint_divmod',body.get(s,'a'),body.get(s,'b')),'r'))
    g=N();loop=g.loop(g.input,guard.finish(again,'Bool'),body.finish(out))
    save('uint_gcd',g,g.get(loop,'a'),'Euclid’s algorithm: replace a,b by b,remainder until the divisor is zero.')
    # Rational representation: a sign flag, numerator and positive denominator.
    g=N();pieces=g.op('split_text',g.input,g.data('/'));n=g.first(pieces);chars=g.chars(n);negative=g.eq(g.first(chars),g.data('-'))
    save('rational_read',g,g.record(negative=g.datum(negative),n=g.choose(negative,g.join(g.rest(chars)),n),d=g.choose(g.empty(g.rest(pieces)),g.data('1'),g.first(g.rest(pieces)))),'Interpret canonical signed rational text as sign, numerator and denominator fields.')
    g=N();n=g.get(g.input,'n');d=g.get(g.input,'d');sign=g.choose(g.boolean(g.get(g.input,'negative')),g.data('-'),g.data(''))
    text=g.textcat(sign,n,g.choose(g.eq(d,g.data('1')),g.data(''),g.textcat(g.data('/'),d)))
    save('rational_text',g,g.choose(g.eq(n,g.data('0')),g.data('0'),text),'Render sign and a non-unit denominator; zero has no negative sign.')
    g=N();n=g.get(g.input,'n');d=g.op('require',g.inverse(g.eq(g.get(g.input,'d'),g.data('0'))),g.get(g.input,'d'),message='Division by zero is undefined.')
    gcd=g.binary('uint_gcd',n,d);nn=g.get(g.binary('uint_divmod',n,gcd),'q');dd=g.get(g.binary('uint_divmod',d,gcd),'q')
    save('rational_reduce',g,g.choose(g.eq(d,g.data('1')),g.call('rational_text',g.input),g.call('rational_text',g.record(negative=g.get(g.input,'negative'),n=nn,d=dd))),'Reduce numerator and denominator by their taught greatest common divisor.')
    g=N();a=g.call('rational_read',g.input)
    save('number_negate',g,g.call('rational_text',g.record(negative=g.datum(g.inverse(g.boolean(g.get(a,'negative')))),n=g.get(a,'n'),d=g.get(a,'d'))),'Negate a rational by reversing its sign, retaining canonical zero.')
    for operation in ('add','multiply','divide'):
        g=N();a=g.call('rational_read',g.get(g.input,'a'));b=g.call('rational_read',g.get(g.input,'b'))
        same=g.eq(g.get(a,'negative'),g.get(b,'negative'))
        if operation=='add':
            x=g.binary('uint_multiply',g.get(a,'n'),g.get(b,'d'));y=g.binary('uint_multiply',g.get(b,'n'),g.get(a,'d'))
            lower=g.eq(g.binary('uint_compare',x,y),g.data('lt'))
            n=g.choose(same,g.binary('uint_add',x,y),g.choose(lower,g.binary('uint_subtract',y,x),g.binary('uint_subtract',x,y)))
            sign=g.choose(same,g.get(a,'negative'),g.choose(lower,g.get(b,'negative'),g.get(a,'negative')))
            d=g.binary('uint_multiply',g.get(a,'d'),g.get(b,'d'))
        else:
            n=g.binary('uint_multiply',g.get(a,'n'),g.get(b,'n' if operation=='multiply' else 'd'))
            d=g.binary('uint_multiply',g.get(a,'d'),g.get(b,'d' if operation=='multiply' else 'n'))
            sign=g.datum(g.inverse(same))
        save('number_'+operation,g,g.call('rational_reduce',g.record(negative=sign,n=n,d=d)),'Rational '+operation+' using taught unsigned arithmetic, sign rules and reduction.')
    g=N();save('number_subtract',g,g.binary('number_add',g.get(g.input,'a'),g.call('number_negate',g.get(g.input,'b'))),'Subtract by adding the negation.')
    for operation in ('less','equal'):
        g=N();a=g.call('rational_read',g.get(g.input,'a'));b=g.call('rational_read',g.get(g.input,'b'));same=g.eq(g.get(a,'negative'),g.get(b,'negative'))
        x=g.binary('uint_multiply',g.get(a,'n'),g.get(b,'d'));y=g.binary('uint_multiply',g.get(b,'n'),g.get(a,'d'));order=g.binary('uint_compare',x,y)
        if operation=='equal': answer=g.both(same,g.eq(order,g.data('eq')))
        else: answer=g.choose(same,g.choose(g.boolean(g.get(a,'negative')),g.eq(order,g.data('gt')),g.eq(order,g.data('lt')),kind='Bool'),g.boolean(g.get(a,'negative')),kind='Bool')
        save('number_'+operation,g,answer,'Compare rational values by sign and cross-multiplied magnitudes.','Bool')
    for operation in ('numerator','denominator','is_integer','floor'):
        g=N();a=g.call('rational_read',g.input);n=g.get(a,'n');d=g.get(a,'d');sign=g.get(a,'negative')
        if operation=='is_integer': result=g.eq(d,g.data('1'))
        elif operation=='denominator':result=d
        elif operation=='numerator':result=g.call('rational_text',g.record(negative=sign,n=n,d=g.data('1')))
        else:
            parts=g.binary('uint_divmod',n,d);q=g.get(parts,'q')
            adjust=g.both(g.boolean(sign),g.inverse(g.eq(g.get(parts,'r'),g.data('0'))))
            result=g.call('rational_text',g.record(negative=sign,n=g.choose(adjust,g.binary('uint_add',q,g.data('1')),q),d=g.data('1')))
        save('number_'+operation,g,result,'Interpret the taught rational representation to obtain '+operation+'.','Bool' if operation=='is_integer' else 'Data')
    guard=N();again=guard.inverse(guard.eq(guard.get(guard.input,'exponent'),guard.data('0')))
    body=N();s=body.input;half=body.binary('uint_divmod',body.get(s,'exponent'),body.data('2'))
    product=body.choose(body.eq(body.get(half,'r'),body.data('1')),body.binary('number_multiply',body.get(s,'value'),body.get(s,'base')),body.get(s,'value'))
    out=body.record(exponent=body.get(half,'q'),base=body.binary('number_multiply',body.get(s,'base'),body.get(s,'base')),value=product)
    g=N();exponent=g.call('rational_read',g.get(g.input,'b'));integer=g.eq(g.get(exponent,'d'),g.data('1'));within=g.inverse(g.eq(g.binary('uint_compare',g.get(exponent,'n'),g.data('100')),g.data('gt')))
    exponent=g.op('require',g.both(integer,within),exponent,message='Power exceeds the taught integer-exponent limit.')
    base=g.choose(g.boolean(g.get(exponent,'negative')),g.binary('number_divide',g.data('1'),g.get(g.input,'a')),g.get(g.input,'a'))
    loop=g.loop(g.record(exponent=g.get(exponent,'n'),base=base,value=g.data('1')),guard.finish(again,'Bool'),body.finish(out))
    save('number_power',g,g.get(loop,'value'),'Compute bounded integer powers by repeated squaring, using a reciprocal for negative exponents.')
    guard=N();again=guard.nonempty(guard.get(guard.input,'pending'))
    body=N();s=body.input;out=body.record(pending=body.rest(body.get(s,'pending')),count=body.binary('uint_add',body.get(s,'count'),body.data('1')))
    g=N();kind=g.op('kind_of',g.input);items=g.choose(g.eq(kind,g.data('record')),g.op('keys',g.input),g.choose(g.eq(kind,g.data('text')),g.chars(g.input),g.input))
    loop=g.loop(g.record(pending=items,count=g.data('0')),guard.finish(again,'Bool'),body.finish(out))
    save('number_count_units',g,g.get(loop,'count'),'Count a collection by removing one item at a time and applying the taught decimal successor operation.')
    g=N();kind=g.op('kind_of',g.input);items=g.choose(g.eq(kind,g.data('record')),g.op('keys',g.input),g.choose(g.eq(kind,g.data('text')),g.chars(g.input),g.input))
    save('number_count',g,g.call('number_count_units',g.call('quantity_count',items)),'Count one unit per item, independently of the meanings of the individual items.')
    guard=N();again=guard.inverse(guard.eq(guard.get(guard.input,'current'),guard.get(guard.input,'stop')))
    body=N();s=body.input;out=body.record(current=body.binary('number_add',body.get(s,'current'),body.get(s,'step')),stop=body.get(s,'stop'),step=body.get(s,'step'),values=body.append(body.get(s,'values'),body.get(s,'current')))
    g=N();a=g.get(g.input,'a');b=g.get(g.input,'b');valid=g.both(g.call('number_is_integer',a,'Bool'),g.call('number_is_integer',b,'Bool'))
    a=g.op('require',valid,a,message='Range requires integer endpoints.')
    step=g.choose(g.call('number_less',g.pair(b,a),'Bool'),g.data('-1'),g.data('1'))
    loop=g.loop(g.record(current=a,stop=g.binary('number_add',b,step),step=step,values=g.data([])),guard.finish(again,'Bool'),body.finish(out))
    save('number_range',g,g.get(loop,'values'),'Enumerate inclusive integer endpoints using the taught successor or predecessor operation.')
    g=N();count=g.call('number_count',g.input)
    save('number_indices',g,g.choose(g.eq(count,g.data('0')),g.data([]),g.binary('number_range',g.data('0'),g.binary('number_subtract',count,g.data('1')))),'Generate ordinal positions by counting the collection and enumerating from zero.')
    digit=N();good=digit.op('contains',digit.get(digit.call('number_symbols',digit.input),'digits'),digit.input,kind='Bool')
    g=N();chars=g.chars(g.input);flags=g.map(chars,digit.finish(digit.datum(good)))
    valid=g.both(g.nonempty(chars),g.inverse(g.op('contains',flags,g.data(False),kind='Bool')))
    save('decimal_read_digits',g,g.call('uint_trim',g.op('require',valid,g.input,message='The taught number reader needs decimal digit symbols.')),'Validate each glyph against the taught decimal alphabet before interpreting its place values.')
    zero=N();z=zero.data('0')
    g=N();parts=g.op('split_text',g.input,g.data('.'));parts=g.op('require',g.empty(g.rest(g.rest(parts))),parts,message='A decimal has at most one point.')
    whole=g.first(parts);fraction=g.choose(g.empty(g.rest(parts)),g.data(''),g.first(g.rest(parts)))
    joined=g.textcat(whole,fraction);n=g.call('decimal_read_digits',joined)
    d=g.textcat(g.data('1'),g.join(g.map(g.chars(fraction),zero.finish(z))))
    save('decimal_read_unsigned',g,g.record(n=n,d=d),'Interpret a decimal point by placing fractional digits over a one followed by one zero per fractional place.')
    g=N();chars=g.chars(g.input);chars=g.op('require',g.nonempty(chars),chars,message='A number needs symbols.')
    negative=g.eq(g.first(chars),g.data('-'));unsigned=g.choose(negative,g.join(g.rest(chars)),g.input)
    parts=g.op('split_text',unsigned,g.data('/'));parts=g.op('require',g.empty(g.rest(g.rest(parts))),parts,message='A rational literal has at most one fraction separator.')
    numerator=g.call('decimal_read_unsigned',g.first(parts));divisor=g.choose(g.empty(g.rest(parts)),g.data('1'),g.call('decimal_read_digits',g.first(g.rest(parts))))
    result=g.call('rational_reduce',g.record(negative=g.datum(negative),n=g.get(numerator,'n'),d=g.binary('uint_multiply',g.get(numerator,'d'),divisor)))
    save('number_parse',g,result,'Interpret sign, decimal point and a fraction separator using the taught digit alphabet, place values and reduction rules.')
    for name, entry in suite.items():
        entry['graph']['memoize'] = True
        if name.startswith('number_') and name not in {'number_symbols','number_count_units'}:
            entry['graph']['interface'] = ['size','length'] if name=='number_count' else name[len('number_'):]
    return suite


if __name__=='__main__':
    path=Path(__file__).parent/'curriculum/numbers.json'
    path.write_text(json.dumps(build(),indent=2)+'\n')
    print(path)
