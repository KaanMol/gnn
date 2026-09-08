"""Teacher-authored examples and reusable programming concepts."""

MAXIMUM='function maximum(xs) { if (xs.length === 0) { return null; } let best = xs[0]; for (let i = 1; i < xs.length; i++) { if (xs[i] > best) { best = xs[i]; } } return best; }'
MINIMUM=MAXIMUM.replace('maximum','minimum').replace('> best','< best')
SUM='function sum(xs) { let total = 0; for (let i = 0; i < xs.length; i++) { total += xs[i]; } return total; }'
COUNT='function countPositive(xs) { let count = 0; for (let i = 0; i < xs.length; i++) { if (xs[i] > 0) { count++; } } return count; }'
PRODUCT='function product(xs) { let total = 1; for (let i = 0; i < xs.length; i++) { total *= xs[i]; } return total; }'
ABS='function absolute(x) { if (x < 0) { return -x; } return x; }'
FACTORIAL='function factorial(x) { if (x < 0) { return null; } let result = 1; for (let i = 2; i <= x; i++) { result *= i; } return result; }'
TOGGLE_TODO='function toggleTodo(input) { return input.todos.map(todo => todo.id === input.id ? {...todo, done: !todo.done} : todo); }'
VISIBLE_TODOS='function visibleTodos(todos) { return todos.filter(todo => !todo.done); }'
CART_TOTAL='function cartTotal(items) { return items.reduce((total, item) => total + item.priceCents * item.quantity, 0); }'


def examples():
    def item(candidates,cases):return {'candidates':candidates,'tests':[{'input':x,'expected':y} for x,y in cases]}
    return {
        'maximum':item([MAXIMUM.replace('let best = xs[0];','let best = 0;'),MINIMUM,MAXIMUM],[([],None),([-9,-2,-7],-2),([3,8,1],8)]),
        'minimum':item([MAXIMUM,MINIMUM],[([],None),([-9,-2,-7],-9),([3,8,1],1)]),
        'sum':item([SUM.replace('total +=','total -='),SUM],[([],0),([1,2,3],6),([-3,1],-2)]),
        'count_positive':item([COUNT.replace('> 0','>= 0'),COUNT],[([],0),([-1,0,2,4],2)]),
        'product':item([PRODUCT.replace('total = 1','total = 0'),PRODUCT],[([],1),([2,-3,4],-24)]),
        'absolute':item([ABS.replace('return -x','return x'),ABS],[(-7,7),(0,0),(12,12)]),
        'factorial':item([FACTORIAL.replace('i <= x','i < x'),FACTORIAL],[(-1,None),(0,1),(5,120)]),
        'toggle_todo':item([TOGGLE_TODO.replace('===','!=='),TOGGLE_TODO],[
            ({'todos':[],'id':1},[]),
            ({'todos':[{'id':1,'done':False},{'id':2,'done':True}],'id':1},[{'id':1,'done':True},{'id':2,'done':True}]),
            ({'todos':[{'id':1,'done':True}],'id':1},[{'id':1,'done':False}]),
            ({'todos':[{'id':1,'done':True}],'id':9},[{'id':1,'done':True}])]),
        'visible_todos':item([VISIBLE_TODOS.replace('!todo.done','todo.done'),VISIBLE_TODOS],[
            ([],[]),([{'id':1,'done':False},{'id':2,'done':True}],[{'id':1,'done':False}])]),
        'cart_total':item([CART_TOTAL.replace('* item.quantity','+ item.quantity'),CART_TOTAL],[
            ([],0),([{'priceCents':250,'quantity':2},{'priceCents':100,'quantity':3}],800)]),
        'repair_policy':{'replacements':[['let best = 0;','let best = xs[0];'],['< best','> best'],['> best','< best'],
            ['total -=','total +='],['total = 0','total = 1'],['>= 0','> 0'],['i < x','i <= x'],['return x;','return -x;']]},
    }


CONCEPTS=[
    ('value','A piece of data manipulated by a program.','programming_expression'),
    ('type','A category of values that determines which operations are valid.','programming_require_number'),
    ('variable','A named binding whose current value is held in program state.','programming_execute'),
    ('assignment','A step that updates a variable binding.','programming_execute'),
    ('expression','A combination of values, names, and operations evaluated to a value.','programming_expression'),
    ('operator','An operation applied to one or more operands.','programming_binary'),
    ('state','The current variable bindings and execution position.','programming_execute'),
    ('sequence','Executing statements in their specified order.','programming_execute'),
    ('branch','Choosing a path according to a Boolean condition.','programming_execute'),
    ('loop','Repeating statements while a condition permits another iteration.','programming_execute'),
    ('loop invariant','A property that should hold before and after every loop iteration.','programming_overview'),
    ('function','A named program with parameters and a returned result.','programming_execute'),
    ('parameter','A name that receives an argument when a function is called.','programming_execute'),
    ('return','A statement that completes a function and supplies its result.','programming_execute'),
    ('array','An indexed sequence of values.','programming_index'),
    ('index','A position used to select an array element.','programming_index'),
    ('accumulator','A variable that carries a partial result through repeated steps.','programming_execute'),
    ('precondition','A requirement on inputs before an operation is valid.','programming_safe_integer'),
    ('postcondition','A requirement that should hold after a program completes.','js_choose_program'),
    ('test case','An input with an expected output used to check behavior.','js_choose_program'),
    ('counterexample','An input for which a proposed program violates the expected behavior.','js_choose_program'),
    ('debugging','Investigating observed behavior to locate and repair a mistake.','js_choose_program'),
    ('generalization','Working on inputs beyond those supplied as examples.','js_choose_program'),
    ('syntax','Rules governing the form of source code.','programming_overview'),
    ('semantics','Rules governing what program forms mean when executed.','programming_execute'),
    ('intermediate representation','A program form between source syntax and execution.','programming_execute'),
    ('execution trace','A record of executed steps and state changes.','programming_execute'),
    ('program synthesis','Searching for a program that meets a specification; this starter searches supplied candidates.','js_choose_program'),
    ('scope','The region in which a name denotes a particular binding.','programming_overview'),
    ('termination','Completion of execution; this interpreter also enforces a finite step budget.','programming_execute'),
    ('data record','Named fields group related values, such as an item identifier and completion flag.','js_object_get'),
    ('immutable update','Construct a changed value while leaving the original value unchanged.','js_object_spread'),
    ('callback','An operation supplied to another operation; this lesson executes inline expression callbacks.','js_array_callback_start'),
    ('mapping','Transform each input element into an output element while retaining order.','js_array_callback_resume'),
    ('filtering','Retain elements whose callback result converts to true.','js_array_callback_resume'),
    ('reduction','Combine elements in order using a supplied initial accumulator.','js_array_callback_resume'),
]
