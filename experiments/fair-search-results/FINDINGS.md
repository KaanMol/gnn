# Fair allocation did not preserve discovery reliably

Across six new planning orders, no-memory search solved **90/180**, while the same fair allocator with managed memory solved **80/180**. Four orders tied at 15/30; two dropped from 15/30 to 10/30 with memory. There were no successful mixed compositions and no final audit false positives.

In both losing orders, pickup was retained but subsequent round-trip tasks were not solved. No-memory search solved all five round-trip instances in each of those orders. Thus this allocation policy did not reliably protect acquisition when learned callables enlarged the search space.

Quota fairness was implemented and tested, but is not sufficient for useful allocation here. It equalizes child attempts among the current near-tied parents, not their execution costs; new candidates can change the cohort. These results do not establish that a different fair policy cannot help.

The next separately frozen experiment partitions search effort between original-only discovery and memory-assisted search. This result remains unchanged. The six permutations reuse two existing example banks, so they test order sensitivity rather than fresh-example or cross-domain generalization. The prior allocator was not rerun on these orders; this comparison measures memory's effect under the new allocator, not an isolated causal estimate of the allocator change.

See REPORT.md and report.json for per-order costs, paired losses, and integrity checks. The running application, memory capacity, text/tree, and abstraction machinery were not changed.
