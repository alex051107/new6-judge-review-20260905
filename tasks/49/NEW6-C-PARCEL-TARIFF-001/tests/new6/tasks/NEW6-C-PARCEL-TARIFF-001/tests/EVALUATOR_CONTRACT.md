# Candidate evidence and scoring

The same six factual criterion values feed all three frozen profiles. `capability_first` is the primary profile; passing uses only the unrounded score ≥ 0.70. There is no hurdle, cap or filename-based negative decision.

Fixed denominators before Agent execution:

- R001: 192 in-scope published service/band/unit/zone prices. Each occurrence has a stable semantic key. Duplicate or contradictory occurrences at a required key do not earn that key's credit. Extra clearly labelled archival rates outside the requested service/scope do not reduce credit.
- R002: 24 distinct service/weight-band identities, plus one effective-date fact. Each complete band has exactly eight requested zone occurrences. Standard date strings and Excel dates are accepted.
- R003: four actually delivered output facts per request (two prices, selected service, selected price), plus the actually displayed batch total: 49 facts. All displayed final totals must agree with the source answer. The evaluator never supplies a missing candidate subtotal.
- R004: four declared changes, each with four targeted request response facts, one batch response fact, and one invariant fact: 24 facts. Numeric response is `(candidate after − candidate before) == (oracle after − oracle before)` in USD. Selected service checks the expected change or preserves the candidate's unchanged selection when no change is due. Inputs are read back after mutation. Original tariff rows and every unaffected request row must remain unchanged; these full checks are aggregated into the single invariant fact per scenario. An erroneous constant offset loses R003 but retains R004 when the actual deltas are correct. Constant baseline quotes retain R003 but lose their affected response facts. The denominator was frozen before any Agent attempt to cover the targeted changes without counting hundreds of untouched outputs as propagation successes.
- R005: each of 12 original request inputs has its original in-scope weight/unit/zone, plus the original request-ID set: 13 facts. Only declared in-scope input changes are tested.
- R006: 24 band-to-page bindings, request provenance and Notice 123 provenance: 26 facts. Page 15 does not match page 5.

For each unit, evidence records candidate value, expected fact and correctness. Candidate self-consistency is reported separately. Partial credit uses these fixed denominators, not the number of parsed candidate rows. A negative fixture can pass the 0.70 threshold and still correctly lose the intended items.

## Parsing and recalculation boundary

The current deterministic reader discovers labelled long tables by fields, with documented aliases in `evaluate.py`. It accepts changed sheet names, row positions/order and reordered columns. It does not use private answer values or reference cell addresses to identify candidate data. Unrecognized valid layouts return `JUDGE_ERROR` for an additional semantic adapter/review; they are not automatic business failures. The current reader is not a complete agentic parser or an assurance that every arbitrary wide-grid/presentation layout is supported.

Version `new6-usps-facts-v1.1-partial-parse` checks rate parsing separately from quote parsing. An unbound weight-by-zone grid remains pending even when a quote long table was successfully read. Detection uses visible headers and populated row shape, never price matches to the Oracle. A clearly empty labelled rate table or explicit candidate omission statement can be graded as a missing business deliverable. If no rate rows bind and omission evidence is insufficient, the result is pending rather than zero. This repair does not add a wide-grid adapter and does not change the frozen Agent task or any score weight or denominator.

The shared runtime recalculates isolated copies using LibreOffice. It invalidates caches and retains source/output hashes, commands and receipts. Broken references and missing numeric candidate outputs are business evidence; unresolved formula-name/type/lookup engine errors are pending native/semantic diagnosis with no score. Python in Excel is a concrete legitimate implementation requiring an unavailable native engine and is tested as pending, not zero.

Missing output requires completed-run evidence for `OUTPUT_MISSING`; otherwise the evaluator returns `INFRA_ERROR`. A broken ZIP/XLSX returns `MALFORMED_OUTPUT`. Genuine legal parser limitations and business failures are distinct.

## External acceptance gaps

This local evaluator has no separately accepted negative-action items and no general agentic layout parser. Those external requirements have not been declared satisfied. Public redistribution rights have not been independently cleared. Fixture counts are calibration evidence, not Agent attempts or natural failure rates.


Current measurement version: new6-usps-facts-v2.0-downstream-use. The user authorized static/dynamic value rebalancing. The current rubric supersedes v1 weights; R004 has11 active response facts, while R005 has26 request/preservation/invariant facts, all fixed from the Oracle and declared test inputs. Zero-delta facts do not earn active-update credit. Baseline accuracy remains R003. Use tests/calibrate_measurement_v2.py for the affected calibration batch; earlier receipts and the original Agent trial are immutable historical evidence.
