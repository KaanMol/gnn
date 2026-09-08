// Author grammar as JSON data consumed exclusively by the stored graph parser.
import fs from 'node:fs';
const rules={};let id=0;
const add=(op,fields={})=>{const name='r'+id++;rules[name]={op,...fields,...(fields.children?{arity:fields.children.length}:{}),...(fields.characters?{width:fields.characters.length}:{})};return name;};
const literal=s=>add('literal',{characters:[...s]});
const chars=(s,positive=true)=>add('character',{characters:[...s],positive});
const seq=(...children)=>add('sequence',{children});
const choice=(...children)=>add('choice',{children});
const repeat=child=>add('repeat',{child});
const not=child=>add('not',{child});
const drop=child=>add('drop',{child});
const cap=(name,child)=>add('capture',{name,child,collapse:['ConditionalExpression','Logical','Equality','Relational','Additive','Multiplicative','PostfixExpression'].includes(name)});
const opt=child=>choice(child,seq());
const plus=child=>seq(child,repeat(child));
const named=(name,rule)=>{rules[name]=rules[rule];return name;};
const alpha='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_$',digit='0123456789';
const nc=chars(alpha+digit),first=chars(alpha),any=chars('',false);
const keyword=w=>seq(literal(w),not(nc));
const keywords=choice(...'export default function return const let if else while for do break continue true false null typeof void'.split(' ').map(keyword));
named('Space',drop(repeat(choice(literal('&#x20;'),chars(' \t\r\n'),seq(literal('//'),repeat(chars('\r\n',false))),
 seq(literal('/*'),repeat(seq(not(literal('*/')),any)),literal('*/'))))));
const tok=s=>drop(seq(literal(s),'Space'));
const kw=s=>drop(seq(keyword(s),'Space'));
const identifier=cap('Identifier',seq(first,repeat(nc)));
named('Identifier',seq(identifier,'Space'));
const escape=seq(literal('\\'),chars('"\'\\nrt'));
const string=choice(seq(literal('"'),repeat(choice(escape,chars('"\\\r\n',false))),literal('"')),
 seq(literal("'"),repeat(choice(escape,chars("'\\\r\n",false))),literal("'")));
named('String',seq(cap('StringLiteral',string),'Space'));
named('Number',seq(cap('NumberLiteral',plus(chars(digit))),not(nc),'Space'));
const separated=(item,separator=tok(','))=>seq(item,repeat(seq(separator,item)));
const params=seq(tok('('),opt(separated('Identifier')),tok(')'));
named('Function',cap('FunctionDeclaration',seq(opt(seq(kw('export'),kw('default'))),kw('function'),'Identifier',cap('Parameters',params),'Block')));
named('Block',cap('Block',seq(tok('{'),repeat('Statement'),tok('}'))));
named('Declaration',cap('VariableDeclaration',seq(cap('DeclarationKind',seq(choice(keyword('const'),keyword('let')),'Space')),'Pattern',tok('='),'Expression',tok(';'))));
named('Pattern',choice('Identifier',cap('ArrayPattern',seq(tok('['),separated('Identifier'),tok(']'))),
 cap('ObjectPattern',seq(tok('{'),separated(seq('Identifier',opt(seq(tok(':'),'Identifier')))),tok('}')))));
named('UpdateStatement',cap('UpdateStatement',choice(
 seq('Identifier',cap('UpdateOperator',seq(choice(literal('++'),literal('--')),'Space')),tok(';')),
 seq('Identifier',cap('UpdateOperator',seq(choice(literal('+='),literal('-='),literal('*='),literal('=')),'Space')),'Expression',tok(';')))));
named('ForInit',cap('ForInit',opt(choice(
 cap('VariableDeclaration',seq(cap('DeclarationKind',seq(choice(keyword('let'),keyword('const')),'Space')),'Identifier',tok('='),'Expression')),
 cap('UpdateStatement',seq('Identifier',cap('UpdateOperator',seq(literal('='),'Space')),'Expression'))))));
named('ForUpdate',cap('ForUpdate',opt(cap('UpdateStatement',choice(
 seq('Identifier',cap('UpdateOperator',seq(choice(literal('++'),literal('--')),'Space'))),
 seq('Identifier',cap('UpdateOperator',seq(choice(literal('+='),literal('-='),literal('*='),literal('=')),'Space')),'Expression'))))));
named('ForStatement',cap('ForStatement',seq(kw('for'),tok('('),'ForInit',tok(';'),cap('ForTest',opt('Expression')),tok(';'),'ForUpdate',tok(')'),'Block')));
named('DoWhileStatement',cap('DoWhileStatement',seq(kw('do'),'Block',kw('while'),tok('('),'Expression',tok(')'),tok(';'))));
named('Statement',choice('Function','Declaration','ForStatement','DoWhileStatement','UpdateStatement',cap('ReturnStatement',seq(drop(seq(keyword('return'),repeat(chars(' \t')))),not(chars('\r\n')),opt('Expression'),choice(tok(';'),not(not(literal('}')))))),
 cap('IfStatement',seq(kw('if'),tok('('),'Expression',tok(')'),'Block',opt(seq(kw('else'),choice('Block','Statement'))))),
 cap('WhileStatement',seq(kw('while'),tok('('),'Expression',tok(')'),'Block')),
 'Block',cap('ExpressionStatement',seq('Expression',tok(';')))));
named('Expression',choice(cap('ArrowFunction',seq(cap('Parameters',choice(params,'Identifier')),tok('=>'),choice('Block','Expression'))),'Conditional'));
named('Conditional',cap('ConditionalExpression',seq('Logical',opt(seq(tok('?'),'Expression',tok(':'),'Expression')))));
function binary(name,lower,operators,captureName=name){named(name,cap(captureName,seq(lower,repeat(seq(cap('Operator',seq(choice(...operators.map(literal)),'Space')),lower)))));}
binary('LogicalAnd','Equality',['&&'],'Logical');
binary('LogicalOr','LogicalAnd',['||'],'Logical');
named('Logical',choice(cap('Logical',seq('Equality',plus(seq(cap('Operator',seq(literal('??'),'Space')),'Equality')))),'LogicalOr'));
binary('Equality','Relational',['===','!==']);
binary('Relational','Additive',['<=','>=','<','>']);
binary('Additive','Multiplicative',['+','-']);
binary('Multiplicative','Unary',['*']);
named('Unary',choice(cap('UnaryExpression',seq(cap('Operator',seq(choice(literal('!'),literal('-'),keyword('typeof'),keyword('void')),'Space')),'Unary')),'Postfix'));
named('Postfix',cap('PostfixExpression',seq('Primary',repeat(choice(
 cap('Member',seq(tok('.'),'Identifier')),cap('Index',seq(tok('['),'Expression',tok(']'))),
 cap('Call',seq(tok('('),opt(separated('Expression')),tok(')'))))))));
named('Primary',choice('JSX','String','Number',cap('BooleanLiteral',seq(choice(keyword('true'),keyword('false')),'Space')),
 cap('NullLiteral',seq(keyword('null'),'Space')),'Identifier',seq(tok('('),'Expression',tok(')')),
 cap('ArrayExpression',seq(tok('['),opt(seq(separated(choice(cap('Spread',seq(tok('...'),'Expression')),'Expression')),opt(tok(',')))),tok(']'))),
 cap('ObjectExpression',seq(tok('{'),opt(seq(separated('Property'),opt(tok(',')))),tok('}')))));
named('Property',choice(cap('Spread',seq(tok('...'),'Expression')),cap('Property',seq(
 choice('Identifier','String','Number',cap('ComputedKey',seq(tok('['),'Expression',tok(']')))),opt(seq(tok(':'),'Expression'))))));
const markup=s=>choice(literal(s),literal('\\'+s));
const tag=cap('TagName',seq(chars(alpha.replace('_','').replace('$','')),repeat(chars(alpha+digit+'-'))));
const attrname=cap('AttributeName',plus(chars(alpha+digit+'-')));
const jsxString=choice(seq(literal('"'),repeat(chars('"',false)),literal('"')),seq(literal("'"),repeat(chars("'",false)),literal("'")));
named('JSXExpression',cap('JSXExpression',seq(drop(literal('{')),'Space',opt('Expression'),drop(literal('}')))));
named('JSXAttribute',cap('JSXAttribute',seq(attrname,'Space',opt(seq(tok('='),choice(cap('JSXString',jsxString),'JSXExpression'))),'Space')));
named('JSXChild',choice('JSXElement','JSXFragment','JSXExpression',cap('JSXText',plus(chars('<{\\',false)))));
named('JSXElement',cap('JSXElement',seq(drop(markup('<')),tag,'Space',repeat('JSXAttribute'),choice(drop(literal('/>')),
 seq(drop(literal('>')),repeat('JSXChild'),drop(markup('</')),tag,'Space',drop(literal('>')))))));
named('JSXFragment',cap('JSXFragment',seq(drop(markup('<>')),repeat('JSXChild'),drop(markup('</>')))));
named('JSX',seq(choice('JSXElement','JSXFragment'),'Space'));
named('Program',cap('Program',seq('Space',repeat('Statement'),add('end'))));
fs.writeFileSync(new URL('../curriculum/javascript-grammar.json',import.meta.url),JSON.stringify({root:'Program',rules},null,2)+'\n');
console.log('Grammar rules:',Object.keys(rules).length);
