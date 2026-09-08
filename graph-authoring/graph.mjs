export class G {
  nodes=[];
  constructor(){this.input=this.op('input');}
  op(op,inputs=[],fields={},type='Data'){const id='n'+this.nodes.length;this.nodes.push({id,op,inputs,type,...fields});return id;}
  data(value){return this.op('data_literal',[],{value});}
  get(a,...path){return this.op('get',[a],{path});}
  item(a,b){return this.op('item',[a,b]);}
  rec(fields){return this.op('record',Object.values(fields),{keys:Object.keys(fields)});}
  eq(a,b){return this.op('data_equal',[a,b],{},'Bool');}
  not(a){return this.op('not',[a],{},'Bool');}
  and(a,b){return this.op('and',[a,b],{},'Bool');}
  bool(a){return this.op('as_bool',[a],{},'Bool');}
  datum(a){return this.op('bool_data',[a]);}
  choose(a,b,c){return this.op('choose',[a,b,c]);}
  num(a){return this.op('as_number',[a],{},'Number');}
  calc(op,a,b){return this.op('as_data',[this.op(op,[this.num(a),this.num(b)],{},'Number')]);}
  lt(a,b){return this.op('less',[this.num(a),this.num(b)],{},'Bool');}
  len(a){return this.op('as_data',[this.op('size',[a],{},'Number')]);}
  contains(a,b){return this.op('contains',[a,b],{},'Bool');}
  list(...a){return this.op('data_list',a);}
  concat(a,b){return this.op('concat',[a,b]);}
  push(a,b){return this.concat(a,this.list(b));}
  finish(output,output_type='Data'){return {input_type:'Data',output_type,nodes:this.nodes,output,trace_mode:'explicit'};}
}
