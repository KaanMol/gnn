# Feedback-grounded field learning

The graph observed outcomes from two synthetic graph environments, rejected ambiguous evidence, chose one informative probe from a supplied pool, then inferred and saved a field predictor. No field name was supplied to the learner.

Both predictors passed 40 held-out records. An unseen field rename returned unknown; relearning from feedback in the renamed environment succeeded. Contradictory observations produced no saved predictor; a pool without distinguishing probes returned no proposed experiment.

- Synthetic environment, with supplied graph action rules.
- Graph chooses an informative probe from a supplied finite pool using a supplied disagreement policy.
- Candidate language is a single observed field, not arbitrary causal rules.
- Renamed fields require new feedback; there is no zero-shot semantic transfer.
- Forty tests per world vary identifiers; there are only four boolean feature combinations.
- No claim of human-like meaning or real-world causal understanding.
