Bounded program-synthesis experiment
===================================

The stored learner enumerates call chains up to depth three over four supplied
operations: sum, count, reverse, select. It executes candidates against training
examples, stops at the first consistent chain, emits an ordinary executable graph,
and saves it through the graph's workspace port. No language model participates.
The search algorithm, operation grammar, predicates, projection adapters, arithmetic,
and success criterion are supplied. It learns the composition, not those primitives.

The numerical training task supplies four examples and the positive predicate and
identity projection. Search evaluates 17 candidates and chooses select followed by
sum. Changing the examples to count positives selects select followed by count.
Contradictory examples exhaust the bounded search without saving a procedure.

After learning finishes, an independent host test harness generates 100 distinct
numerical inputs, excludes training inputs, and compares execution of the saved graph
with a reference calculation. A second set contains 100 distinct product arrays,
excluding its training inputs. These inputs are never supplied to the learner.
Reusing the same graph with supplied availability/price adapters passes the product
task; this is configured parameterized reuse, not autonomous abstraction transfer.
It takes one candidate check versus 17 candidates for a fresh search under this fixed
ordering. This does not establish a general runtime advantage or open-ended coding.

Artifacts: ../program-synthesis-report.json and program-synthesis.graph.sqlite3.
The live app also stores learned_synth_positive_total and its training evidence.

To execute it through chat:

    Run skill learned_synth_positive_total: {"items":[-3,4,6],"predicate":"synth_positive","projector":"synth_identity"}

Expected result: 10. To reproduce independently, choose a fresh database path:

    python3 -B experiments/program_synthesis.py --database /tmp/new-synthesis.sqlite3 --report /tmp/new-synthesis-report.json

The experiment refuses to overwrite an existing learned procedure. It does not
promote that procedure into the search vocabulary automatically. Hierarchical
vocabulary growth is a separate, not-yet-implemented experiment.
