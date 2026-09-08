# Interpretation of the frozen transfer run

The current experiment did not demonstrate useful wall-clock or CPU economics from whole-program reuse across the new environments. It does **not** establish that cumulative compositional learning fails to transfer.

Across two 30-task streams per environment, both the baseline and adapted manager solved 30/60 planning tasks, 10/60 text tasks, and 20/60 tree tasks. The exact frozen condition solved zero: its host scheduler still enumerates the unavailable reduction vocabulary, and its canonicalizer rejects the new operation sequences. This is an interface dependency, not a competitive search result.

Planning retained two distinct programs per stream: movement out and back, and movement followed by pickup. Retention reduced total online graph steps by about 1%, but increased CPU cost. Text and tree retained no multi-operation programs: search found only their one-operation targets. Their failures therefore expose a discovery bottleneck before memory accumulation can be meaningfully tested. Every failed search attempt exhausted its logical step budget; none terminated on the CPU cap.

The deliberately unsupported targets test missing primitives or variable-length/recursive structure. Other targets are expressible within the five-operation limit but were not discovered under the fixed search budget. The post-run auditor checks those reference solutions separately; reference witnesses are never taught to the learner.

## What this does and does not test

The adapted condition removes reduction-specific simplification and continuation templates. It probes saved complete programs, but does not let learned methods enter new candidate compositions. Thus the narrow conclusion is: **whole-program reuse did not provide a convincing practical transfer benefit under this setup**. A small logical-step saving in planning is real but insufficient to establish faster execution, reliable cross-domain economics, or useful hierarchical growth.

The next compositional experiment should admit supplied operations and learned methods through the same generic callable interface. Candidates must be charged for expanded primitive length and nested execution, including cache hits. That policy should be frozen across environments and compared with both original-only search and this whole-program-reuse condition. No domain-specific continuation templates should be supplied. This is proposed future work, not functionality demonstrated by this run.

See REPORT.md for audited counts, costs, crossover positions, and boundary classifications; ../TRANSFER.md for reproduction and condition definitions. Previous reduction-language results remain separate and unchanged.
