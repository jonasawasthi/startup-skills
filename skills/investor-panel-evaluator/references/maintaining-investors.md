# Maintaining investor profiles

Investor profiles are the only place this skill learns anything about a real person. Each one is a sourced, dated file that follows the [profile schema](investor-profile-schema.md). The shipped library is `skills/investor-panel-evaluator/investors/`, one file per person, indexed in [investors/README.md](../investors/README.md).

Research follows the [investor-fit protocol](../../../knowledge/frameworks/investor-fit.md) and fundraising-strategist's [investor research](../../fundraising-strategist/references/investor-research.md) rules: public, professional information only; primary sources first; stated thesis separate from observed behaviour; dates on everything.

## Adding an investor

1. **Confirm identity.** Find the person's programme appearances and main ventures from primary sources (broadcaster pages, their company's site, their own site or book). Rule out namesakes. Choose the `id`: a lowercase slug of the public name, for example `example-investor`.
2. **Copy the template.** Copy [the template](../assets/templates/investor-profile.md) to `investors/<id>.md`.
3. **Collect sources.** At least two, ideally six or more. Open each page and read the claim there before citing it (`verification: read-at-source`). If you can only confirm that the URL and title exist (for example behind a paywall), use `url-verified`, and do not rest any fact on that source alone. Record the page's `title` as the headline a reader sees on the page (not the browser-tab text if that differs), plus the publisher, type, publication date and access date. Prefer `own-statement`, `official-bio`, `broadcaster`, `company` and `filing` sources. When one page mixes types (for example broadcaster text with an interview inside it), type the source by the claim it supports, and say so in its `note` ("interview section; the rest of the page is broadcaster text"); if it supports claims of both kinds, cite it twice with two ids. Use `reference` sources (encyclopaedias, aggregators) only to find primary ones.
4. **Write the facts.** Fill `programmes` (seasons, role, `panel_status`, `status_checked`), `business_background`, `major_ventures`, `documented_expertise`, `documented_philosophy` and `investment_history`. Every entry cites a `read-at-source` source that is not a `reference`. Paraphrase; never store a quotation. Mark philosophy `stated` (the person's own words or an interview) or `observed` (documented behaviour). A deal agreed on television is `televised`, never an investment, until a later source confirms completion.
5. **Write known gaps.** List domains common in pitches (hardware, regulated finance, health, software, retail, food) for which the record shows no operating or investing experience. Write them as industries or domains, not as dimensions; evaluators apply a gap to points whose judgement depends on that domain ([individual evaluation](individual-evaluation.md#procedure)).
6. **Write the lenses.** One to six. Each one:
   - starts its `interpretation` with "Analytical interpretation:" and says what the record suggests the person *examines*, never how they behave;
   - lists `derived_from` (existing `P` or `X` ids), the `dimensions` it covers, `attracted_by`, `concerned_by` and `evidence_demanded`;
   - has a `decline_pattern` only when the lens reaches two or more distinct sources and those sources document the person declining for that reason.
   Name the lens by its subject rather than by a country where the record allows ("reach beyond the home market", not "expansion beyond <country>"), so that evaluators can apply it to a startup in any market. When the record is specific to one market, keep the country in the interpretation and let the label carry the subject.
   Two lenses of the same person should cover different dimensions or demand different evidence. A lens that would fit every investor is not a lens.
7. **Set the emphasis.** Map each dimension the person's record clearly prioritises to the lens that lists it: at most four `primary`, any number of `secondary`.
8. **Set the confidence** from the minimums in the [schema](investor-profile-schema.md#confidence). Do not declare `high` when the person's stated views rest only on statements more than five years old, even if the counts are met; add a recent interview or declare `medium`. Then write a `confidence_rationale` of at least 15 words that says what rests on primary sources and what could not be confirmed.
9. **Write the body:** summary, panel membership and notes for maintainers, each claim cited `[S1]`.
10. **Validate:** `"$TK/bin/startup-kit" shark-tank profiles`. Fix every error. Check the profile's lenses with `shark-tank profiles --id <id>`.
11. **Review by reading** (reviewer item P12 in [guards](guards.md)): every paraphrase fairly represents its source, every lens is a reasonable reading and not a caricature, and nothing personal is present.
12. **Index it** in `investors/README.md`.

## Updating an investor

Update when a new season is announced, a person joins or leaves a panel, or a major venture changes.

1. Re-open the source that changed, or add a new source with the next `S#` id. Never renumber existing ids.
2. Change only the affected entries. For a panel change, update `panel_status`, `status_note`, `status_checked` and the sources of that `programmes` entry. A person who leaves stays in the library as `former`.
3. If a lens no longer reflects the record, revise it. Keep its id if it covers the same ground; give a new id if it is new.
4. Set `last_verified` to the date every source was last checked. Only set it if you re-checked all of them; otherwise leave it and note what was checked under "Notes for maintainers".
5. Validate and review as when adding.
6. Existing evaluations keep the profile date they were written with (it is in their simulation label). Re-run them if the change affects a lens they used.

## Verifying an investor

Verify every profile at least once every 12 months. Profiles older than 18 months are treated as one confidence level lower, and `shark-tank profiles` warns about them.

1. Run `shark-tank profiles` and note the warnings and each profile's effective confidence. Use `--today <YYYY-MM-DD>` to see which profiles will become stale by a given date.
2. Open every source. Check that the URL resolves, the headline still matches `title`, and the claim is still there.
3. Run the link checker, `python3 scripts/check_links.py`. It covers the investor library: it fetches each source URL and compares `title` with the page's HTML title or its published headline (`og:title`), so either form passes. A mismatch usually means the page moved or was rewritten; re-read it before changing anything.
4. For a source that has moved, update the URL. For one that has disappeared, cite an Internet Archive copy and say so in `note`, or remove the facts that rested on it.
5. Re-check every `programmes` entry against the latest season.
6. Update `accessed` on each source, then `last_verified`. Validate.

## A requested person has no profile

If a user asks for a well-known person who has no profile, do not research and write a profile inside the same request unless the user explicitly asks for that. Say there is no profile, and offer either an archetype ([individual evaluation](individual-evaluation.md#archetypes)) or the steps above. A new profile goes in the shipped library (`investors/`) when it is a contribution to the repository, and otherwise in a private library passed with `--library` (below).

## Adding an investor from outside the television programmes

The same schema works for any investor with a public, professional record, such as an angel investor who has published their thesis, or a fund partner.

- Set `kind: independent-investor`. `programmes` may be empty.
- The same minimums apply: at least two `read-at-source` sources, with identity sourced.
- Only people with a public investing or business record. Never profile a private individual, a founder's acquaintance, or anyone whose information is not public and professional.
- The simulation for an independent investor is still a simulation. For a real fundraising decision about that person, hand off to fundraising-strategist ([integration](integration.md)).

## Keeping a private library

A user may want profiles that should not be committed (for example investors relevant to one startup).

1. Put them in a gitignored folder, for example `outputs/<startup>/shark-tank/investors/`.
2. Use the same schema and template.
3. Pass the folder to every command that reads profiles: `shark-tank profiles --library <dir>`, `queue … --library <dir>`, `check … --library <dir>`. `--library` may be repeated.
4. An `id` in a private library must not equal an `id` in the shipped library.
5. Never copy a private profile into the shipped library without the same review as a new profile.

## When a profile cannot meet the minimum

If a person's public record cannot meet the `low` minimum (two `read-at-source` sources with identity and panel status sourced):

1. Do not write the profile. A thin profile would make the simulation invent the rest.
2. List the person in the index's "not profiled" section with the date and the reason (for example "only one source found that could be read").
3. In the meantime, offer an archetype ([individual evaluation](individual-evaluation.md#archetypes)). An archetype is never a panel member: it can be evaluated alongside a panel as a separate document, never inside it. Name it by type, never by the person.
4. Try again when new primary sources appear, such as a new season's broadcaster biographies.
