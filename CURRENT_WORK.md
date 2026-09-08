# Latest update — general calendar interval and birthday application lessons, 2026-09-07 18:16

User rejected a one-off birthday helper: explicitly wants general days-left
calculation taught, then knowledge that birthdays use that method. DONE/LIVE:
preview session91854,8765; samewarmGemma18769/PID83031. Backup
preview-memory.before-calendar-reasoning-20260907-181543.sqlite3. All existing
assertions/settings preserved, including priorusercasechange speaker=kaan.
Knownbirthfact was born on/Kaan/24th of February2000; no need toreteach it.

New build_calendar_reasoning_curriculum.py generates explicitoptional
curriculum/calendar_reasoning.json;13procedures taughtlive via package API
method (not installedonstartup). Package /tmp/seed-calendar-package.json uses
actualexistingknowledge_describe as knowledge_describe_facts fallback snapshot.
Do NOT snapshot the new dispatcher back into its own fallback on reteaching.

Graphmethods: calendar_is_leap,day_of_year,day_number,days_between,
annual_date_exists,next_annual_date,question_policy,event_countdown;
knowledge_describe_facts,computed_question_policy,knowledge_describe;
language_question_policy,language_interpret. Daynumber uses completedyears365
plusfloor(y/4)-floor(y/100)+floor(y/400), then taught monthlengths/day. All
numeric execution through existing numbergraphbindings. Generalintervalsigned,
sametodayzero. Annualoccurrence findsnextvalidmonth/day includingtoday; skips
nonleapyears foractualFeb29. Birthday-specific policyasks forFeb29observance in
nonleapyear ratherthanchoosingFeb28/March1. Unknown/conflicted/futurebirthfails.
Questionpolicy maps birthdaycountdown→storedbirthdate→nextannualoccurrence→
generaldaysbetween. Explicittemplategrammar dataprefix/suffix forms include
userexactquestion,possessive,my/your; unmatchedformsstilluseGemma.

OnlygenericPython adaptersadded: optional language_interpret beforeexisting
languagefallback; Knowledge.describe renders learnedresulttext; interface
retains methodtrace andusesitsname ininterpretation. No new birthdaysemantic
branch or calendararithmetic inPython runtime. Fullknowhowforthisnewtask is
in graph lessons, bounded questiontemplates areteacher supplied.

Verified isolatedcopy fullchat withNoModel (Gemmacallsraise): user'sexact
question gave Kaan nextbirthday2027-02-24,170days fromlive2026-09-07. General
boundarychecks with independentdatetimeoracle: reversed/zerointerval,yearcross,
2024/2000leap and2100nonleap, birthdaytoday/justpassed. Removingcalendar_days_between
blocksanswer withMissingtaughtprocedure; nofallback. No fulltestsuites.
Livegraphteacherrecord hasanswer+executiontrace. GETstateconnectedTrue,
reasoning_errorNone. READMEdocumentslessonchain,limits,forgetting.

# Latest update — Gemma translation context overflow, 2026-09-07

User hit “llama.cpp did not complete a single translation.” Runtime log showed
3941 prompt tokens in4096-slot and155 generatedtokens ending truncated=1.
Fixed interface.LlamaCppLanguage to pack bounded relevant vocabulary, measure
rendered chat with /apply-template and /tokenize, read capacity via /props,
reserve1200 outputtokens+64margin, drop optionalcontextuntilfit. Preserve full
userinput and identity roles. Keep original fullINSTRUCTIONS normally; new
LOCAL_INSTRUCTIONS compact equivalent onlywhen fullinstructionscannotfit.
If finish_reason=length, retry translation once with1800 reservedoutputtokens;
no partial operations execute. Clear capacity/incomplete/malformedreplyerrors.
SCHEMA operations nowmin1/max8 matchingexistingvalidator. Recentusercontext
excludesCodexteacherreviews/importedlessonpackages. No graphlessons orfacts
modified: this is language-transport contextmanagement, not graphreasoning.

Live directtranslation smoke only, no fullsuites peruserinstruction:
Lina/person+Lina/like/tea translated into2operations at2680prompt+295completion;
Bryan homo sapien query2643prompt+86completion, bothfinishstop with1200reserved.
Earlier compact-only trial dropped a locationclause; retainedfullinstructions
asprimary (existingdirectlocationadapteralsohandles thatcase). Never claim
perfect interpretation. Existing mocked LlamaCppLanguage tests predate the new
props/template/tokenize requests and need fixtureupdates before broader suites.

Restarted onlypreview90808; LIVE session22224 now8765 withsamewarmGemma
18769/PID83031. GETstate connectedTrue/reasoning_errorNone. Browser tab4
statusPreviewTab notrefreshed toprotectanydraft; olderrorwillclear nextsend.
No synthetic teaching insertedlive. Usercanretrywithoutreload. Current exposed
last_translation diagnostics containcounts/reasononly, notmessagecontents.

# Latest update — confirmed-rule labels, 2026-09-07

User thought the two active rules were unanswered questions. Database read
confirmed no waiting input, no proposed rules,2active and6rejected; no new
reviews or knowledge edits needed. graph-ui.js now renders active inclusions
as category arrows, statuses as Confirmed · in use, and explicit unanswered
proposal/confirmed-rule counts. Heading Learned rules and proposals; completed
rules have no Ask me about this rule button. Focus options and graph nodes use
the same labels; Look for patterns retains accurate counts after finishing.
Static files served live; no preview or Gemma restart required. Browser tab4
(statusPreviewTab) was idle/empty draft and refreshed for UI verification.

# Latest update — meaning lessons and authorized teacher reviews, 2026-09-07 17:56

LIVE preview session2779 on8765; warm Gemma untouched18769/PID83031.
Backup preview-memory.before-meaning-20260907-175442.sqlite3. Original954
assertions and all settings preserved. Added3 attributed evidence assertions;
957 total. User explicitly authorized answering all its questions. Completed
all8 current hypothesis reviews through stored learning_reply: 2 active
(gas giant→planet, ice giant→planet),6 rejected. Every hypothesis has
teacher_review with Codex attribution, rationale, sources; 11 codex-teacher
chat records include3 evidence lessons and8 decisions. PendingNone.
NASA planets overview and Neptune facts checked for classification evidence;
Earth negative gasgiant/icegiant explicitly marked teacher inference from
terrestrial classification. Neptune/is/icegiant supplies missing secondwitness.

New build_meaning_curriculum.py/curriculum/meaning.json has7 graph methods:
policy,phrase,fact,assertions,rules,reference_question,retraction_keys.
Explicit bounded modifier/head vocabulary, unknown compounds preserved;
Julia(name) separate fromJulia, no gender inferred forperson. Livepolicy
supplies Mercury(planet)/Mercury(element) mappings using existing source
markers; starterpolicy source_scopes empty. Original rawassertions retained;
normalization used forinference/learning, derivedphrase entailments not
independent examples. Python Knowledge adapters, interfacecontext and Gemma
instructions updated tocall/preservegraphmeanings. Not alllanguage islearned.

12 entries explicitly taughtlive via Session.teach_graph_package:7meaning,
knowledge_rules/rebuild/lookup_response,learning_evidence/inclusion_candidates.
Graph-only optimization: lazyrelationbranches avoidunneededphrasework;
inclusion generator prefilters membershipfacts once beforepair comparisons.
Stage fullcycle failed3M budget beforeoptimization,1.72s successafter. Budget
unchanged. No fulltestsuites peruserinstruction; isolatedexecution verified
name/property/opaquephrase behavior and fullcopyreview beforelivedeployment.
LiveAPI confirms connectedTrue,reasoning_errorNone,8reviewed,pendingNone.

UI: checkboxshowsobserving/rejected/deferredhistory; defaultactive/actionable.
Teacherchatlabels nowCodex·teacher (notYou), assistantlabel usesstoredname.
README describeslimits andprovenance. Browser tab3 was on a cached connection-refused data URL and could not be
controlled. Original notebook tab1 (meaningPreviewTab) reloaded successfully;
HTTPAPIhealthy. open_in_codex queued the preview for the current task.
Temporaryreview script /tmp/seed-review-meaning.py and package
/tmp/seed-meaning-package.json; stageDB /tmp/seed-meaning-stage.sqlite3.
All files untracked; no commits. Do not repeatreview/migration.

# Latest update — general pattern learning, 2026-09-07 17:34

USER: accepted proposed learning loop (notice pattern, propose, check examples,
ask, revise), requested implementation. COMPLETED and LIVE session9327 on8765;
warm Gemma remains18769/PID83031. Backup before update:
preview-memory.before-learning-20260907-173104.sqlite3. Stopped oldpreview37259
only after browser idle. All original assertions, settings/identity andcanvas
explicitly compared and preserved; no synthetic smoke examples inserted live.

New build_learning_curriculum.py authors curriculum/learning.json (12 graph
procedures) merged for NEW notebooks via foundation.curriculum. Existing live DB
explicitly taught package of12 plus revised knowledge_rules. Live initial scan
created8 unconfirmed hypotheses fromexisting observations,2 eligible,0 active.
Gas giant→planet is one proposed rule. No proposal was confirmed onuser's behalf.

Graphs:learning_policy,snapshot,mutual_candidates,inclusion_candidates,evidence,
check,assess,active_rules,discover,cycle,review,reply. Bounded2 candidate families,
2 distinct witnesses required; mutualpair countedonce. Onlyrawassertions are
training examples, neverown deductions. Unknown != negative. Explicitnegations
andcontestedpremises blockadoption. Acceptedrules rechecked againstcurrentraw
assertions everyinference rebuild. Counterexample/loss ofsupport suspendsrule;
needs_review doesnotautomaticallyreactivate evenaftercounterexamplegone.
Teacher yes/no/skip stored, pending rulepayloadmuststillmatch andcurrentevidence
eligible. Fullcorrection handed toordinarylanguageinterface. Rejected/deferred
patterns notautoasked. Askedflagpreventsrepeat aftercancelwait. Askselectionprefers
fewerunknowncases. Generalizationtemplates andcontroldecisions aregraphprograms;
notunrestrictedinductionorAGI. No nativealgorithmforpatterns.

Knowledge.fields/source_signature/_rebuild nowincludehypotheses;knowledge_rules
mergeslearning_active_rules. Activeproofsincludefirst4trainingcases'witnessfacts.
Session aftervalidatedassertionchanges invokeslearning_cycle withchangedtriples,
insidecommittransaction. RawWorkspaceSurface addsentries(namespace), preserving
keys/values withoutassigningmeaning. Fullscan manually viachatLookforpatterns or
UIbutton. Existingpendingquestionsarenotoverwrittenbyautomaticcycle.

UI Graph notebook→Learning & hypotheses includeslist,status,witnesses,evidence
nodeview,reviewbutton,learningprogramlink. FullrecordAPI supports tuple-shaped
hypothesiskeys;partialstate remainscompact withup to4cases/category. 12learning
programs visibleinprocedureeditor. BrowserliveGraphTab(tab3) refreshedwhenidle
andleftongasgiant→planetproposalevidence. No question sent/answered live.

Verification: no fulltestsuites (userpreviouslysaidstoptests). Signaturevalidation,
isolatedactualexecution ofpropose→confirm→unseenpairinference→counterexample→
suspend/remove deduction succeeded. Fullcopyoflive notebookreview took4.22sec;
startup2.75sec. Then live migration+startup/APIhealth confirmedreasoning_errorNone,
8hypotheses,0activelearnedrules,pendingNone. FinalUIproposalbuttons/optionsobserved.
Currentserver9327 healthy. README updated. All files untracked, no commits.

# Latest update — graph lookup behavior, 2026-09-07 17:13

User reported Bryan/is/human plus Homo sapiens/ncbi common name/human did not infer
membership. Requested generalized editable graph lookup rules and permission for
the system to ask for explanations. Last steering: “fuck the tests, just run it”.
LIVE now session15933, preview8765, unchanged warm Gemma18769. Backup:
preview-memory.before-lookup-20260907-170956.sqlite3. No original facts removed.

New authored build_lookup_curriculum.py contributes 6 stored methods: policy,
name_links, name_targets, name_rules, response, reply. Policy declares permitted
concept-name relations (ncbi common name, concept name), explicit spelling variants,
general Horn rules, ask_when_unknown. Name rules infer reversible membership only
from unambiguous uncontested label links, preserving naming and membership evidence.
No Bryan-specific deduction code. Live policy explicitly teaches homo sapien as
spelling variant of homo sapiens; starter policy does not assume that spelling.
Knowledge_rules merges these with existing symmetry/subtype/conjunction rules.
Knowledge_rebuild uses name rules on negatives too; does not apply positive subtype
rules to negatives. Horn_apply appends fixed naming proof witnesses.

Initial live rebuild exceeded 3M budget; fixed taught horn_join to prefilter ground
text fields at tuple positions1/2 as well as relation before structural matching.
No numeric/runtime limit increase. Updated this graph directly after stopping old
preview16467. Live /api/state returns reasoning_errorNone and Bryan/is/human,
Bryan/is/homo sapiens, Bryan/is/homo sapien. Nine new/revised lessons installed by
API; horn_join installed explicitly afterwards. All in graph procedures roots.

interface.py adds optional lookup-response invocation after successful structured
validation, inside commit transaction. Graph decides known response vs unknown
question through raw dialogue port. Stored continuation asks for precise statement
on vague yes/no, stops unresolved, or hands full text back to language interface.
Host only supports generic language_input continuation result; semantic teaching
still requires validated translation. Questions themselves do not add facts.
Graph UI has Lookup behavior overview plus current-policy JSON editor via existing
teach_graph API. Full rule compilation/execution nodes stay editable in procedures.

51 focused tests had finished successfully in36s before user requested stop; no new
tests after that instruction. /tmp/seed-lookup-regression.log. Covers unseen names,
ambiguity, negative/conflict evidence, explicit spellings, forgetting/restart,
general containment composition, asking/no-learning/full-statement handoff, plus
existing structured/foundation/conversation/performance/preview checks. Subsequent
horn_join prefilter change only verified by live startup/health and derived facts;
do not claim tests cover the final prefilter change. No tests running.

# Latest update — teaching speed, 2026-09-07 16:58

User complained adding data was very slow, then explicitly agreed not to send all
data continuously. Fixed and deployed; latest live session8824 runspreview.py on
8765, Gemma remains warm18769. Priorprocess86417 was stopped withSIGINT only
after its active teaching finished. Livebackupbeforeteaching-speed-20260907-165501
preserved953 assertions,266prior messages,all155procedures except intentional
horn_join replacement,settings,boardandall existingderivedfacts/proofwitnesses.

Changes:graph_runtime shares validatedData literals within a run and uses bounded
LRU shapevalidationcache; primitive scalar validation no longer re-enters recursive
Data copying. Allnumeric methods stillgraphlessons/no nativefallback.
GraphStore.clone_namespaces usesSQLite pagebackup outsideopenwritetransactions,
keepsrequestedroots only; transactioncase keepsoldencodecopy.
Knowledge.__deepcopy__ reusesmaterializedresults with exactsource-root checks;
adopt uses directstorageviews andskipsunchangedroots so noextra inference from
derivedgetters midcommit. One newassertion doesonerebuild(previouslythree).
Taught horn_join nowfiltersconstantrelation candidates beforepattern_match,
retains all candidates for variablerelations; authoredcurriculumupdatedandonly
thatlessonwasretaughtlive. No native reasoninghelper.

Previewstate projectslarge records (6000chartext,500chartracepreviews);fullrecords
remain at/api/record?namespace=...&key=JSON. Browserusesstate_version deltas:
unchangedsectionsomitted,language_patchonlychangedrows;expiredversionsfullreset.
8 recentviewsheldinmemory;notknowledgecache. Initialfetchonlyonce (was4times).
Browsermergespatchbeforeallrenderwrappers;large answersandtraceeventslinktofull
storedrecord. Fullstate clients remain supported byomittingstate_version.

Measurements froma951assertioncopy:/tmp/seed-teaching-baseline.log and
/tmp/seed-teaching-optimized.log. SamecProfileteaching175.24s→2.81s;
unprofiledoptimizednewfact1.70s (excludesGemmaandUI). Oldstate31,800,602bytes;
teachingdelta91,707bytes. Livefinalinitialstate1,196,084bytes. Do not equate
these graph-stage timings with fullGemma language latency.
65targetedtests passed:46in/tmp/seed-speed-tests.log plus19in
/tmp/seed-storage-speed-tests.log. Finaltexttruncation5previewtests passedagain
/tmp/seed-preview-final-tests.log. Testcoveragecloneisolation/rollback,
singlerebuild,variable/sharedbindings,retraction,forgetting,numbercachebounds,
completeevidenceAPI,delta fallback/payloadbehavior. Fixed2oldGraphStoretests to
explicitlypassteachednumericlibrary (productionstillfailswhenabsent).
READMEupdated. Allfilesuntracked,preserveno commits.

BrowserliveGraphTabtab3 validagain viaopen_in_codex(tabIdprovider2). Useractively
testingBryan livesinDordrecht;do notoverwriteinputorinterruptrequests.
Bothnewactivitytextandfullevidencelinksobserved. APIs200,reasoning_errorNone.

# Earlier state — 2026-09-07 16:35 (archived)

Live preview is serving on 127.0.0.1:8765, with Gemma kept warm at18769.
The Wikipedia/reference-import task restarted it concurrently as PID86417,
`python3 -u preview.py --base-url http://127.0.0.1:18769 --port 8765`.
Our prior session71894 was stopped. Our restart34242 exited on a database lock
because the other preview was already loading the same DB. Do not kill its
healthy process or start another. GET / returned200 and /api/state verified
155 procedures,952 facts,reasoning_error=None,dialogue installed,waiting=None.
The user is actively using tab3 ("Tell me about Turkey" was in flight); do not
overwrite their draft, send a live tutoring test, or clear their interaction.

Arithmetic replacement IS LIVE:37 supplied number graphs under the same active
knowledge.procedures roots. Numeric operators and numeric parsing bind to graph
methods; no native operation fallback. Symbol/collection primitives, Fraction
transport/validation, formatting, expression parsing, UI routing and drivers
remain code. Gemma's pretrained linguistic knowledge is outside the graph.
Never claim literally all knowledge/behavior or AGI; the math scope is bounded
and the programs/tables were authored by teachers, not independently discovered.

Conversation IS IMPLEMENTED AND TAUGHT LIVE:build_conversation_curriculum.py
authors11 lessons in curriculum/conversation.json. RawDialogueSurface offers
say/ask/wait, persisting continuation+state underinteraction.state. Genericattempt
node permits taught failure handling without rollback or budgetreset. Session.chat
delivers the next reply to the stored continuation. Teach me algebra starts a
3-part linear-equation course; currentalgebra_solve executes examples/exercises,
number_parse/equal check answers. Graphsthemselves choose hints/retry/advance/stop
and ask for missingmathlessons. Numeric dependencies removed fromtutor control
so even forgettinguint_add can lead to a question. Explicitreteaching command:
Teach conversation methods. Course explanations are teacher-authored; no general
automatic pedagogy or autonomous program synthesis is claimed.

Live conversation migration backup:
preview-memory.before-conversation-20260907-163016.sqlite3
Verified preservation of951 existing assertions,243 prior messages,144 prior
procedures,session settings andenvironment board. Another task had imported
reference knowledge; preserveknowledge-expansion/ andwikipedia-starter/.

Graph UI live:factrelationships/proceduredependency/recordedtrace andwaitingmode.
Newwaitingbanner supports explicitcancel. PreviousSVG factsandprogram navigation
visuallyverified. NewwaitingUI loadedinlivebrowser. Browserruntimebrowser2:
liveGraphTab=tab3(currentrealuseractivity);graphPreviewTab=tab2(nowerrorpage),
tab1 also app. Don't navigateerrorpage(dataURLblocked); originaltab2wascreated
bythis task earlier. Codex open_in_codex withtabId2 actuallycreatedtab3; beware.
Browser/frontendskills alreadyread; no rebootstrapneeded. UseNodeREPLtool.

Tests:33 passed in123.793s in/tmp/seed-release-checks.log:
test_conversation,test_numbers,test_computation,test_foundations,test_preview.
Conversation6 passed independently too. Includesunseenexercise,wronganswer,
help,finish,noGemma,removedmathask,restartresume,forgottencontinuation andattempt.
Earlier numbers+calendar12 passed. Fullsuite76788 was interrupted after12min,
no failures emitted; stackshowedtest_structured setup, so DONOT claimfullsuitepass.
Structured+calendar run session76265 finished:22 tests passed in113.717s,
/tmp/seed-chat-checks.log. Total55 focused tests passed. No tests running.
SkillSystem preflight nowmemoizes dependency heights toavoid repeatedDAGwalks
while preservingcycle/missing/depthchecks;33testsaboveincludeit.
README/ARCHITECTURE updatedfortaughtarithmetic,tutor,graphUIandpreciselimits.

Finalresponse stillowed:answeruser's repeatedallmath/allknowhowquestionwith
scopedtruth,mention howtotryteacher andgraphnodes. Avoidsweepingyes. LiveUI
chat-testnotperformedbecauseuserwasactivelyusingit;unit+APIverified.

# Archived implementation notes (earlier in this turn)

User objective: unify the teachable system in a graph without hidden domain algorithms. Do not claim AGI or unique research. User keeps steering in conversation; preserve all requests. NO subagents permitted by latest developer. No goal tools. Keep commentary under 60 sec apart. No need to ask permission for authorized work. Preserve live DB/history/board.

## Live

Preview at http://127.0.0.1:8765 now running **session 62204**, launched python3 preview.py --base-url http://127.0.0.1:18769 --port 8765 (approved prefix). Gemma warm at18769; leave it running. Old preview78421 stopped.

Live SQLite `preview-memory.graph.sqlite3` was migrated to foundation reasoning on Sept7 15:46. Backup `preview-memory.before-foundations-20260907-154642.sqlite3`. 106 procedures,23 facts,162 messages, identity+entirehistory+board preserved. New live foundation includes inference/rewrite/world/planner/calendar/workspace programs and Sudoku read/query/goal/check contract. **LIVE STILL RUNS NATIVE ARITHMETIC**: replacement numbers were written AFTER restart and not yet taught live. Do not claim replacement complete until tested/taught/restarted. Current source changes can affect static UI immediately; graph-ui.js route is new, needs restart. Stage DB copy `/tmp/seed-migration-check-1788788321.sqlite3` earlier tested migration; not current authoritative.

Browser skill already read fully; browser2 persistent binding, graphPreviewTab=tab2; both tabs now valid URLs8765. Use tools.mcp__node_repl__js through functions.exec. Documentation was read earlier; do not bootstrap/re-read. browser2.tabs.list/playwright.domSnapshot; inspect before actions, don't overwrite drafts. frontend-design skill read and announced; incremental existing paper/green UI. Tools only via functions.exec; inspect ALL_TOOLS fornode tool ifneeded.

## Implemented this long turn, before numeric change

- `graph_store.py`: authoritative SQLite typednodes/orderededges/roots (no JSONblob authority). GraphMap andGraphSequence live trackedviews,transactions,stalehandlespreventresurrection. Existing Session.load readsrootsneverhistory/sourcecurricula.
- `build_foundation_curriculum.py`, `build_world_curriculum.py`, `build_rewrite_curriculum.py`, `build_date_curriculum.py`, `build_memory_curriculum.py`, `build_skill_curriculum.py` author static curriculum/foundation.json. App doesn't import builders.
- `foundation.py`: new notebooks explicitly supplied startercurriculum. Existing DB never reloads forgottenmethods. `run` invokes onlystoredname,3M budget. `data` serializes tuples/Fractions tointerfaceData.
- Foundation graphs: pattern_match/substitution/treewalk, Hornjoin/closure, knowledgeinference/query/find/describe/explain, subtypeclosure,symmetry, worldhypothesis/search/revise, mathrewrite policy/iteration, counting/memorycorrection, calendarparse/monthvocabulary/fieldbinding/leapyears, clock_calendar taughtinterfacebinding `current_date`, plan_search BFS/tag contracts,plan_execute dynamicinvoke, workspace andcanvas usage.
- `Knowledge` uses these graphs; preserves raw assertions and removes stale deductions when methodsmissing. Methods readglobal knowledge.procedures. Source signaturesincludeprogramroots; deleting/editingmethodinvalidatesderivedproofs. `knowledge.executions` retains last inputs/results/trace/program-root IDs bymethod. Stagingadopt now rebindsTaughtCategory tolivecoreinsteadclosedclonestore. NativelegacyMeaningSystem still existsforCLI, butpreviewusesKnowledge.
- `Explorer` world inference in graphs; initialfeatures/simulator/environmentremainhost; record episodefactformattingnative (representation only). Lastworld methodresults inworld.executions.
- `math_lessons` match/rewrite methodstaughtgraphs,syntax/renderadapters remain. `date_tools` clockrawnative; parse_date takeslibrary andinvokescalendar_parse; agefindingbindingorderingusesstoredgraphs. ClockDatequeryinvokesclock_observe. Birthdate correction comes frommemory_policy functionalrelationlist +memory_superseded graph inside stagedassert (beforeassert). Countingselection andsequence graphbased.
- Sudoku20curriculum graphs all reasoning/reading/input/checking, no constraints/candidatevalues fromsensor. New `sudoku_observe_read`,`sudoku_query_candidates`,`sudoku_goal_check` andskillcontractonsudoku_observe_solve requires[sudoku_canvas] provides[filled_sudoku_canvas]. Old17 retained;livechangedonlytopentrymetadata+3newgraphs and62foundations.
- `skill_system.py`: genericrun,goal records,contractcatalog,preflightsentireselectedplanbeforeeffects,dynamicinvoke; `verified` onlyexplicitBoolchecker,otherwiseexecuted_unverified. Failingchecks/unknownplans notsuccess. WorkspaceSurface rawread/write/keys/delete; readonlysensorhistory. Genericrunners onlyrawcanvas/workspace/clock, cannotaccesslegacyrichSudoku adapter. Failedruns keepactualtraces/effects. Numericresults serializedexact (integerorcanonicalfractionstring).
- `sensory.js` panel generalized toallproceduretypes andgoal controls; load/teach temperature example,goalJSON. APIs teach_graph_package/run_skill/achieve_goal inpreview. `examples/temperature.skills.json`3teachergraphs demonstratesnewdomainconvert/assess/check contracts;86F->30C,warmtrue,thresholdrevisioncausescheckfail,deletionlosesplan.
- `graph_runtime.py` genericDataops addedkind/keys/characters/split/join/has_key,as_numbers,dynamicinvoke; bounds64deep100kvaluescontainer2000. Toolopcodecurrent_date resolvesstoredinterfacebindingratherthancodeddateparsing. Observe/act recordattributed evidence. Emits keepstructured evidence. Errorscarrygraph_trace. DefaultclockonlyHub whennosensors (testswithoutcanvasnowUnknownperceptionsource).
- README/ARCHITECTURE updated forabove (now stale re built-inarithmetic because numericreplacementpending).

## Newest steering, all outstanding work

1. User wants node visualization of facts/connections, procedures and thinking traces.
2. User explicitly: remove built-in numeric arithmetic, make it all taught node programs. First suggested unaryexample wasn't enough; now REPLACING numeric opcode implementation itself. Need verify forget=>failsnoPythonfallback.
3. User wants ask/wait/choose/continue behaviors tobegraph nodes andlearned policies. OriginallysaidEventually; subsequentlyexplicitaskquestion/waitevent shouldbe node. Not implemented. Need an honest event-driven taughtbehaviorloop; rawhost handlesdisplay/delivery only.
4. Latestuser: "if I ask explain something it knows, like teach me algebra, it can't". We explained storedsolverisn'tpedagogicalprocedure; promised teachingbehaviorusingstoredalgebraknowledge+question/waitloop, notGemmafabrication. Need implement tutor with authoredcourse/teachingpolicy/observedcalculator outputs, questions,resumablestate inDB.
5. No claims ofhumanunderstanding. Distinguish directteaching/programming, inference,andboundedworldinduction(actualML).

## Numeric replacement in WORKING COPY (not live yet)

`build_number_curriculum.py` +generated`curriculum/numbers.json`~316KB. GraphauthorclassN extendsG but usesNO Numberops. UsesData text/list/lookup/structuralequality/control. Explicittaughtdecimaldigit add/subtract/multiplycarrytables, comparetable,glyph->unitquantitymapping. Generated graphalgorithms:
- quantity_zero/successor/add/count/symbol
- uint_trim, add/subtract withcarryborrow, compare, digit_product, multiply bypartialproducts, division_digit repeatedsub,divmod longdivision,gcd Euclid
- rational_read (canonicaltext->sign,n,d), text, reduce
- number_add/subtract/multiply/divide/negate/less/equal/is_integer/floor/numerator/denominator/power (repeatedsquaring integerabs<=100)
- number_count_units loops successor; number_count firstmapsdata toidenticalunitmarks so genericmemoization reusescounts forcollections ofsamecardinality
- number_range,number_indices
All numericgraphs `memoize:True`, `interface` fieldbindingoperationname (count binds ['size','length']). Internalhelpers notbound.

Foundation.curriculum NOW MERGES numbers.json +foundation.json =94entries. Newnotebooks thereforeteachnumbers. ExistingliveDBnotyetcontainsnumbers. NeedMIGRATE numeric package DIRECTLY to GraphStore BEFORE Session.load because newruntimepreflightsmathbindings duringload (canfail ifoldDBnoarithmetic). Backup firststoppreview. Explicitteachingtransactionsgraphroots thenSessionload/teachhistory; don'tautofillstartup.

Runtime NOW has NUMERIC_OPERATIONS={add,subtract,multiply,divide,power,negate,less,equal,is_integer,floor,numerator,denominator,size,length,range,indices}. Preflight resolvesinterfacebinding fornumericops andrecurses into taughtgraphs. `numeric` serializesFraction args tocanonicaltext,invokesboundgraph, converts returnedtext toFraction transport; Boolchecked; indicesstringpositions->ints;range->ListNumber. Nativefraction arithmetic branches REMOVED. size/indices routed too. Pure per-execution memoization of teacheroptedgraphmethods; purityrejectsI/O/tool/invoke/emit andchecksdependencyclosure inclnumericbindings. Cache20k results, currentlibrarysnapshot; nomemo acrossrevision. Both staticcall/dynamicinvoke useprogram helper. Default execute_graph limit changed1000->100000 afternumeric expansion. foundation/run3M retained. `procedures.define` got visitedset forstaticacyclicchecktoavoidhighsharedDAGoverhead.

Potential remaining Numeric concerns:
- `bounded_number` and normalize stillFractionparseinputs; hostFractionisrepresentation/validation andoutputformattingstillnative. To fullyteachsymbols/decimalgrammar canadd number_parse graph androute literal/input/as_number executionthroughit. Validation maystillcheckformats butnotcalculateanswers. Avoidpretending thisalreadydone.
- Native`number_text` formats decimalsusinghostarithmetic; explanationboundary notsolver but userstrictcouldwanttaughtformat. Couldusecanonicalfractionstr forData andgraphformatforlanguage later.
- Numericpreflight missingbinding exceptions notyethandled likeMissingtaughtprocedure inKnowledge/Explorer (fixpredicate).
- SkillSystem.preflight justextendedNumericops butneedtests.
- Graph pure memo cachedargjson `default=str`,typedData usuallyvalid. Mustnotcacheeffectfulgraphs; tests neededrevisionforgetcache.
- Rootdependencydepth20 withrationalmethods mightgetexceeded inverydeepalgebra;benchmarks belowpassed.
- `uint_digit_product` carryflushtable multiplicationat a0 withb arbitrary carries okay.
- Power alwayssquaresbaseevenlaststep,resultsizebounded; intermediatecanhitboundbiggerthanfinal butgenericresourcelimitfair.
- Some standalone tests previouslycall execute_graph withoutlibrary. They nowmustexplicitlyteach/passarithmetic fixture. DO NOT addimplicitfallbackinproduction whenlibraryempty. Addtestfixturehelper oradjusttestsintentionally. Partiallibrary testsneedmergeexplicitnumberlibrary whereappropriate, butdeletion/ablationtestsmustnotrestoremissingmethods. Algebraablationiteratesalgebrapackageonlyalreadyupdated;SudokuablationcurriculumonlyskipnewBoolcheckercoveredgenericgoaltest.

Numeric smoke results (allusingtaughtgraphs): uint_add999+6=1005,multiply123*456=56088,longdiv113379904/22=5153632r0,rationals1/3+1/6=1/2,-7/3 floor=-3,power(-2/3)^3=-8/27. NewSession~5.2sec startupbeforecount/reduceoptimization. Afteropt fullSudoku default~4.3sec correct;5x=20~0.32sec x4;(x-22)^6~2.48sec root22mult6. Nativearithremovedinworkingcopy duringthesetests.

A `test_date_tools.DateToolTests -q` execution **session34201** wasstartedbefore defaultbudgetincrease; pollmayfailold1000bound. Needrerunafterfix. Nootherexecscriptsknowinglyrunning exceptlivepreview62204.

## Visualization just authored, not verified/live route

New `graph-ui.js`, linkedafter sensory.js inpreview.html; preview.py servesrouteonlyafterrestart. Paper/greenSVGcomponentaftermain:
- Facts view focusesanentity/concept, incoming+outgoingrelationshiplabeledarrows, clickneighborsnavigatewithoutpersonnode.
- Procedure view displays typedgraphinstructionDAGlayout withinputedges;greenlinkedcall/numeric/tool nodesopenboundprocedure. Distinguishesstoredstructurefromexecutedbranches.
- Runs view chronologicalrecordedtraceevents,labelsemits/stepresults, clickdetails. Explicittracesomitintermediates,captionstateschronology notdataflow.
- Focusselectmode/back, actualrawgraphID API link,scrolllargegraphs,keyboardaccessibleSVGnodes.
- wrapper render collectsstate.language traces,skillruns,goals; preview.state adds last10runs. Manytraceevents mayhugeSVGwidth buthorizontal scroll. Excerptnoautomaticcap yet.
- `.graph-workspace` stylesappendedsensory.css.
Needbrowserread/screenshot/interactverifyandfixissues. graphState.speaker isn'tinstate so defaultfocusalphabetical (chooseKaan fallback viaassistant??optionalfix). Userdraftsafe.

## Tests before numeric replacement

Earlierfullsuite116testsfail2 ONLY stale expectation/laterfileeditchanges whiletestwasrunning. Fixed source assertions:
- no-sensors canvasread nowUnknownperceptionsource (notold sensoryaccessmsg).
- Sudoku20newBoolchecker excludedfromsolverdependencyloop; testedthroughgenericgoalfailurebeforeeffects.
- Persistence testsinterface/playground assertionsnowINSIDEtempdircontext becausegraphinvocationspersisttraces; DBdeletedoutsidewithcausedreadonlywriteerror.
- Earliernewscopefixturesalgebradependencylooponlyalgebrapackage; Sudokuonlysudoku; Datadepthtest65>64.
Focused13testsablation+sensory+foundations passed justbefore numericchange. Newfoundationsfile11tests (numbersnapshot meanscurrenttestcount117). Includes incominginference/retraction ablation,calendarvocabrevision,forgetclockbeforeI/O, count/correctionpolicy, noresurrection restart, newtemperaturecomposition/checkfail/delete,unverifiedcontracts,workspace read/revise/forget,rawcanvasscope,exactFractionUIserialization,goalSudoku actualboardcheck/deletion, staticmissingdependencybeforeeffects.
Neednew numeric propertytests with PythonFraction referenceONLYTESTS, verify zero/sign/fractions/negativepowers/limits/forget/revise/restart/noNumberops innumbercurriculum. Fullsuiteafterproperfixtureupdate, notblindweakening.

## Further implementation plan (not alreadydone)

Complete numeric tests/integration +teachlive afterbackup. Build rawDialogSurface (ask/wait/sayinputdelivery) +taughtresume policies in separatecurriculum toavoidfoundation94limit100 (increasegenericpackagecapifjustified). Persist pending{question,resume,state,id}; Session.chat deliversnewinput tostoredresumegraph whenpending, nohardcodedteachinglogic. Teachergraph canreadcourse fromworkspace, executeknownalgebraexamplemethod, askquiz, compareanswerusingtaughtarithmetic,wait/retry/advancelessons. Coursecontentauthoreddata, includeprovenance +descriptions notLLManswers. Route “teach me algebra” tostoredteacherstart throughsyntaxadapter. Exposependingquestion/stateinUI andnodeview. Genericplannerwhenstuck couldexecuteauthor-definedonstucklesson thatasksandwaits ratherthannativefallback, butdon'tpromisefullself-directedlearningalgorithm.

Newscopeislarge; persistasonechainacrosscompaction. Do notfinishwithonlyplanorstatuswhenimplementationstillauthorized. Finalhonestlimits,whatlive,testresults,andhowtotry. Do notclaimallsoftwarecodegoneorAGI.
# Latest update — identity, taught word forms, and inspector marker, 2026-09-07

User reported Nex did not connect its own name to itself and human/humans were
separate; explicitly accepts teaching their link. DONE/LIVE: 13 lessons from
build_identity_curriculum.py, stored curriculum/identity.json, installed through
the existing teach_graph_package API. Backup:
preview-memory.before-identity-20260907-190642.sqlite3. Original assertions and
session settings compared and preserved. No storage format/compression changes:
the earlier compact-layout investigation was read-only, per user instruction.

Graph policies resolve current speaker/addressee in participant fields, normalize
created/creator of to created by with reversed endpoints, answer taught creation
question forms, and include stored facts in self descriptions. No Kaan/Nex names
in the teaching package. meaning_reference_policy teaches human/humans labels for
the same concept, including relationship endpoints. No suffix heuristic or
automatic universal quantification. Unknown/ambiguous forms remain unchanged.
Existing meaning and calendar language methods preserved under *_before_identity;
builder safely preserves original methods on repeated teaching. Host changes:
interface.py invokes taught reference/self-description methods and fixes the old
object-pronoun fallback that still used Seed; knowledge.entity invokes taught
meaning_reference. New notebooks are not implicitly supplied this extra package.

Isolated real execution (/tmp/seed-identity-check.py) verified both self queries,
human/humans/Homo sapien membership, concept-target links, preserved birthday
countdown, a different speaker/assistant pair, active/passive contradictions,
unknown creator, and missing-lesson failure. No full test suites run. Live HTTP
chat confirmed Who created you/Nex => Nex created by Kaan and Who are you includes
the learned facts. Preview restarted as exec session96783 on8765; warm Gemma
18769/PID83031 untouched. Live reasoning_error None.

Latest steering: highlight Nex in graph inspector. graph-ui.js and sensory.css
now mark fact-view nodes matching current assistant_name in amber with accessible
This assistant labels, add a direct identity focus button, and include settings
provenance in selected-node evidence. Marker follows the configured name and
applies to incoming/outgoing/central nodes, not executable nodes with similar names.
UI verified in the working browser tab1 (identityTab): current-name focus option,
amber This assistant node, direct focus button and identity evidence selection.
Server HTTP200, connectedTrue and reasoning_error None. User asked to boot it;
open_in_codex requested the local preview (queued in current task). Browser
binding statusPreviewTab (tab4) is now
on a cached connection-error data URL blocked by browser policy; HTTP preview is
healthy. Use another valid tab to inspect; avoid printing huge data URL errors.
# Latest update — linked natural-language commands, 2026-09-07 19:38

User accepted fixing natural-language sequences with result references. Implemented
and explicitly taught 26 graph lessons in curriculum/sequences.json, authored by
build_sequence_curriculum.py and build_sequence_language.py. Backup before teaching:
preview-memory.before-sequences-20260907-193749.sqlite3. Live preview restarted as
session24384 on8765, existing warm Gemma18769/PID83031 preserved. Live HTTP checks
passed: plain chat5→10→13 in1.76s and8→24→20→4 in1.24s, connectedTrue,
reasoning_errorNone, waitingNone. Working browser tab1 (identityTab) refreshed
after checking the chat draft was empty. No storage layout changes or knowledge-fact migrations.

sequences.py is a transport/validation/recording adapter. interface.py routes
recognized linked requests and continuation replies; LlamaCppLanguage now shares
its bounded _translate_json transport with a separate linked-step schema. Taught
sequence_detect recognizes then/afterwards and explicit sequence prefixes while
leaving if/then teaching and create/define procedure paths alone. sequence_catalog
offers public Number procedures, skill contracts and sequence_input declarations.

Graph sequence_interpret and sequence_clause_policy compile common arithmetic,
date and “then run NAME on that” forms without Gemma. Any unmatched clause sends
the WHOLE request to the Gemma plan translator, never a partial command. Gemma
still has variable reliability for unfamiliar phrasing: early checks produced
incorrect argument wrappers and spurious clarification, motivating the taught
clause compiler. Do not claim arbitrary language is perfectly understood.

Plan steps have id/method/argument; nested {var:earlier_id} uses existing taught
tree_nodes/pattern_substitute. sequence_prepare rejects duplicate/forward/unknown
references and unavailable methods before any action; host preflights all static
dependencies. sequence_execute preserves actual per-step inputs/results, stops at
the first runtime failure and does not retry completed effects. skills.sequences
and experience.language retain plan, status, trace, results and program root IDs.
preview.record allows direct reading of skills.sequences; conversation execution
traces already appear in the graph inspector. Structured final values use ordinary
JSON presentation, with no calculations in the host.

Missing initial “that” asks through sequence_question and dialogue_ask; sequence_reply
retains the original request and accepts a numeric starting value through a taught
reader, or sends other clarification to the model with the original. Stop/cancel
clears an unstarted request. Max8 steps. Conditionals/loops in arbitrary English
are not supported; compatible taught methods may encapsulate that behavior.

Isolated actual checks passed (no full suites): /tmp/seed-sequence-smoke.py gave
5→10→13, birthday→today→next occurrence→170 days, missing “that”→starting7→14,
identity unaffected. /tmp/seed-sequence-boundaries.py checked a new skill, nested
references, forward-ref rejection before a visible effect, cancel, divide-by-zero
retaining the completed step and preventing the later effect, and human/humans.
Final extra check taught fresh_offset (Number→Number) and used ordinary chat to
produce2→9 with a NoModel translator; date→report displayed the actual date array.
Live smoke passed as described above. README documents supported forms and limits.

# Latest update — assistant rename continuity, 2026-09-07 20:26

DONE/LIVE. User renamed Nex to Sam Agiman, but only session.settings changed;
facts still referenced Nex. “Update all Nex references to Sam Agiman” was
mistranslated as retracting Nex/created by/Kaan (history index425).
New build_rename_curriculum.py + curriculum/rename.json explicitly taught six
procedures: meaning_rename_reference, identity_text_range, identity_rename_policy,
identity_rename_interpret, language_interpret_before_rename, language_interpret.
The current language dispatcher was snapshotted, preserving all prior methods.

Stored rename behavior produces a revised meaning_reference_policy literal
graph. One entity-name row retains identity=nex and aliases nex/sam agiman;
canonical=Sam Agiman. Repeated renames retain prior aliases. Existing meaning_fact
normalizes both endpoints and negatives; raw assertions/history stay unchanged.
Known name/concept collisions are refused. Host Knowledge.rename_entity only
validates/persists the resulting graph and rebuilds; interface stages it with the
new assistant display setting. No display-only fallback if lesson is forgotten.
Describe also resolves historical aliases for self-description and summaries.
graph-ui.js follows the selected assistant through a rename.

Backup: preview-memory.before-rename-20260907-202443.sqlite3. Live repair retained
all original assertions/settings, restored exactly one accidentally retracted
assertion from preview-memory.before-sequences-20260907-193749.sqlite3 with its
original source “You are created by Kaan”. A codex-teacher repair record documents
record425 and the backup; current965 assertions. No synthetic example facts live.

Focused isolated verification: repeated renames, historical-name lookup,
incoming references, negatives, collision rejection, invalid-batch rollback,
and no Gemma fallback for taught rename forms. Final checks used current runtime
without a shim. Live questions Who are you / Who created you / Who created Nex
all return Sam Agiman with existing facts and creator Kaan. Browser tab1 refreshed
with empty draft, assistant button focused, connected true/reasoning_error null.
Preview PID78497, exec session10918,8765; Gemma83031 stays warm18769.

Concurrent task Assess Wikipedia knowledge training (01a07c2b-33fb-7bc3-8d3c-4fd4d23d338c)
is modifying runtime caching/source curriculum in this workspace. Coordinated
restart: they installed29 source lessons via API; preserved. They fixed shared
node preparation after I found KeyError:0 (deepcopy preserves aliasing). I moved
execute_graph's return outside the optional cache if, which otherwise returned
None with no cache. Runtime/source changes belong to that task, not rename
semantics. They received healthy PID and will only perform JS/read checks next.
Useful scripts /tmp/seed-rename-install.py (ALREADY APPLIED; do not repeat),
/tmp/seed-rename-check.py, /tmp/seed-rename-final-check.py.

# Latest update — functional states, background routines, dark assistant UI

DONE/LIVE 2026-09-07 ~21:09. User requested persistent graph emotions/sympathy,
background subroutines, then a dark tabbed assistant UI with Seed/toy world
removed, sticky chat, newest-message default, readable graph edges, and original
amber assistant highlighting preserved. All implemented. Preview PID18821, exec
session26013,8765, Gemma18769 unchanged. Another task (Assess Wikipedia knowledge
training) now has permission to teach Vienna/person scoping and restart later;
check current PID before any future restart. They are preserving these changes.

New build_affect_curriculum.py (11 lessons), build_background_curriculum.py
(5+1 interpreter), curriculum/affect.json and background.json. Explicitly installed
17 lessons offline after backup preview-memory.before-behavior-20260907-205640.sqlite3.
Existing assertions and assistant name preserved. session.behavior binds
behavior_interpret, affect_observe_turn, background_tick. No startup reseeding.

skills.affect/current stores values curiosity/uncertainty/satisfaction/sympathy
0..100, revision, last cause and20-event history. State deltas/classification/
bounded arithmetic/question decision are graph rules. Sympathy matches explicit
phrases (I feel sad, No advice, etc), offers talk vs practical help, records state
and schedules one3minute gentle follow-up; follow-up stays quiet if superseded
by another meaningful event. Does NOT prove or claim subjective experience.
How are you feeling? reads the state without rewarding itself. Unknown wording
still uses language layer. behavior.py is generic event delivery; chat wrapper
calls old _chat, then graph after-turn observer. Errors preserve primary outcomes
and record session.behavior/last_error rather than changing a successful answer.

Background graph scheduling writes skills.subroutines, clock observation now
adds unix_seconds. Generic preview daemon delivers ticks every5s under app.lock
(nonblocking acquisition). Graph executes at most1due routine/tick, defers while
interaction waiting, stores completed/failed status, repeats only when requested.
Deadline persists across restart; server required to deliver. Chat syntax:
Remind me in30seconds toTEXT (with spaces). General background_schedule accepts
id/method/argument/delay_seconds/repeat_seconds; repeat0=once. Routines UI form
and cancel buttons. No external notifications. Verified isolated sympathy60
after2explicit examples, identity recall, reminder once; final version queued
follow-up. Live state report successful; labeled Setup check reminder delivered
once, background_error null. User subsequently added 'be nice to you' reminder;
do not delete/alter it. Isolated examples were never asserted live.

New workspace-ui.js/css dark sidebar tabs: Conversation, Memory, Internal state,
Routines, Tools(Programming/Sudoku), Teach & inspect. Legacy DOM moved, toy-world
notebook removed after extracting authoring controls; branding dynamic name.
preview.html render shows last50 messages with load older, preserves read position,
newest default; composer anchored and message scroll separate. Graph source
handlers retained. GET/api/state?since now supports incremental polling, every5s
while tabvisible and no active request; drafts not cleared. Graph initial fetch
callback now resolves latest render wrapper. All light-editor selectors overridden
with dark backgrounds/light text; edge labels dark halo fixes white-stroke issue.
Assistant graphnode amber restored; curiosity gold, uncertainty blue, satisfaction
green, sympathy rose. Browser screenshots and computed colors verified, composer
insideviewport. Browser binding identityTab (tab1) refreshed and used. Other tabs
may need refresh. Full skills/procedure inspection remains available.

Important files: behavior.py, interface.py chat wrapper, sensors.py clock, preview.py
thread/state/static/query route, workspace-ui.*, preview.html, graph-ui.js.
/tmp/install-behavior.py ALREADY APPLIED; do not repeat. /tmp/affect-check.py isolated.
No full test suites (user preference).

## Rendered browser interface (2026-09-07)
- Installed 23 web graph lessons from `build_web_curriculum.py`; browser navigation, selectors, subtree reading, favorites and example report interpretation are graph procedures.
- `rendered_web_surface.py` + `browser_engine.cjs` provide fixed controls to isolated Chromium. Website JavaScript executes normally. No arbitrary JavaScript execution command is exposed to the agent. DOM observations and screenshot correspond to the rendered main document; iframe/shadow DOM traversal is not implemented.
- Web tab exposes screenshot clicks, typing, keys, scroll, DOM inspection, navigation and persistent graph favorites. Browser profile is ephemeral; popups/downloads/service workers/websockets are restricted.
- Generic JS interaction fixture passed. Graph weather reader read public wttr.in London HTML successfully using stored selectors. The starter reader supports that layout only; other layouts require teaching. The London favorite is an example, not the user's weather default. No personal location is automatically transmitted.
- Backup saved as `preview-memory.before-web-*.sqlite3`. Existing live database loaded without reseeding. Old `web_surface.py` is the unused static prototype.

## Dynamic dashboard and bilingual starting grammar (2026-09-07)
- Dashboard live: cards, stored method/input, intervals, deadlines, pause/resume/remove, last good result and errors are `skills.dashboard` records. Sixteen taught graph procedures own scheduling/refresh/weather recipe and dispatch; the host runs the existing generic timer. Background cards do not emit repeated chat messages. First due card is selected by deadline; refresh is deferred during pending dialogue. Failures retain successful content and back off to at least five minutes.
- Dashboard UI supports generic text/value/list outputs, custom procedure inputs and explicit refresh controls. Local date and user-added weather cards verified live. English and Dutch dashboard examples are in the taught language/behavior programs.
- Bilingual starting grammar: fourteen graph programs plus sentence frames in `skills.language_patterns` and mappings in `skills.language_words`. Pure matching/normalization/operation construction is graph-executed; Python only dispatches the result to existing semantic operations. This is bounded template grammar, not unrestricted English/Dutch understanding. Unknown qualifiers and unresolved third-person pronouns decline matching; hybrid retains Gemma fallback.
- `session.language.mode` defaults to hybrid. Optional symbolic mode blocks model fallback, including sequence translators. Existing legacy parsers/host semantic execution remain; this is not a claim that every language function in the app is graph-based.
- Teach & inspect contains mode, sentence frame and vocabulary teaching forms. Replies still often use English. Words are aliases, not automatically inferred definitions.
- Isolated checks passed: bilingual fact/query/recall/retraction operations, ambiguous/qualified clause rejection, Dutch dashboard intervals, no-model unknown handling. Parse-only simple sentence measurements were ~0.07–0.10s; not end-to-end latency. Dashboard checks covered success, failure retaining content, pause, deletion, deferred dialogue and clock execution.
- Backups: `preview-memory.before-dashboard-*` and `preview-memory.before-bilingual-*`. Existing algebra-request lesson and reference-correction changes preserved.

## Reply latency correction (2026-09-07)
Measured simple Dutch recall without Gemma: cProfile 2.153s, 1.245s of which was 15 GraphMap.to_dict calls copying the full procedure library. Added GraphSnapshot frozen content-root mapping, lazy isolated value copies and interface metadata lookup; execute_graph now snapshots roots rather than copying every lesson. ExecutionCache fingerprints frozen root IDs. Same profiled reply 0.904s. Ten snapshot/cache checks pass, including deletion, edits and result isolation. This changes loading mechanics only, not graph lessons or domain algorithms. Full HTTP measurement before restart: 3.063s (4331-byte incremental response).
Full live HTTP result after lazy snapshot alone was 2.984s, so that optimization did not account for most wall latency. Batched short behavior/language interpretation observation writes into existing graph transactions (Gemma/network execution stays outside these new scopes). Same live query then took 1.745s versus 3.063s initially, with the same factual answer. Ten snapshot/cache checks still pass. Gemma remains available in hybrid mode. No domain lessons changed.

## Persistent assistant tasks (2026-09-07)
- Added `build_task_curriculum.py` / `curriculum/tasks.json`, Tasks UI and `persistent_tasks.py` transport. Task state lives in `skills.tasks`: request, plan, remaining/completed steps, bindings, status, missing question, failure and in-flight checkpoint.
- Generic configured `background_progress` hook runs `task_tick` outside an enclosing transaction so workspace checkpoint writes commit before device actions. Generic startup hook runs taught `task_recover`: in-flight actions become needs_review and are not automatically retried. Existing background routines/dashboard remain on their prior hook.
- Plans use Gemma's existing structured sequence translation with a taught task policy and known procedure catalog. Graph lessons execute the selected methods and record outcomes. `task_input` asks once and stores a reply keyed to its task; reply through Tasks UI. Save/inspect/start, pause/cancel, revise current argument, resume; completed steps are not replayed. No claim of automatic general task invention or unrestricted conditional/recurring planning.
- Task:/Taak: prefixes use taught detection. Direct step JSON is also supported. Missing capabilities/unsupported plans remain saved as needs_plan.
- Isolated verification passed for missing input, resume with earlier bindings, explicit plans, failures, interrupted-action review and real on-disk reload. Backup `preview-memory.before-tasks-*`; existing graph facts, dashboard cards and Gemma mode retained.
Live task planning initially returned an incorrect Gemma refusal about asking questions; expanded the taught planning policy with an explicit task_input example across turns, after which the natural-language request produced the correct three-step plan. Live testing also exposed potential background starvation under concurrent tab polling; the worker now queues for the application lock instead of dropping its tick when busy. Queued task retained across that restart for live verification.
Live verification completed: natural-language plan saved s1=5, s2=task_input, s3=add; queued task survived preview restart, paused with 1/3 steps complete, accepted UI answer "3", then completed with results [5,"3",8]. Existing completed step was retained. The cancelled first planning attempt and completed demonstration remain visible as task history.

## Prefix-free ordinary requests (2026-09-08)
- Added taught natural_request_policy to Gemma translation instructions via session context; commands such as Task:/Solve for X: are optional. Added plan_task transport intent for persistent plan creation using the original user request. Ordinary question schema permits plan drafting but still blocks factual writes; Dutch question starters recognized and question condition arrays constrained empty.
- Normal linked requests that contain a task_input step are routed to persistent task creation instead of executing a fake immediate answer. task_input now explicitly fails outside the durable runner. Existing simple linked arithmetic remains immediate.
- Verified actual local Gemma translations and taught solver answers for “Can you find x in 5x = 20?” and “Wat is x als 5x = 20?” (both x=4); normal workflow wording produces a saved plan; “What is a task?” stays a factual question. Checked missing-input linked route with deterministic transport. Clarified full Dutch JSON example after catching an incorrect field mapping; no solver/domain algorithm changes.
- Backup before install: preview-memory.before-natural-requests-*.sqlite3. Hybrid mode and existing tasks/cards retained. This broadens routing, not a guarantee of understanding arbitrary language; unknown requests still clarify. Plans retain the existing inspect/start workflow.
