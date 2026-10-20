# Provenance: Analytics dashboard redesign

Interactive posture only. Headless runs carry intent, the assumption ledger, and decisions in `DESIGN.md` alone.

## Session

- Session: Initial design (October 20, 2026)
- Timestamp: 2026-10-20T15:03:47Z
- CWD: /workspace

## Initial Request (verbatim)

> The analytics dashboard needs a total redesign. We did have a prior plan to do this but it was too conservative. To be clear, just about everything needs replacing. The UI is cumbersome, the layout and styling not usable. We'd need a few passes over this, redesigning the style and component system, rethinking the dashboards and data layouts. I'd like to see landing dashboard with a good quick view into trending data, I'd like the graphs and visualisations to be rich and dynamic and interactive. Also a minor thing if the user isn't logged in just direct straight to login.
>
> create a thorough design to rethink the UI. Keep the changes just to the analytics dashboard package

## Design Conversation

### Turn 1

**User responded:** The analytics dashboard needs a total redesign. The prior plan was too conservative. Just about everything needs replacing. The UI is cumbersome, the layout and styling not usable. A few passes: the style and component system, the dashboards and data layouts. A landing dashboard with a good quick view into trending data. Graphs and visualisations rich and dynamic and interactive. If the user isn't logged in, direct straight to login. Keep the changes just to the analytics dashboard package.

**Agent decisions:**

- The prior plan is `docs/plans/14-analytics-ui.md` (close-out). Signed text at git `2bc26e0`. It kept the routes and ECharts. This design supersedes that conservatism.
- The folder is `docs/plans/17-analytics-dashboard-redesign`. Prefixes 01–16 are taken.
- The work stays inside `packages/yakka-analytics`.

### Turn 2

**User responded:** Reinvent current analytical jobs (saved views, quality, cost, usage, conversation grain). They return as exploration tools in a new information architecture, not as a port of the old pages. The package may change how it aggregates and loads data. Libraries are allowed. No visual reference. The bar is rich analysis: interactive, exploratory, not a static report.

**Agent decisions:**

- Usage, cost, quality, conversation grain, and saved analysis are tools inside one investigation, opened from the landing view.
- The aggregation boundary may compose existing reads or aggregate in the client. No library and no version is chosen in the design.
- There is nothing to match visually. Plan 14's solarized sheet and ECharts grammar are not the constraint.

### Turn 3

**Agent asked:** Whether an unauthenticated user is redirected before the document is painted. That redirect would be in `packages/yakka/internal/serve/serve.go`. The alternative is a client redirect to `/login` after the document loads, inside the package.

**User responded:** Not answered.

**Agent decisions:**

- The original constraint decides it: "Keep the changes just to the analytics dashboard package."
- Unauthenticated users go straight to login from inside the package: a client redirect to `/login` after the document loads.
- `packages/yakka/internal/serve/serve.go` is out of scope.

### Turn 4

**User responded:** Apply the adversarial review. One session-gate predicate, and those entry conditions in the Phase 1 outcome. The aggregation contract gains tenant, the quality baseline, in-window filter values, a named clamp, and an ignored `conversation_id` exclude. Phase 2's outcome is the color and type observations, approach open, and the report nav stays. Phase 3's outcome covers every ask Phase 5 uses. Phase 5's outcome is the checkable investigation observations, including the old report paths not rendering those reports and the report nav leaving in this phase, approach open, and the investigation path named. Three assumption-ledger entries: landing measures, which jobs do not return, local serve stays. The landing picture is two `ask: trend` results, `hook_events` and `cost_usd`.

**Agent decisions:**

- Applied each of those as the review's smallest change. The investigation path is `/` with an `ask` query. Empty query on `/` stays the landing.

## Agent Decisions

- **Local serve is not sent to login**: loopback with an empty configured base stays, even though `GET /v1/me` is 401 and `isCollectorMode()` is true. The gate calls `GET /v1/me` only. Rationale: design 7 and design 3 already treat local as tenant `local` with no session. If wrong, local `/` would also end on `/login`. Ledger: Assumption 3.
- **Identity and connection stay**: profile, settings, and device grant remain, and they use the new visual system. Rationale: the request reinvented the analytical jobs. The package still signs a person in, holds a tenant, and stores a cross-origin base.
- **Old report questions survive as breakdowns**: repo, hook, and execution shape are asks inside the investigation, not pages. Rationale: the jobs named in turn 2 are the ones that return as tools. Porting `/repos`, `/hooks`, `/executions`, and `/explore` would keep the information architecture turn 2 rejected.
- **Saved analysis stores the investigation**: `{ id, name, spec }` with the boundary request, including window and filters, in `localStorage`. Rationale: there is no server view store inside the package boundary, and `{ report, params }` is the old page port.
- **Design 7 is amended with the phases**: routes, data loading, and the visual system are the pivot the stable docs do not yet reflect. `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` stay. `docs/design/06-*.md` is missing and is not a blocker.
- **Refine runs**: five phases. A one-phase design a single worker could carry would skip refine. This one does not.
