# Phases Directory

Organized phase-by-phase planning and specifications, all aligned with the [master plan](../plan.md).

## Structure

```
phases/
├── phase-1.md       # ✅ Canonical contract foundation
├── phase-2.md       # → Plugin SDK & connector implementation
├── phase-3.md       # → API layer & data retrieval
├── phase-4.md       # → Dashboard & exploration UI
└── phase-5.md       # → Agent layer & automation
```

## Phase Template

Each phase document includes:

- **Overview** — What the phase delivers
- **Deliverables** — Artifacts, code, docs
- **Key Design Principles** — Architectural decisions for this phase
- **Acceptance Criteria** — Gate requirements before moving to next phase
- **What's NOT Included** — Clear scope boundaries
- **Next Steps** — Preview of following phase
- **Alignment with Master Plan** — How phase fulfills `plan.md` commitments

## Phases

| Phase | Focus                      | Alignment                     | Status     |
| ----- | -------------------------- | ----------------------------- | ---------- |
| 1     | Contracts & schemas        | Source abstraction foundation | ✅ Complete |
| 2     | Implementation & ingestion | Plugin layer + connectors     | 🚧 Planned  |
| 3     | API layer                  | Canonical data retrieval      | 🚧 Planned  |
| 4     | Dashboard UI               | Multilingual exploration      | 🚧 Planned  |
| 5     | Agent framework            | Agentic automation            | 🚧 Planned  |

## Related Documentation

- **Master Plan:** [`specs/plan.md`](../plan.md) — Vision, principles, and strategy
- **Public Docs:** See `docs/` for user-facing documentation
- **Contracts:** See `docs/contracts/` for all technical contracts
- **Configs:** See `configs/` for source definitions and schemas
- **Fixtures:** See `data/fixtures/` for test data
