Reference correction
====================

A person and a city can share a spelling without sharing an identity. The stored
meaning_assertions rule now scopes both fact endpoints; existing source-scoping rows
without an endpoint field retain their subject-only behavior. Original assertions,
provenance and negation remain unchanged. Full scoped labels identify the interpreted
entities. Ambiguous bare labels prompt for a choice, including in new assertions.

The explicit separate_person_city operation invokes a stored correction method that
uses taught relation-role evidence. Its current roles cover has sister/has brother,
sister of/brother of, world bank listed capital, and capital of. It requires evidence
for both meanings, creates a policy revision, and persists it atomically. Unsupported
or insufficient evidence does not produce a success response. This is a bounded
correction capability, not arbitrary entity disambiguation.

The graph recognizes the form “I meant NAME as a person's name, not the city …”,
including curly apostrophes. The language translator also has the typed correction
operation available. No particular person, city, country, or spelling is hard-coded.

A model-generated clarify operation cannot claim it changed memory. Its answer is
rendered by dialogue_clarification_response as an explicit no-change explanation.
Actual engine failures keep their own error details. Successful correction text is
returned only after the new policy passes validation and the staged change commits.

Live Vienna correction preserved the original family and geography assertions while
interpreting Julia's sister as Vienna (person) and Austria's capital as Vienna (city).
Regression evidence: reference-correction-report.json and test_reference_correction.py.
