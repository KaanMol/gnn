# Proposed Rust graph engine and binary graph format

Status: design proposal, not an implemented engine or a measured Rust speedup.

## Latest user requirements

Recorded on 2026-09-08. These are notes for later work; do not start a Rust rewrite as part of the current learning experiment.

- The learning system should generate and revise its own executable graph/bytecode, not generate Rust source code or require a Rust compiler each time it learns.
- A generic Rust engine remains an architectural possibility, not a requirement for the learner's output language or an implementation started here.
- Knowledge must remain editable and capable of improvement. Bytecode needs a defined, validated representation that the system can inspect, compose, test and persist.
- Load only the needed working window, under a RAM budget. Permit retention of selected hot sections and writeback of changed knowledge; keep unused sections on disk.
- Explore better binary storage, compilation and memory residency later. Continue the current evidence/reuse/feedback experiments now.
- Export self-contained, shareable model packages, analogous in distribution to open-weight models. A compatible engine must be able to load the package, inspect it, execute it and continue learning independently of the originating process.

A useful distinction is canonical editable bytecode/graph IR versus optional optimized execution blocks. The system can emit canonical instructions directly, validate and test the proposed revision, then commit it. Optimized blocks remain rebuildable derivatives. No Rust-source generation is involved, and self-modification does not imply that an edit is an improvement: it must pass held-out behavioral and cost checks.

## Shareable model packages

Treat an exported `.gpack` as a portable graph-model checkpoint. This system does not currently have neural weights; the analogous learned content is its graph definitions, compositions, learned policies/evidence and executable canonical instructions.

An export should contain:

- A manifest identifying the format, model revision, required generic opcode/semantics versions and entry roots.
- The canonical learned graph/bytecode and all included graph dependencies, with stable content identities.
- Selected learning evidence/provenance, licensing information and optional benchmark metadata.
- Optional prepared caches labeled by ABI/target; incompatible caches are ignored and rebuilt from canonical content.
- Declarations of any external ports needed by particular capabilities. The loader reports missing ports; exporting a model cannot make a hardware-dependent capability portable by itself.

The package cannot depend on local database paths, RAM addresses, undeclared procedures, credentials or the original process. Export packages include their dependency closure and pass a clean-process load test. A model license and the format specification should accompany public distribution; merely having a shareable binary does not establish open licensing or compatibility with unrelated engines.

Support both a consolidated portable checkpoint and optional revision/delta packages that explicitly identify their base checkpoint. The default shared artifact should load without a separately copied journal. A recipient can fork the model, learn into a new local revision, and export a new package while preserving provenance. Large packages still load only their needed working window.

## Objective and boundary

Replace the Python execution/storage core with a Rust engine that runs the existing graph semantics. Programs, syntax rules, learned compositions, search policies, evidence and warm-section policies remain graph data. Rust provides generic execution, validation, resource accounting, persistence and explicitly registered I/O ports. It must not acquire JavaScript-, React-, algebra- or task-specific handlers during migration.

Preserve exact numeric behavior and the existing dispatch into taught arithmetic graphs. A native numeric shortcut would be a separate semantic decision, not an unnoticed implementation detail. Preserve lazy branches, attempts/errors, snapshot isolation, definition revision, traces and charged work on cached calls.

## Two representations in one design

The persistent graph and the executable layout serve different purposes:

1. **Canonical graph segments:** immutable typed values, ordered edges, procedure graphs, evidence and root revisions. Content hashes identify immutable objects across reloads and compaction. These are authoritative knowledge.
2. **Prepared execution segments:** dense instruction arrays, constant pools, register indices, resolved references and debug mappings. These are derived from a particular graph revision and engine ABI. They can always be discarded and rebuilt.

Changing storage alone does not remove interpreter dispatch, allocations, validation or search costs. A compact file extension alone provides no speed guarantee.

## Proposed `.gpack` container

Use an explicitly specified little-endian wire layout, never an in-memory Rust struct dump. Initial format version zero is experimental.

| Section | Contents |
|---|---|
| Header | Magic, format version, required feature flags, generation, directory offset and length |
| Segment directory | Segment kind, offset, byte length, checksum and optional codec identifier |
| Symbol table | Length-prefixed UTF-8 names, indexed by local integer IDs |
| Value arena | Tagged scalars and containers; variable-size values reference bounded byte ranges |
| Edge arena | Ordered integer references; explicit record keys and list positions |
| Object identity index | Stable content hash to segment/local offset mapping |
| Root index | Namespace/key to immutable object ID at a committed generation |
| Optional prepared blocks | VM version, source/dependency hashes, instruction/operand arrays and constants |
| Debug/evidence index | Instruction-to-source-node mappings and provenance references |

Use dense local references within a segment and explicit cross-segment references. Small programs should not pay a full content-hash lookup per instruction. Specify large-segment overflow handling explicitly rather than assuming every graph fits in 32 bits.

Do not require whole-file decompression for executable blocks. Compression can be independently enabled for cold evidence or text segments after measurement. Memory mapping is an option for immutable validated segments, not a claim that all graph data can execute without decoding or allocation.

## Load only the required working window

The engine must operate under a configured residency budget, with most knowledge remaining on disk. A window is a bounded set of graph/program blocks required by the current activity; it is not the entire file or necessarily one contiguous byte range.

- Keep a small directory/index cache in memory. Root and object indexes must support block-level lookups without loading all keys.
- Place a procedure's instructions, constants and frequently traversed local edges together when practical. Preserve stable object identities even when compaction changes physical placement.
- Fetch the entry block first. Resolve further blocks lazily at calls or traversals; do not preload the entire transitive graph, which may reach most of the database.
- Bound each independently loadable/decompressible block. Select its size from cold-load, random-traversal and edited-program benchmarks rather than assuming one universally optimal page size.
- Track canonical pages, decoded values, bytecode and optional native code separately under one accounted memory budget. Mapping the file does not make all of it resident, but an unbounded decoded-object cache can still consume RAM.
- Let graph policies request prefetch/retention for a bounded region using observed access evidence. The engine may refuse requests exceeding quotas and must report actual status.
- Protect currently executing blocks from eviction. Evict clean, unretained blocks when space is needed; journal/commit dirty graph revisions before releasing them, or explicitly abandon the uncommitted revision.
- Apply OS page locking only to a small explicitly selected hot set, if supported and within platform limits. It is independent from snapshot immutability and is not required for ordinary demand loading.

Conceptual path: **disk index → needed graph block → RAM working window → bytecode/native cache → committed delta back to disk**. Unused graph regions remain on disk. When execution shifts to another region, the window shifts with it.

## Optional native compilation and memory locking

First implement bounded bytecode execution. Later, use measured reuse to select blocks for native compilation; include compile time and extra code memory in the decision. A backend such as [Cranelift](https://github.com/bytecodealliance/cranelift-jit-demo) could supply generic machine-code generation. This does not move domain rules out of graph data.

Freezing a revision protects execution consistency. OS memory locking instead asks for page residency; it is platform-specific and limited, as illustrated by the [POSIX memory-locking specification](https://man7.org/linux/man-pages/man3/mlock.3p.html). Neither mechanism automatically makes arithmetic or search faster. Native blocks need the same revision checks, logical metering, error behavior and invalidation as bytecode.

## Learning and persistence

Required lifecycle: **stored graph → RAM graph → prepared bytecode → execution/learning → committed graph changes → reload**. Bytecode is a first-class persisted cache, while the editable graph remains the source of truth.

The engine API should expose generic load, prepare, execute, begin-revision, apply-graph-edits, commit, flush, inspect-residency and release operations. The graph can request these through its engine port; the engine enforces dependency and resource constraints.

In RAM, edits create a new graph revision and mark its modified objects dirty. Commit validates and journals the canonical changes, publishes a new root generation, and invalidates/rebuilds prepared blocks whose source or dependencies changed. Executions already using the previous generation keep a consistent snapshot. New executions use the committed generation.

Persist prepared blocks with their source hash, dependency hashes, bytecode version and engine ABI. Reload a valid block directly into the executable representation; rebuild only blocks that fail compatibility checks. Store symbolic/relative references, never process pointers or allocator layouts. Restarting on a new process must resolve references safely.

"Write back from RAM" means committing dirty canonical graph objects and optionally compatible prepared blocks. It does not mean dumping arbitrary process memory. A prepared block may be evicted while the corresponding graph revision remains durable. A dirty revision must be committed or explicitly abandoned before release.

Direct bytecode rewriting is a separate possible feature: require validation and a lossless canonical graph representation before publishing it as learned knowledge. Initially, self-modification edits graph IR and recompiles affected blocks. This keeps learning inspectable and avoids needing to reverse arbitrary optimized bytecode into the original graph.

Learning appends new objects and root revisions instead of rewriting the entire image. Pair the checkpoint with a transaction journal:

- Each transaction has framing, a sequence number, payload length, checksum and commit record.
- Publish a new root generation only after referenced data is durable under the selected durability mode.
- Recovery accepts complete committed transactions and ignores incomplete tails.
- Compaction writes a fresh checkpoint and publishes it atomically; readers retain their previous immutable generation until finished.
- Retain explicit history roots according to policy. Objects needed by active snapshots or preserved evidence cannot be reclaimed.

These are requirements to implement and fault-test, not durability guarantees already achieved. Replacing SQLite means taking responsibility for crash recovery, migration, corruption detection and inspection tooling.

## Rust execution layout

- A validated procedure becomes a contiguous array of generic opcodes and integer operand/register references.
- Constants, variable-length operands and nested bodies live in separate bounded arenas.
- Runtime values use explicit tags and arena/shared references where appropriate; copying entire graph dictionaries is unnecessary.
- Calls resolve against one immutable root generation. Prepared blocks carry dependency identities so edits cannot reuse stale code.
- Optional instruction fusion must preserve lazy behavior, errors, source attribution and logical resource charges.
- Graph requests such as prepare, retain, inspect and release choose what to keep warm. The engine enforces memory limits and reports residency or refusal.

Actual OS page residency cannot be promised merely by holding a mapping. Distinguish loaded, prepared and retained states; do not report "in RAM" as a hard guarantee unless it is enforced and measured.

## Parallelism

Start with deterministic single-threaded parity. Then run independent candidate evaluations on worker-local arenas against shared immutable snapshots. Reserve and charge a common logical budget, cancel work on exhaustion, and define deterministic candidate selection. Keep mutation and effectful ports serialized unless their contracts explicitly allow concurrency.

More threads can increase speculative work; record all consumed work, including losing workers. Do not report a speedup obtained by silently expanding the search budget.

## Migration gates

1. Define a versioned export of SQLite roots and immutable values. Import into a new `.gpack` without changing the live database. Verify root/value equivalence and round-trip export.
2. Build a Rust reader, inspector and validator. Test truncated files, corrupt references, unknown required versions and recovery from interrupted commits.
3. Implement the generic VM with Python as a differential oracle. Match outputs, errors, effects, revisions and logical step counts on the existing tests and fixed generated programs.
4. Run the synthesis and reuse benchmarks unchanged. Measure cold load, edited-program load, warm execution, allocations, resident memory, write latency and recovery.
5. Connect the preview through a stable engine API after parity. Retain export/rollback until the new engine passes recovery and end-to-end tests.
6. Add instruction fusion or independent-search workers as separately measured changes.

No whole-system cutover is justified by this document alone. The first implementation milestone is a file reader plus generic-VM parity slice, not a promise of full Rust replacement.

## Evidence from the current engine

An instrumented local sample on 2026-09-08 executed `select → sum` over `[-9, 2, 5]`, using the same open database connection and execution cache. The top-level procedure had already been fetched before counting SQL statements.

| Phase | SQL statements during execution | Logical graph steps | Wall time |
|---|---:|---:|---:|
| Cold library/execution | 12,112 | 3,379 | 179 ms |
| Warm | 1 | 3,379 | 22 ms |
| Warm again | 1 | 3,379 | 22 ms |

This is a single diagnostic sample with SQL tracing on a shared machine, not a general benchmark. It indicates that cold reconstruction and warm execution deserve separate optimization. It does not measure Rust, a binary format, or the fraction of warm time attributable to SQLite.

Relevant existing code: `graph_store.py` caches decoded immutable nodes but constructs execution snapshots and deep-copies requested values. `graph_runtime.py` prepares Python instruction tuples with integer operand indices. A Rust rewrite can preserve the architecture while replacing those object-heavy execution structures.
