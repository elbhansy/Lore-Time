# Frontend Architecture & Design System Specification (Phase 6.1)

## 1. System Overview

Phase 6.1 establishes the frontend architectural foundation for the Temporal Story Intelligence platform. The frontend operates strictly as an **editorial presentation and investigation client** consuming the backend Intelligence Core (Phases 5.0–5.4).

The frontend **does not infer story truth, compute causal links, or fabricate temporal boundaries locally**. It relies entirely on typed read models and respects the backend temporal firewall at all times.

---

## 2. Directory & Component Architecture

```text
apps/web/src/
├── api/
│   ├── client/
│   │   ├── api-client.ts           # Centralized HTTP client, error classifier, AbortSignal timeouts
│   │   └── __tests__/              # API client and error normalization test suite
│   ├── contracts/
│   │   └── read-models.ts          # Typed representations mirroring Phase 5.4 read models
│   └── queries/
│       └── intelligence-queries.ts # Scoped query functions for overview, timeline, character, graph, etc.
│
├── components/
│   ├── feedback/
│   │   ├── EmptyState.tsx          # Editorial empty state component (distinct from error state)
│   │   ├── ErrorState.tsx          # Classified error display with retry capabilities
│   │   ├── GlobalErrorBoundary.tsx # Error boundary preventing crash propagation
│   │   └── Skeleton.tsx            # Layout-preserving shimmer loader
│   ├── layout/
│   │   ├── ApplicationShell.tsx    # Global layout container with header, sidebar, main, inspector, footer
│   │   ├── Header.tsx              # Top navigation bar with active series and temporal horizon controller
│   │   ├── InspectorPanel.tsx      # Contextual right-hand inspection drawer
│   │   ├── PageLayout.tsx          # Standardized editorial page layout with title and toolbar
│   │   ├── Sidebar.tsx             # Primary navigation sidebar for intelligence views
│   │   └── Toolbar.tsx             # Scoped action and filtering toolbar
│   ├── ui/
│   │   ├── Badge.tsx               # Status, tag, and temporal horizon badges
│   │   ├── Button.tsx              # Primary, secondary, ghost, danger buttons with loading states
│   │   ├── Card.tsx                # Information-dense container with subtle borders and elevation
│   │   ├── Input.tsx               # Accessible labeled input with error indicators
│   │   └── Tabs.tsx                # Clean editorial tab navigation with count badges
│   └── visualization/
│       └── VisualizationViewport.tsx # Viewport primitive for future graph and timeline visualizers
│
├── features/
│   ├── reader/                     # Reader horizon state and chapter selector
│   └── temporal/                   # Temporal intelligence integration and React Query hooks
│
├── pages/
│   ├── overview/
│   │   └── OverviewPage.tsx        # Story overview dashboard consuming StoryOverviewReadModel
│   └── SeriesPage.tsx              # Legacy multi-view explorer
│
├── state/
│   └── temporal/
│       ├── temporal-context.tsx    # Centralized temporal context and spoiler boundary provider
│       └── __tests__/              # Temporal context unit test suite
│
└── styles/
    └── tokens.ts                   # Centralized design tokens (colors, typography, spacing, shadows)
```

---

## 3. Design System & Visual Language

- **Visual Direction**: Dark, Cinematic, Editorial, Information-Dense, Structured.
- **Palette**: Deep obsidian canvas (`#090a0f`), dark slate primary surfaces (`#11131a`), subtle borders (`#232736`), deep indigo accents (`#6366f1`), and amber temporal boundary glow (`#d97706`).
- **Typography**: Clean sans-serif hierarchy for metadata and navigation, monospace for IDs, sequences, and raw data.
- **Design Tokens**: Exported from `src/styles/tokens.ts` and synchronized as CSS custom properties in `src/index.css`.

---

## 4. API Client & Contracts

- **Base URL**: Configurable via `VITE_API_URL` with default fallback `/api/v1`.
- **Contracts**: Typed frontend contracts in `src/api/contracts/read-models.ts` mirroring `apps/api/app/schemas/read_models.py`:
  - `TemporalContextReadModel`
  - `StoryOverviewReadModel`
  - `TimelineReadModel`
  - `CharacterReadModel`
  - `GenericGraphReadModel`
  - `EventReadModel`
  - `TemporalNarrativeCausalExplanationDTO`
- **Error Normalization**: HTTP and network errors are normalized into `NormalizedApiError` classified into `NETWORK`, `NOT_FOUND`, `BAD_REQUEST`, `TEMPORAL_BOUNDARY`, `SERVER_ERROR`, and `UNKNOWN`.

---

## 5. Temporal Context & Series Isolation

- **State Abstraction**: `TemporalProvider` provides `seriesId`, `readerChapter`, `minVisibleChapter`, and `maxVisibleChapter`.
- **URL Synchronization**: Synchronizes `?chapter=` parameter with reader navigation, clamping values between `1` and `totalChapters`.
- **Temporal Firewall**: Prevents future event leakages by providing strict `maxVisibleChapter` to all consumers and queries.
- **Series Isolation**: All API calls and UI routes are scoped by `:seriesId`.

---

## 6. Verification and Regression Gates

- **Vitest Unit/Integration Tests**: 38 passed across 13 test files (0 failures).
- **TypeScript & Production Build**: `tsc -b && vite build` succeeded (0 type errors, production bundle generated).
- **Linter**: `oxlint` clean (0 errors).
- **Backend Regression Suite**: 404 tests passed, 0 skipped, 0 failed.
