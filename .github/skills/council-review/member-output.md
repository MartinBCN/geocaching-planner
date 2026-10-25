# Council member output contract

Every council member returns **exactly** this Markdown structure and nothing else.

```markdown
## <Member role> review: <target filename>

**Member verdict:** Approve | Approve with changes | Revise & resubmit
**Rationale:** <one sentence>

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| <PFX>-1 | Blocker/Major/Minor/Nit | <section>: "<short exact quote>" | <what is wrong and why it matters> | <concrete fix, e.g. a rewritten AC or sentence> |

(If there are no findings, write the single row: `| – | – | – | No findings | – |`)

### Strengths
- <up to 3 bullets; what should be kept>

### Open questions for the author
- <questions whose answer could change the review; "none" if none>

### Out of my lane
- <one-line notes for other council members; "none" if none>
```

## Rules
- **ID prefix:** Architect `ARC`, Product Designer `PRD`, Quality & Delivery `QDE`. Number the findings in order of severity.
- **Evidence is mandatory.** Quote the target or a context file exactly (short, ≤ 25 words). For a *missing* item, quote the section where it should be and say what is absent.
- **Member verdict** follows the same rule as the council: any Blocker → Revise & resubmit, else any Major → Approve with changes, else Approve.
- Stay in your lane. Do not invent requirements, and do not demand anything the spec lists as a non-goal.

## Severity scale (shared)
| Severity | Meaning |
|---|---|
| **Blocker** | Wrong, contradicts an Accepted ADR or the spec, or cannot be implemented or verified as written. Must be fixed before Ready/Accepted. |
| **Major** | A significant gap, ambiguity, or risk that will likely cause rework or a wrong implementation. |
| **Minor** | Should be fixed. Low risk. |
| **Nit** | Wording, formatting, or style. |
