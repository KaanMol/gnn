"""Author reusable algebra graphs. The application never imports this builder.

Polynomials use ascending rational coefficients. AST tokens are syntax only;
operator meaning, distribution, collecting terms and solving live in this data.
"""
import json
from pathlib import Path
from graph_dsl import Graph


class G(Graph):
    def num(self, value): return self.op('as_number', value, kind='Number')
    def data_num(self, value): return self.op('as_data', value)
    def calc(self, op, *args): return self.data_num(self.op(op, *(self.num(a) for a in args), kind='Number'))
    def lt(self, a, b): return self.op('less', self.num(a), self.num(b), kind='Bool')
    def ne(self, a, b): return self.op('not', self.op('equal', self.num(a), self.num(b), kind='Bool'), kind='Bool')
    def eqn(self, a, b): return self.op('equal', self.num(a), self.num(b), kind='Bool')
    def both(self, a, b): return self.op('and', a, b, kind='Bool')
    def either(self, a, b): return self.op('or', a, b, kind='Bool')
    def inverse(self, a): return self.op('not', a, kind='Bool')
    def length(self, a): return self.data_num(self.size(a))
    def item(self, a, i): return self.op('item', a, i)
    def append(self, a, v): return self.op('concat', a, self.op('data_list', v))
    def loop(self, initial, guard, body): return self.op('while', initial, guard=guard, body=body)
    def emit(self, value, label, evidence=None): return self.op('emit', value, evidence or value, label=label)


def build():
    suite = {}
    def save(name, g, out, description):
        suite[name] = {'graph':g.finish(out, description=description, trace_mode='explicit'),
                       'source':'Teacher-supplied general algebra curriculum: '+description}

    g=G(); save('algebra_policy',g,g.data({'max_exponent':12,'trial_divisor_limit':20000}),
                 'Bound expansion to exponent 12 and divisor trials to 20,000. An unresolved factor is not a proof of no roots.')

    guard=G(); run=guard.both(guard.lt(guard.data(1),guard.length(guard.input)),
                             guard.eqn(guard.item(guard.input,guard.data(-1)),guard.data(0)))
    body=G(); cut=body.op('slice',body.input,stop=-1)
    g=G(); out=g.loop(g.input,guard.finish(run,'Bool'),body.finish(cut))
    save('poly_trim',g,out,'Remove zero coefficients above the highest nonzero power; retain one coefficient for zero.')

    g=G(); p=g.get(g.input,'p'); i=g.get(g.input,'index')
    inbounds=g.both(g.inverse(g.lt(i,g.data(0))),g.lt(i,g.length(p)))
    save('poly_coefficient',g,g.choose(inbounds,g.item(p,i),g.data(0)),'A missing power has coefficient zero.')

    for name, operation, initial in [('algebra_sum','add',0),('algebra_product','multiply',1)]:
        guard=G(); run=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'items')))
        body=G(); s=body.input; i=body.get(s,'i'); items=body.get(s,'items')
        updated=body.record(items=items,i=body.calc('add',i,body.data(1)),
                            value=body.calc(operation,body.get(s,'value'),body.item(items,i)))
        g=G(); loop=g.loop(g.record(items=g.input,i=g.data(0),value=g.data(initial)),guard.finish(run,'Bool'),body.finish(updated))
        save(name,g,g.get(loop,'value'),'Fold a sequence using '+operation+'.')

    body=G(); ctx=body.get(body.input,'context'); i=body.get(body.input,'item')
    a=body.call('poly_coefficient',body.record(p=body.get(ctx,'a'),index=i))
    b=body.call('poly_coefficient',body.record(p=body.get(ctx,'b'),index=i))
    sum_value=body.calc('add',a,b)
    g=G(); positions=g.op('indices',g.op('concat',g.get(g.input,'a'),g.get(g.input,'b')))
    out=g.call('poly_trim',g.map(positions,body.finish(sum_value),g.input))
    save('poly_add',g,g.emit(out,'collect_like_terms'),'Add coefficients of equal powers; missing terms contribute zero.')

    body=G(); value=body.calc('multiply',body.get(body.input,'item'),body.get(body.input,'context'))
    g=G(); out=g.call('poly_trim',g.map(g.get(g.input,'p'),body.finish(value),g.get(g.input,'k')))
    save('poly_scale',g,out,'Multiply every coefficient by the same scalar.')

    product=G(); ctx=product.get(product.input,'context'); i=product.get(product.input,'item')
    a=product.item(product.get(ctx,'a'),i)
    b=product.call('poly_coefficient',product.record(p=product.get(ctx,'b'),index=product.calc('subtract',product.get(ctx,'k'),i)))
    term=product.calc('multiply',a,b)
    body=G(); ctx=body.get(body.input,'context'); k=body.get(body.input,'item')
    products=body.map(body.op('indices',body.get(ctx,'a')),product.finish(term),body.record(a=body.get(ctx,'a'),b=body.get(ctx,'b'),k=k))
    total=body.call('algebra_sum',products)
    g=G(); indices=g.op('indices',g.op('concat',g.get(g.input,'a'),g.get(g.input,'b')))
    result=g.call('poly_trim',g.map(indices,body.finish(total),g.input))
    save('poly_multiply',g,g.emit(result,'distribute_and_collect'),'Distribute products: coefficient k is the sum of a[i] times b[k-i].')

    guard=G(); run=guard.lt(guard.data(0),guard.get(guard.input,'n'))
    body=G(); p=body.get(body.input,'p'); n=body.get(body.input,'n')
    updated=body.record(p=p,n=body.calc('subtract',n,body.data(1)),value=body.call('poly_multiply',body.record(a=body.get(body.input,'value'),b=p)))
    g=G(); n=g.get(g.input,'n'); config=g.call('algebra_policy',g.input)
    allowed=g.both(g.op('is_integer',g.num(n),kind='Bool'),g.both(g.inverse(g.lt(n,g.data(0))),g.inverse(g.lt(g.get(config,'max_exponent'),n))))
    checked=g.op('require',allowed,g.input,message='The taught polynomial power lesson supports nonnegative integer exponents up to its stored limit.')
    loop=g.loop(g.record(p=g.get(checked,'p'),n=g.get(checked,'n'),value=g.data([1])),guard.finish(run,'Bool'),body.finish(updated))
    save('poly_power',g,g.get(loop,'value'),'Expand a nonnegative integer power by repeated polynomial multiplication.')

    g=G(); b=g.get(g.input,'b'); a=g.get(g.input,'a')
    constant=g.eqn(g.length(b),g.data(1))
    divisor=g.op('require',constant,g.item(b,g.data(0)),message='Division by an expression containing the unknown needs rational-expression lessons; it is not cancelled automatically.')
    reciprocal=g.op('require',g.ne(divisor,g.data(0)),g.calc('divide',g.data(1),divisor),message='Division by zero is undefined; this equation has an undefined expression.')
    save('poly_divide_constant',g,g.call('poly_scale',g.record(p=a,k=reciprocal)),'Divide all coefficients by a nonzero constant; refuse variable denominators.')

    # Interpret a flat syntax token with its already interpreted child results.
    g=G(); token=g.get(g.input,'token'); values=g.get(g.input,'values'); op=g.get(token,'op'); args=g.get(token,'args')
    a=g.item(values,g.item(args,g.data(0))); b=g.item(values,g.item(args,g.data(1)))
    negative=g.call('poly_scale',g.record(p=a,k=g.data(-1)))
    minus_b=g.call('poly_scale',g.record(p=b,k=g.data(-1)))
    subtract=g.call('poly_add',g.record(a=a,b=minus_b))
    exponent=g.op('require',g.eqn(g.length(b),g.data(1)),g.item(b,g.data(0)),message='The exponent must be a nonnegative integer constant.')
    result=g.op('require',g.eq(g.data('known'),g.data('unknown')),g.data([0]),message='No taught polynomial meaning for this operator.')
    meanings=[('number',g.op('data_list',g.data_num(g.num(g.get(token,'value'))))),('symbol',g.data([0,1])),
              ('negate',negative),('+',g.call('poly_add',g.record(a=a,b=b))),('-',subtract),('=',subtract),
              ('*',g.call('poly_multiply',g.record(a=a,b=b))),('/',g.call('poly_divide_constant',g.record(a=a,b=b))),
              ('^',g.call('poly_power',g.record(p=a,n=exponent)))]
    for symbol,value in reversed(meanings): result=g.choose(g.eq(op,g.data(symbol)),value,result)
    save('algebra_token',g,result,'Interpret numbers, the unknown and arithmetic syntax as polynomials. Subtract equation sides to preserve equality with zero.')

    guard=G(); run=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'tokens')))
    body=G(); i=body.get(body.input,'i'); tokens=body.get(body.input,'tokens'); values=body.get(body.input,'values')
    interpreted=body.call('algebra_token',body.record(token=body.item(tokens,i),values=values))
    updated=body.record(tokens=tokens,i=body.calc('add',i,body.data(1)),values=body.append(values,interpreted))
    g=G(); state=g.loop(g.record(tokens=g.get(g.input,'tokens'),i=g.data(0),values=g.data([])),guard.finish(run,'Bool'),body.finish(updated))
    result=g.item(g.get(state,'values'),g.data(-1))
    save('algebra_normalize',g,g.emit(result,'polynomial_normal_form'),'Read syntax in postorder; execute taught operator meanings; return ascending coefficients.')

    guard=G(); run=guard.inverse(guard.lt(guard.get(guard.input,'i'),guard.data(0)))
    body=G(); p=body.get(body.input,'p'); x=body.get(body.input,'x'); i=body.get(body.input,'i')
    value=body.calc('add',body.item(p,i),body.calc('multiply',body.get(body.input,'value'),x))
    updated=body.record(p=p,x=x,i=body.calc('subtract',i,body.data(1)),value=value)
    g=G(); p=g.get(g.input,'p'); loop=g.loop(g.record(p=p,x=g.get(g.input,'x'),i=g.calc('subtract',g.length(p),g.data(1)),value=g.data(0)),guard.finish(run,'Bool'),body.finish(updated))
    save('poly_evaluate',g,g.get(loop,'value'),'Horner evaluation: repeatedly multiply the accumulated value by x and add the next coefficient.')

    guard=G(); run=guard.lt(guard.data(0),guard.get(guard.input,'i'))
    body=G(); s=body.input; p=body.get(s,'p'); root=body.get(s,'root'); i=body.get(s,'i')
    carry=body.calc('add',body.item(p,i),body.calc('multiply',root,body.get(s,'carry')))
    q=body.op('concat',body.op('data_list',carry),body.get(s,'q'))
    updated=body.record(p=p,root=root,i=body.calc('subtract',i,body.data(1)),carry=carry,q=q)
    g=G(); p=g.get(g.input,'p'); root=g.get(g.input,'root'); lead=g.item(p,g.data(-1))
    loop=g.loop(g.record(p=p,root=root,i=g.calc('subtract',g.length(p),g.data(2)),carry=lead,q=g.op('data_list',lead)),guard.finish(run,'Bool'),body.finish(updated))
    remainder=g.calc('add',g.item(p,g.data(0)),g.calc('multiply',root,g.get(loop,'carry')))
    save('poly_synthetic_divide',g,g.record(quotient=g.call('poly_trim',g.get(loop,'q')),remainder=remainder),'Divide by (x-r) using synthetic division and return the exact remainder. A factor requires remainder zero.')

    # Integer square root is itself taught binary search, using generic floor.
    guard=G(); run=guard.lt(guard.data(1),guard.calc('subtract',guard.get(guard.input,'hi'),guard.get(guard.input,'lo')))
    body=G(); n=body.get(body.input,'n'); lo=body.get(body.input,'lo'); hi=body.get(body.input,'hi')
    mid=body.calc('floor',body.calc('divide',body.calc('add',lo,hi),body.data(2)))
    small=body.inverse(body.lt(n,body.calc('multiply',mid,mid)))
    updated=body.record(n=n,lo=body.choose(small,mid,lo),hi=body.choose(small,hi,mid))
    g=G(); allowed=g.both(g.op('is_integer',g.num(g.input),kind='Bool'),g.inverse(g.lt(g.input,g.data(0))))
    n=g.op('require',allowed,g.input,message='Integer square-root search requires a nonnegative integer.')
    loop=g.loop(g.record(n=n,lo=g.data(0),hi=g.calc('add',n,g.data(1))),guard.finish(run,'Bool'),body.finish(updated))
    save('integer_sqrt',g,g.get(loop,'lo'),'Binary-search the greatest integer whose square is at most the input.')

    g=G(); n=g.calc('numerator',g.input); d=g.calc('denominator',g.input)
    product=g.calc('multiply',n,d); root=g.call('integer_sqrt',product)
    exact=g.eqn(g.calc('multiply',root,root),product)
    save('rational_sqrt',g,g.record(exact=g.op('bool_data',exact),value=g.calc('divide',root,d)),
         'For nonnegative n/d, test whether n*d has an integer square root. When exact, sqrt(n/d)=sqrt(n*d)/d.')

    g=G(); b=g.item(g.input,g.data(0)); a=g.item(g.input,g.data(1)); root=g.calc('divide',g.calc('negate',b),a)
    save('algebra_linear',g,g.emit(g.record(roots=g.op('data_list',root),complete=g.data(True)), 'isolate_linear_variable'),
         'For a*x+b=0 with nonzero a, subtract b and divide by a.')

    g=G(); c=g.item(g.input,g.data(0)); b=g.item(g.input,g.data(1)); a=g.item(g.input,g.data(2))
    disc=g.calc('subtract',g.calc('multiply',b,b),g.calc('multiply',g.data(4),g.calc('multiply',a,c)))
    numerator=g.calc('negate',b); denominator=g.calc('multiply',g.data(2),a); sqrt=g.call('rational_sqrt',disc)
    positive=g.calc('divide',g.calc('add',numerator,g.get(sqrt,'value')),denominator)
    negative=g.calc('divide',g.calc('subtract',numerator,g.get(sqrt,'value')),denominator)
    real_roots=g.op('data_list',positive,negative)
    radicals=g.op('data_list',*(g.record(kind=g.data('radical'),numerator=numerator,radicand=disc,denominator=denominator,sign=g.data(sign)) for sign in (1,-1)))
    roots=g.choose(g.lt(disc,g.data(0)),g.data([]),g.choose(g.op('as_bool',g.get(sqrt,'exact'),kind='Bool'),real_roots,radicals))
    save('algebra_quadratic',g,g.emit(g.record(roots=roots,complete=g.data(True),discriminant=disc),'quadratic_formula'),
         'For a*x^2+b*x+c=0 use (-b +/- sqrt(b^2-4ac))/(2a). Negative discriminant has no real roots; keep irrational roots symbolic.')

    # Rational-root candidates: clear denominators, then signed divisors of
    # constant coefficient divided by divisors of leading coefficient.
    body=G(); denominator=body.calc('denominator',body.input)
    g=G(); multiple=g.call('algebra_product',g.map(g.input,body.finish(denominator)))
    save('poly_integerize',g,g.call('poly_scale',g.record(p=g.input,k=multiple)),'Multiply coefficients by the product of their denominators; nonzero scaling preserves roots.')

    guard=G(); i=guard.get(guard.input,'i'); n=guard.get(guard.input,'n'); limit=guard.get(guard.input,'limit')
    run=guard.both(guard.inverse(guard.lt(n,guard.calc('multiply',i,i))),guard.inverse(guard.lt(limit,i)))
    body=G(); s=body.input; n=body.get(s,'n'); i=body.get(s,'i'); factors=body.get(s,'factors'); quotient=body.calc('divide',n,i)
    is_divisor=body.op('is_integer',body.num(quotient),kind='Bool')
    added=body.op('unique',body.op('concat',factors,body.op('data_list',i,quotient)))
    updated=body.record(n=n,i=body.calc('add',i,body.data(1)),limit=body.get(s,'limit'),factors=body.choose(is_divisor,added,factors))
    g=G(); n=g.choose(g.lt(g.input,g.data(0)),g.calc('negate',g.input),g.input)
    n=g.op('require',g.both(g.lt(g.data(0),n),g.op('is_integer',g.num(n),kind='Bool')),n,message='Divisor enumeration requires a nonzero integer.')
    config=g.call('algebra_policy',g.input)
    loop=g.loop(g.record(n=n,i=g.data(1),limit=g.get(config,'trial_divisor_limit'),factors=g.data([])),guard.finish(run,'Bool'),body.finish(updated))
    save('integer_divisors',g,g.get(loop,'factors'),'Try integer divisors and paired quotients, within the taught trial budget.')

    guard=G(); run=guard.both(guard.lt(guard.get(guard.input,'pi'),guard.length(guard.get(guard.input,'ps'))),guard.inverse(guard.op('as_bool',guard.get(guard.input,'found'),kind='Bool')))
    body=G(); s=body.input; ps=body.get(s,'ps'); qs=body.get(s,'qs'); pi=body.get(s,'pi'); qi=body.get(s,'qi'); p=body.get(s,'p')
    candidate=body.calc('divide',body.item(ps,pi),body.item(qs,qi)); minus=body.calc('negate',candidate)
    poszero=body.eqn(body.call('poly_evaluate',body.record(p=p,x=candidate)),body.data(0))
    negzero=body.eqn(body.call('poly_evaluate',body.record(p=p,x=minus)),body.data(0))
    found=body.either(poszero,negzero); nextqi=body.calc('add',qi,body.data(1)); wrap=body.eqn(nextqi,body.length(qs))
    updated=body.record(p=p,ps=ps,qs=qs,pi=body.choose(wrap,body.calc('add',pi,body.data(1)),pi),qi=body.choose(wrap,body.data(0),nextqi),
                        found=body.op('bool_data',found),root=body.choose(poszero,candidate,minus))
    g=G(); p=g.call('poly_integerize',g.input)
    ps=g.call('integer_divisors',g.item(p,g.data(0))); qs=g.call('integer_divisors',g.item(p,g.data(-1)))
    loop=g.loop(g.record(p=p,ps=ps,qs=qs,pi=g.data(0),qi=g.data(0),found=g.data(False),root=g.data(0)),guard.finish(run,'Bool'),body.finish(updated))
    save('poly_rational_root',g,g.record(found=g.get(loop,'found'),root=g.get(loop,'root')),'Test signed rational-root-theorem candidates by exact substitution. Failure only means no factor found within the search budget.')

    g=G(); p=g.input; degree=g.calc('subtract',g.length(p),g.data(1))
    # The mean-of-roots candidate comes from coefficients, never a stored answer.
    mean=g.calc('divide',g.calc('negate',g.item(p,g.data(-2))),g.calc('multiply',degree,g.item(p,g.data(-1))))
    mean_is_root=g.eqn(g.call('poly_evaluate',g.record(p=p,x=mean)),g.data(0))
    is_zero=g.eqn(g.item(p,g.data(0)),g.data(0))
    result=g.choose(is_zero,g.record(found=g.data(True),root=g.data(0)),
                     g.choose(mean_is_root,g.record(found=g.data(True),root=mean),g.call('poly_rational_root',p)))
    save('poly_find_root',g,result,'Try zero, then -a[n-1]/(n*a[n]) (the only possible root of a repeated linear power); verify exactly, then search rational candidates.')

    guard=G(); run=guard.both(guard.lt(guard.data(3),guard.length(guard.get(guard.input,'p'))),guard.op('as_bool',guard.get(guard.input,'progress'),kind='Bool'))
    body=G(); s=body.input; p=body.get(s,'p'); roots=body.get(s,'roots'); found=body.call('poly_find_root',p); root=body.get(found,'root')
    division=body.call('poly_synthetic_divide',body.record(p=p,root=root))
    checked=body.op('require',body.eqn(body.get(division,'remainder'),body.data(0)),body.get(division,'quotient'),message='The proposed factor failed its exact remainder check.')
    divided=body.record(p=checked,roots=body.append(roots,root),progress=body.data(True))
    divided=body.emit(divided,'factor_by_zero_remainder',body.record(root=root,quotient=checked,remainder=body.get(division,'remainder')))
    stopped=body.record(p=p,roots=roots,progress=body.data(False))
    updated=body.choose(body.op('as_bool',body.get(found,'found'),kind='Bool'),divided,stopped)
    g=G(); loop=g.loop(g.record(p=g.input,roots=g.data([]),progress=g.data(True)),guard.finish(run,'Bool'),body.finish(updated))
    p=g.get(loop,'p'); length=g.length(p)
    terminal=g.choose(g.eqn(length,g.data(1)),g.record(roots=g.data([]),complete=g.data(True)),
               g.choose(g.eqn(length,g.data(2)),g.call('algebra_linear',p),
                 g.choose(g.eqn(length,g.data(3)),g.call('algebra_quadratic',p),g.record(roots=g.data([]),complete=g.data(False)))))
    roots=g.op('concat',g.get(loop,'roots'),g.get(terminal,'roots'))
    identity=g.both(g.eqn(g.length(g.input),g.data(1)),g.eqn(g.item(g.input,g.data(0)),g.data(0)))
    report=g.record(roots=roots,complete=g.get(terminal,'complete'),identity=g.op('bool_data',identity),residual=p,polynomial=g.input,domain=g.data('real'))
    save('algebra_solve_polynomial',g,report,'Factor repeatedly with exact remainder checks, then solve the constant, linear or quadratic remainder. Preserve unsolved higher-degree factors.')

    g=G(); p=g.call('algebra_normalize',g.input); result=g.call('algebra_solve_polynomial',p)
    save('algebra_solve',g,g.emit(result,'algebra_result'),'Normalize both equation sides, solve using stored polynomial lessons, and report complete or partial real solutions.')
    return suite


if __name__ == '__main__':
    path=Path(__file__).parent/'curriculum/algebra.json'
    path.write_text(json.dumps(build(),indent=2)+'\n')
    print(path)
