---
globs:
  - "app/frontend/**"
---

- Path alias: `@/` maps to `src/` (configured in vite.config.ts and tsconfig)
- Routing: file-based via TanStack Router — add routes as files under `src/routes/`, `routeTree.gen.ts` is auto-generated (do not edit manually)
- UI components: shadcn/ui with `components.json` config (rsc: false, baseColor: slate, cssVariables: true). Components install to `src/shared/ui/` — aliases configured in `components.json`
- Package manager: bun (not npm/yarn). CI uses `bun install --frozen-lockfile` — commit `bun.lock` after adding/updating deps.
- API client: auto-generated via `@hey-api/openapi-ts` from `openapi.json` → `src/shared/api/`. Uses axios (`@hey-api/client-axios`), not fetch. `src/shared/api/` is ESLint-ignored — never edit manually, always regenerate.
- Layout: features/ (hooks-only domain logic: `features/{domain}/hooks/use-{noun}.ts`), widgets/ (composite UI), shared/ (api, lib, ui components)
- Data fetching: TanStack React Query with generated query/mutation options from the API client
- Forms: react-hook-form + zod validation
- No `enum` keyword — `erasableSyntaxOnly: true` in tsconfig; use `as const` objects instead
- Type imports must use `import type` — `verbatimModuleSyntax: true` enforced
- Unused vars/params break the build — `noUnusedLocals` + `noUnusedParameters` are `true`
- Tailwind v4 CSS-only config — no `tailwind.config.ts`; theme customization in `src/index.css` via `@theme inline {}`
