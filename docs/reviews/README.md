# Council reviews

Advisory review reports produced by the **Council of the Wise** (`.github/skills/council-review`, [ADR-0010](../adr/0010-council-review.md)).

## How to run
In Copilot CLI: *"Run the council on T-007"* or *"council-review ADR-0004"*.

## Files
| Folder | Contents |
|---|---|
| `adr/` | ADR reviews, e.g. `adr/0004-brouter-routing-review-1.md` |
| `features/` | Ticket reviews, e.g. `features/T-007-pq-gpx-parser-review-1.md` |

File name: `<target-stem>-review-<n>.md`. Each re-review gets the next `n`. Old reports are never edited.

## Reading a report
| Verdict | Meaning | Typical next step |
|---|---|---|
| **Approve** | No Blocker or Major findings | Set the ticket to Ready, or the ADR to Accepted |
| **Approve with changes** | At least one Major finding, no Blocker | Fix the Majors (no re-review required) |
| **Revise & resubmit** | At least one Blocker | Revise, then run the council again |

| Severity | Meaning |
|---|---|
| Blocker | Wrong, contradicts an ADR or the spec, or cannot be implemented or verified |
| Major | Significant gap; will likely cause rework |
| Minor | Should be fixed; low risk |
| Nit | Wording or style |

The **Dissent** section shows where members disagreed. It is deliberately not resolved by the council. The owner decides.
