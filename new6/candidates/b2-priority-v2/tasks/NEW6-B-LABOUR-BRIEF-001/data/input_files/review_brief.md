# Reporting scope

Compare the supplied January 2024 and January 2025 LI01 releases for English lower-tier and unitary/local authorities represented by the same geography code in both. This scope uses code prefixes E06, E07, E08 and E09; other geographic levels are outside the comparison. Use each source indicator's observation period and population definition.

Assess availability and comparability separately for employment and unemployment. Record affected exclusions and their reasons. Keep the source statistical values available for review. For this review, calculate changes and ties from rates as displayed to one decimal place; underlying values can remain in the preserved source workbooks. Changes are measured in percentage points.

The ranking covers unemployment-comparable authorities with positive unemployment-rate changes. Report the largest five when at least five qualify; otherwise report all that qualify. Order exact ties by geography code ascending, and show employment changes for the same authorities. Interpret the estimates within the qualifications in the supplied sources.

# Follow-up review policy

This is a benchmark-authored descriptive review exercise using published ONS statistics, not a real commissioning decision. The review team can examine at most five areas. The unemployment-increase top five requested above remains a descriptive comparison; the follow-up shortlist below has a separate purpose.

Consider all in-scope codes in either release. An area is eligible for follow-up only if both indicators are comparable, unemployment has risen by at least the scenario threshold and employment has fallen by at least that same threshold. Both boundary values are inclusive. Missing or suppressed data are unavailable, never zero or evidence of no deterioration.

Use three scenarios: baseline 1.0 percentage point, relaxed 0.5 percentage point, strict 2.0 percentage points. Among eligible areas, select up to five, ordered by unemployment increase descending, employment change ascending (the larger fall first), then geography code ascending. An eligible area outside the five places remains eligible but is not selected. Do not fill unused places with ineligible areas.

Provide a screening register for every in-scope code showing eligibility and selection under all three scenarios, with source changes or a traceable link to the comparison dataset. Provide an ordered shortlist for each scenario, including the code, both indicator changes and order. Reconcile selected-area counts and identify which codes enter or leave relative to baseline. In the briefing distinguish descriptive deterioration and policy sensitivity from statistical significance or a causal explanation. These three fixed scenario comparisons may be delivered as static results in any clear layout. The editable live review below is a separate required deliverable.

# Editable live review

Alongside the three fixed comparisons, provide clearly labelled numeric input cells for `Unemployment threshold pp` (initially 1.0), `Employment decline threshold pp` (initially 1.0), and `Review places` (initially 5). The two thresholds may each vary independently between 0 and 5 percentage points; capacity is an integer from 1 to 10. These are operational screening settings, not statistical significance thresholds.

A separate current review must update automatically when these inputs change, using the same inclusive eligibility and ordering policy. Deliver current eligibility and current selection for every code, the ordered current shortlist with both changes, and a labelled `Current selected count`. Permit fewer selected areas than the capacity. Do not let a current-review change alter the original rates, exclusions, descriptive chart or three fixed scenario results. Keep those fixed results clearly distinguished from the live review. Formula or other native spreadsheet implementations are acceptable; a precomputed live snapshot alone does not satisfy this requirement.
