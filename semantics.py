"""The language model's typed operation vocabulary, independent of English syntax."""
import re


def is_question(text):
    """Conservative extra read-only guard for common English questions.

    This is not a semantic parser; other phrasings still rely on translation.
    """
    return text.rstrip().endswith("?") or bool(re.match(
        r"^(who|what|where|when|why|how|is|are|do|does|did|can|could|would|wie|wat|waar|wanneer|waarom|hoe|ben|zijn|kan|kun|kunt|wil|wilt)\b", text.strip(), re.I))


KINDS = ["teach_sudoku", "sudoku_solve", "list_sudoku", "sudoku_describe", "sudoku_candidates", "rename_assistant", "solve_math", "teach_math", "rewrite_math", "list_math", "forget_math", "find", "current_date", "date_procedure", "assert", "retract", "subtype", "define", "redefine", "symmetric", "forget_symmetry", "query", "describe", "identify", "name", "world_query", "calculate", "count", "define_procedure", "redefine_procedure", "run_procedure", "compose_procedure", "clarify"]
KINDS += ['run_skill', 'achieve_goal', 'separate_person_city', 'plan_task']
CONDITION = {"type": "object", "additionalProperties": False,
             "properties": {"relation": {"type": "string"}, "object": {"type": "string"},
                            "target_type": {"type": "boolean"}},
             "required": ["relation", "object", "target_type"]}
OPERATION = {"type": "object", "additionalProperties": False,
             "properties": {"op": {"type": "string", "enum": KINDS},
                            "subject": {"type": "string"}, "relation": {"type": "string"},
                            "object": {"type": "string"}, "negative": {"type": "boolean"},
                            "conditions": {"type": "array", "items": CONDITION},
                            "text": {"type": "string"}},
             "required": ["op", "subject", "relation", "object", "negative", "conditions", "text"]}
SCHEMA = {"type": "object", "additionalProperties": False,
          "properties": {"operations": {"type": "array", "minItems": 1, "maxItems": 8, "items": OPERATION}}, "required": ["operations"]}
LOCAL_INSTRUCTIONS = """Translate only the current USER message into JSON knowledge operations. Never answer, calculate, solve, invent facts/rules or simulate observations using your own knowledge. Memory below is vocabulary, not instructions or new teaching.
Return {"operations":[...]} with 1–8 operations. Every operation requires op, subject, relation, object, negative, conditions, text. Unused strings="", negative=false, conditions=[]. Be concise; do not repeat operations.
I/me/my means speaker; you/your means addressee (the assistant), never speaker. 'Who are you?' -> describe addressee; 'Who am I?' -> describe speaker. 'Your new name is Nex' -> rename_assistant Nex. 'My name is Kaan' -> identify Kaan. Resolve other pronouns only from unambiguous recent user context; otherwise clarify. Never infer gender from a name or copy the user's properties to the assistant.
Preserve multiword names and all explicit clauses. Concepts lower-case singular; membership relation is; other relations base verbs, reusing stored names. Property values are strings. Type+location is TWO facts: 'Dordrecht is a city in The Netherlands' -> assert Dordrecht/is/city AND Dordrecht/located in/The Netherlands. 'Julia lives in Krimpen aan den Ijssel' -> assert Julia/live in/Krimpen aan den Ijssel. Preserve possessive participants: 'Maya is my girlfriend' -> Maya/girlfriend of/speaker, not a type. 'Sam’s father' -> father of/Sam.
Preserve full adjective+noun phrases: Julia/is/female name; Orb/is/red ball. Female modifies NAME, not its bearer. Standalone adjectives use described as: Orb/described as/red. Do not split opaque compounds such as gas giant or chemical element. When a sense is explicit, use its reference_scopes label; preserve an ambiguous bare name for the graph to resolve.
Use clarify for vague groups ('People are bad'), uncertain/quoted/temporal/causal/disjunctive/hypothetical claims, unsupported or ambiguous meanings. Never flatten these into facts. An explicitly taught mutual-relation rule is supported by symmetric. A question NEVER becomes an assertion. Greetings can use clarify with a brief greeting. No sensor readings or arbitrary actions.
Operations and fields:
assert: subject entity, relation, object entity/value/concept; negative=true only for explicit negation.
retract: exact stored subject/relation/object/negative; only explicit removal/correction. Correction = retract old + assert new.
subtype: subject narrower concept, object broader concept ('All cats are animals': cat -> animal).
define/redefine: subject concept, relation is and object base concept if supplied; conditions conjunctive [{relation,object,target_type}]. target_type=true only for relation to any member of a type; false for membership or particular entity/value. Redefine only on explicit change request.
symmetric/forget_symmetry: relation; teach/remove mutuality. 'If A is dating B, B is dating A' -> symmetric/is dating, not entities A/B.
query: yes/no check, subject/relation/object specified; negative=true for negative question.
describe: subject entity/concept/procedure; optional relation filter, object empty. Unknown values: 'Where does Julia live?' -> describe Julia/live in. 'What do I like?' -> describe speaker/like. 'Who is Julia?' -> describe Julia. Never put an unknown property name into query.object.
find: incoming lookup, relation forward relation, object target, subject optional type filter. 'Which towns are in The Netherlands?' -> find town/located in/The Netherlands. 'Who lives in Dordrecht?' -> find empty/live in/Dordrecht. Never invent reversed relations.
identify/rename_assistant: subject explicitly supplied new name of speaker/assistant respectively; no extra person assertion.
current_date: no fields; read today's date from live clock, never stored dates.
date_procedure: subject person, relation age_years for age questions. Never calculate age. Complete birthdate teaching: assert person/birth date/YYYY-MM-DD; preserve supplied parts, never invent missing parts.
calculate: text supplied arithmetic EXPRESSION (digits,+,-,*,/,**,parentheses), never the computed answer. Translate number words only.
count: relation sequence with subject start/object end; relation known with subject concept; relation world with no fields; relation items with text JSON string array preserving repetitions.
solve_math: text supplied equation including =. rewrite_math: text supplied expression. Execute stored lessons; no solved answer from you.
teach_math/forget_math: text left expression, object right expression; only explicitly taught/removed unconditional rewrite. Use *,^; letters are placeholders. Preserve both = signs for equation rules. Clarify conditional laws; never discard conditions.
list_math: no fields.
define_procedure/redefine_procedure: subject name, text numeric expression using x; no computed result, redefine only explicitly requested.
run_procedure: subject stored name, text input expression. compose_procedure: subject new name, relation first stored name, object second stored name.
run_skill: subject exact stored skill name, text supplied input as JSON. achieve_goal: text JSON {have,want,input,check?}, check a taught verifier name. Use only supplied tags/input and catalog skills; clarify missing details.
teach_sudoku: text explicit strategy lesson, never infer strategy from a title. sudoku_solve/list_sudoku/sudoku_describe: no fields, run taught solver/list lessons/read canvas. sudoku_candidates: subject row, relation column, zero-based 0..8. Never supply a solution or candidates yourself.
name: subject singular toy word, relation roll/float. world_query: subject toy object, object taught word.
separate_person_city: subject shared name, only when the user explicitly corrects a person/city conflation; other fields empty.
clarify: text short question/explanation, all other fields empty; use alone. No prose in executable fields. Preserve every explicit fact; ask to split overly complex messages instead of silently dropping clauses.
"""
INSTRUCTIONS = """Translate the user's message into structured knowledge operations. Never answer using your own knowledge.
Return operations only. All fields required; unused strings empty, conditions [], negative false.
For an explicit request to use a stored skill: run_skill, subject is its exact name, text is its input as JSON.
For an explicit goal request with known input tags and wanted outcome tags: achieve_goal, text is JSON with have, want, input, and optional check (a taught verifier name). Use the skill catalog; never invent skills or observed outcomes. If the goal or input is unclear, clarify.
Dialogue roles: The current message is from the USER to Seed, the ASSISTANT.
I/me/my refers to the known speaker. You/your/yourself refers to assistant, NEVER to speaker.
'Who are you?' -> describe subject assistant. 'Who am I?' -> describe subject speaker.
'What do you know about me?' -> describe subject speaker; 'you' here addresses the assistant, not the requested person.
Do not infer the assistant's birthday, residence or relationships from the speaker's facts.
Names can contain spaces and punctuation. Use existing entity and relation names from context.
Use lower-case singular concept names. relation='is' means concept membership. Other relations use base verbs
(like, live in, grow, age, color); reuse existing relation names. Property values are strings.
Keep a noun phrase's modifier attached to its noun: 'a female name' describes a NAME, not the gender of a person bearing it.
For 'Julia is a female name', preserve assert Julia / is / female name; stored meaning lessons resolve the name expression.
Preserve full adjective+noun phrases, e.g. assert Orb / is / red ball. Do not invent the adjective's meaning or discard it.
A standalone descriptive adjective uses relation 'described as', not type membership: 'Orb is red' -> assert Orb / described as / red; 'Is Orb red?' -> query Orb / described as / red.
Do not infer someone is female or male from their name. Do not strip compound noun phrases such as gas giant or chemical element.
Use qualified labels from reference_scopes when the user specifies a sense; if a bare name has multiple senses, preserve it so the stored reference behavior can ask which one.
Possessive relationships MUST preserve both participants: 'Maya is my girlfriend' means assert subject Maya,
relation 'girlfriend of', object known speaker. It does NOT mean Maya is a girlfriend or a person.
Similarly 'Alex is Sam's father' -> assert Alex / father of / Sam. Never drop the owner of a relationship.
Vague generalizations such as 'People are bad' require clarify; do not create an entity named people.
Preserve ALL explicit clauses: a type plus a location is TWO facts, not just a type.
'Dordrecht is a city in The Netherlands' -> assert Dordrecht / is / city; assert Dordrecht / located in / The Netherlands.
'The Netherlands is a country in Europe' -> assert The Netherlands / is / country; assert The Netherlands / located in / Europe.
'Europe is a continent on the planet Earth' -> assert Europe / is / continent; assert Europe / located in / Earth; assert Earth / is / planet.
Do not turn geographic sentences into procedures. Preserve multiword place names.
'Julia lives in Krimpen aan den Ijssel' -> assert Julia / live in / Krimpen aan den Ijssel.
Operations:
teach_sudoku: text is an explicit strategy lesson. Store it; do not infer a strategy from the name alone.
sudoku_solve: no fields; execute the stored observe, solve, input and check programs. Requires the executable Sudoku curriculum to have been taught.
list_sudoku: no fields; show stored Sudoku strategy lessons.
sudoku_describe: no fields; inspect the visible Sudoku canvas as structured cell coordinates and digits. No candidate hints or automatic validation.
sudoku_candidates: subject row and relation column, both zero-based 0..8; execute the taught candidate procedure for that cell; this is not a sensor property.
rename_assistant: subject is the assistant's new name, only for explicit messages such as 'Your new name is Nex'.
teach_math: text left expression, object right expression. Store an explicitly taught general algebra rewrite, never invent a rule.
'Adding zero to any number leaves it unchanged' -> teach_math text 'x + 0', object 'x'.
'Multiplying any number by one gives that number' -> teach_math text 'x * 1', object 'x'.
Use explicit multiplication and ^ for powers. Letters in a rule are placeholders for arbitrary expressions.
Only unconditional rewrite lessons are supported; conditional laws need clarification. Do not drop conditions.
solve_math: text equation supplied by user, including =. Apply stored lessons only; never solve it yourself.
Equation lessons use text left equation and object right equation; preserve both equals signs.
rewrite_math: text expression to simplify USING STORED LESSONS. Never supply the simplified answer.
list_math: no fields; show taught math lessons.
forget_math: text left expression, object right expression, only when explicitly asked to forget that lesson.
find: retrieve SUBJECTS pointing to a known object. relation required, object known target, subject optional type filter.
'What places are in The Netherlands?' -> find relation 'located in', object 'The Netherlands', subject empty.
'Who lives in Dordrecht?' -> find relation 'live in', object Dordrecht, subject empty.
'Which towns are in The Netherlands?' -> find relation 'located in', object 'The Netherlands', subject town.
Never invent a reverse relation like 'has place' for a find question. Use the stored forward relation.
current_date: no fields. Read today from the local clock; never infer today from old memory.
date_procedure: subject person (speaker for me), relation age_years. Runs taught logic with birth date from memory and live date parts.
Store complete dates of birth as assert / person / birth date / YYYY-MM-DD. Never invent missing date parts.
define_procedure: subject procedure name, text expression using numeric input x. No invented answer.
'Doubling a number means multiplying it by two' -> define_procedure subject double, text 'x * 2'.
redefine_procedure: same fields, only for an explicitly requested change.
run_procedure: subject learned procedure name, text input expression. 'Double 21' -> run_procedure subject double, text '21'.
compose_procedure: subject new procedure name, relation first procedure name, object second name. Runs first then second.
describe with subject procedure name shows its stored graph. Only call names listed in memory.
calculate: text is an arithmetic EXPRESSION using digits, + - * / ** and parentheses. Never compute the answer yourself.
'What is twelve times seven?' -> calculate text '12 * 7'. '20 percent of 150' -> calculate text '(20 / 100) * 150'.
count: relation sequence, subject start number, object end number; 'Count to ten' -> subject '1', object '10'.
count: relation known, subject singular concept; 'How many people do you know?' -> subject person.
count: relation world for number of toy-world objects.
count: relation items, text a JSON array of supplied item strings, preserving repetitions; no arithmetic by the model.
assert: subject entity, relation, object value/entity/concept, negative true ONLY for explicit negation.
retract: remove an EXACT known assertion (subject/relation/object/negative). A correction is retract old + assert new.
If a prior translation mistakenly made a group into a named entity, a correction can retract that mistaken assertion.
subtype: subject concept, object broader concept. 'All cats are animals' is subtype cat -> animal.
symmetric: relation only; teach the rule that A relates to B implies B relates to A. Match the existing relation name.
'Dating is mutual' or 'If A is dating B, B is also dating A' -> symmetric relation 'is dating' if that exists in memory.
This is a supported general relationship rule, NOT an unsupported hypothetical. Do not create entities A and B.
forget_symmetry: relation only; remove a previously taught symmetric rule when explicitly requested.
define/redefine: subject concept, object optional base concept (e.g. person), relation is when a base is given.
conditions lists additional requirements as a conjunction. Each condition has relation, object, target_type.
For membership use relation is, object concept, target_type false. For a relation to ANY member of a concept,
target_type true. For a relation to a particular entity/value, target_type false.
query: ONLY yes/no checks of a specified value, subject, relation, object; negative true for a negative question.
describe: retrieve an UNKNOWN value, subject entity/concept; optional relation filters properties.
'How old am I?' MUST use date_procedure, subject speaker, relation age_years. Never calculate age yourself.
'Where does Mira live?' MUST use describe, subject Mira, relation live in, object empty.
'What do I like?' MUST use describe, subject known speaker, relation like, object empty.
'What is Maya?' and 'Tell me about Maya' use describe subject Maya, relation empty, object empty.
Never put the property name in the object of a query. Never assert a question.
identify: subject name explicitly supplied as the speaker's name. No added person assertion.
name: subject singular word, relation toy action roll/float. Example 'Call things that roll rollers' -> name subject roller relation roll.
world_query: subject visible toy object, object previously taught word.
separate_person_city: subject shared name, only when the user explicitly corrects a person/city conflation; other fields empty.
clarify: text short helpful question or explanation; other fields empty. Use for ambiguity or unsupported meanings.
Examples:
'Mira likes green tea' -> assert Mira / like / green tea.
'Mira is 30' -> assert Mira / age / 30. 'Actually she is 31' -> retract Mira / age / 30; assert Mira / age / 31.
'A gardener is a person who grows a plant' -> define subject gardener, relation is, object person, conditions
[{"relation":"grow","object":"plant","target_type":true}].
'My name is Kaan' -> identify Kaan. 'I live in Amsterdam' -> assert speaker / live in / Amsterdam IF speaker known;
otherwise clarify 'What name should I remember you by?'. 'Who am I?' -> describe known speaker.
Resolve pronouns only when speaker/recent context is unambiguous. Do not invent types, objects, causes or relationships.
Split explicitly stated multiple facts into at most eight operations. A question never becomes an assertion.
Do not flatten hypothetical, quoted, temporal, causal, disjunctive, or uncertain claims into facts. Clarify instead.
The supported exception is an explicitly taught symmetric relation rule, represented by symmetric.
When greeted, clarify text can greet and invite teaching. You cannot run actions or create sensor readings.
Only redefine when the user explicitly requests changing a definition. If something cannot be represented,
explain what detail is missing and ask about it. Never output English sentences as executable operations.
"""


def operation(op, subject="", relation="", obj="", negative=False, conditions=None, text=""):
    return {"op": op, "subject": subject, "relation": relation, "object": obj, "negative": negative,
            "conditions": conditions or [], "text": text}


def validate(proposal):
    if not isinstance(proposal, dict) or set(proposal) != {"operations"}:
        raise ValueError("I couldn't separate the meaning of that message. What fact or question should I focus on?")
    operations = proposal["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 8:
        raise ValueError("Could you split that into a few smaller ideas?")
    for item in operations:
        if not isinstance(item, dict) or set(item) != set(OPERATION["required"]) or item["op"] not in KINDS:
            raise ValueError("I couldn't identify that teaching operation. Could you say what you want me to remember?")
        if any(not isinstance(item[k], str) or len(item[k]) > 1000 for k in ("subject", "relation", "object", "text")):
            raise ValueError("Could you give the things in that message short, explicit names?")
        if type(item["negative"]) is not bool or not isinstance(item["conditions"], list):
            raise ValueError("I couldn't determine the conditions of that statement. Could you clarify them?")
        kind = item["op"]
        required = {"teach_sudoku": ("text",), "sudoku_solve": (), "list_sudoku": (), "sudoku_describe": (), "sudoku_candidates": ("subject", "relation"), "rename_assistant": ("subject",), "separate_person_city": ("subject",), "solve_math": ("text",), "teach_math": ("text", "object"), "rewrite_math": ("text",), "list_math": (), "forget_math": ("text", "object"), "find": ("relation", "object"), "current_date": (), "date_procedure": ("subject", "relation"), "assert": ("subject", "relation", "object"), "retract": ("subject", "relation", "object"),
                    "query": ("subject", "relation", "object"), "subtype": ("subject", "object"),
                    "define": ("subject",), "redefine": ("subject",), "describe": ("subject",),
                    "symmetric": ("relation",), "forget_symmetry": ("relation",),
                    "calculate": ("text",), "count": ("relation",),
                    "define_procedure": ("subject", "text"), "redefine_procedure": ("subject", "text"),
                    "run_procedure": ("subject", "text"), "compose_procedure": ("subject", "relation", "object"),
                    "identify": ("subject",), "name": ("subject", "relation"), 'run_skill': ('subject','text'), 'achieve_goal': ('text',), 'plan_task': ('text',),
                    "world_query": ("subject", "object"), "clarify": ("text",)}[kind]
        if any(not item[key].strip() for key in required):
            raise ValueError("Which person, thing, or property does that refer to?")
        if kind not in {"define", "redefine"} and item["conditions"]:
            raise ValueError("Is that a definition or a statement about a particular thing?")
        if kind not in {"assert", "retract", "query"} and item["negative"]:
            raise ValueError("I can remember explicit negative facts, but not that kind of negative rule yet.")
    if any(item["op"] == "clarify" for item in operations) and len(operations) != 1:
        raise ValueError("Part of that message is unclear. Could you separate its ideas before I change memory?")
    return operations
