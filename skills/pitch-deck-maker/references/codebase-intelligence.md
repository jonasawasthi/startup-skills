# Codebase intelligence procedure

Goal: an **evidence-backed product map**. The result is a description of what exists, what is being built, and what is only planned, with file paths as proof.

## Step 1: scan (read-only)

```bash
"$TK/bin/startup-kit" scan <repo> --out <evidence-dir>
```

The inventory lists the following:

- deployable units (apps, packages, services) with frameworks, integrations, route counts, LOC, tests and deploy configs;
- data-model objects (Drizzle, Prisma, SQL, Django) and role enums;
- documentation files with titles;
- environment variable **names** from example files (values are never read);
- brand assets (logo candidates, colour tokens) and screenshot candidates;
- analytics events tracked in code;
- unfinished-work markers (TODO, FIXME, "coming soon", mock data);
- git activity per area (last 90 days) and recent commits.

## Step 2: read the right files (in this order)

1. Root README, CLAUDE.md / AGENTS.md, and `docs/` overviews: the founders' own description, which is *reported*, not verified.
2. Each unit's README and manifest description.
3. Schema files: entities reveal the real product (creators, members, bookings, payouts, subscriptions…).
4. Route trees: user-facing surfaces and admin tools. Group routes by role.
5. Payment and pricing code: fee constants, plan definitions, checkout and payout flows. This is the **revenue-mechanics evidence**.
6. Integrations: payments, auth, messaging, media and AI providers. These show dependencies and costs.
7. Deployment config and external hosts: candidate production domains.
8. Git log per unit: activity and recency separate *active* from *abandoned* work.
9. Planning docs (roadmaps, specs, reconnaissance notes): these are **planned/proposed** unless the code shows otherwise.

## Step 3: classify status (per product and per major feature)

| Status | Required evidence |
|---|---|
| `live` | Built **and** deployed and used: a reachable production URL (check with `curl -I`), an app-store listing, analytics or payment records, or founder confirmation recorded as `reported` |
| `built` | Implemented end to end in code (routes + data model + business logic), tests or recent commits, but no deployment or usage evidence |
| `in-development` | Partial implementation: some routes or schema exist, with TODOs, mocks or recent active commits |
| `planned` | Only in docs, roadmaps, issues or planning notes |
| `proposed` | Mentioned as an idea, with no plan |
| `unknown` | Conflicting or insufficient evidence. Ask the founder |

Rules:
- A route list is not a product. Name the **user job** each surface serves.
- Mock data, hard-coded fixtures or "coming soon" text in a UI mean the product is not live, even if the page renders.
- When docs and code disagree, the code wins for "what exists", and the founder decides "what's live". Record both.

## Step 4: product map (write to `startup-profile/products.md`)

```markdown
## <Product name>
- **Purpose:** <user job in one sentence>
- **Users / roles:** <from role enums and routes>
- **Key capabilities:** <3–6 bullets, each with a file reference>
- **Revenue mechanics:** <fees, plans, payouts, with code references> [E-…]
- **Integrations:** <providers>
- **Dependencies:** <other products and services it relies on>
- **Status:** built [E-…] (live pending deployment confirmation)
- **Open questions for founder:** <list>
```

## Step 5: ecosystem view

For multi-product companies:

- draw the dependency graph (shared identity, payments, data);
- identify the **wedge** product (the most evidence of use) and the expansion path;
- use a `diagram` slide for architecture and a `products` slide for the product map. Statuses must be visible on both.

## Privacy and safety

- Never open `.env*`, key files or credential files. The scanner skips them.
- Never copy secrets, API keys, customer personal data or private URLs with tokens into outputs.
- Keep analysis of private repositories in `outputs/` (gitignored), never in public examples.
