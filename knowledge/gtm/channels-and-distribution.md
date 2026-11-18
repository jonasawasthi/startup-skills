---
title: Channels, product-channel fit and founder-led acquisition
source: Brian Balfour; Paul Graham; Y Combinator; HubSpot
urls:
  - https://brianbalfour.com/four-fits-growth-framework
  - https://brianbalfour.com/essays/product-channel-fit-for-growth
  - https://www.paulgraham.com/ds.html
  - https://www.ycombinator.com/library/Ip-how-to-get-your-first-customers
  - https://www.ycombinator.com/library/Mo-the-sales-playbook-for-founders
  - https://www.ycombinator.com/library/ND-how-to-get-your-first-users
  - https://www.hubspot.com/inbound-marketing
sources:
  - {title: "Four Fits For $100M+ Growth", url: "https://brianbalfour.com/four-fits-growth-framework", author: Brian Balfour, verification: read-at-source}
  - {title: "Product Channel Fit Will Make or Break Your Growth Strategy", url: "https://brianbalfour.com/essays/product-channel-fit-for-growth", author: Brian Balfour, published: 2017-07-12, verification: read-at-source}
  - {title: "Do Things that Don't Scale", url: "https://www.paulgraham.com/ds.html", author: Paul Graham, published: 2013-07, verification: url-verified}
  - {title: "How to get your first customers", url: "https://www.ycombinator.com/library/Ip-how-to-get-your-first-customers", author: Gustaf Alströmer, published: 2022-12-29, verification: url-verified (description read)}
  - {title: "The Sales Playbook For Founders", url: "https://www.ycombinator.com/library/Mo-the-sales-playbook-for-founders", author: Tom Blomfield, published: 2025-08-15, verification: url-verified (description read)}
  - {title: "How To Get Your First Users", url: "https://www.ycombinator.com/library/ND-how-to-get-your-first-users", author: Ankit Gupta, published: 2026-01-14, verification: url-verified (description read)}
  - {title: "What Is Inbound Marketing?", url: "https://www.hubspot.com/inbound-marketing", author: HubSpot, verification: url-verified}
authors: [Brian Balfour, Paul Graham, Gustaf Alströmer, Tom Blomfield, Ankit Gupta, HubSpot]
date_checked: 2026-11-07
type: attributed-summary + original-analysis
verification: read-at-source (Balfour essays); url-verified (others)
related_skills: [gtm-strategy-maker, startup-idea-evaluator]
---

# Channels and distribution

## Attributed

- **Four fits (Balfour).** Growth needs four fits to hold together: market–product, product–channel, channel–model and model–market. Channels and the business model constrain each other. A low price point cannot pay for an expensive channel. Balfour plots this as an ARPU-to-CAC spectrum.
- **Product–channel fit (Balfour, 2017).** Channels have rules the startup does not set, so products are built to fit channels, not the reverse. Distribution tends to follow a power law: at any one time a company with product–channel fit usually gets most of its growth from one channel. Balfour advises focusing on one or two channels early, and warns that channels can break, as when a platform shuts down an API.
- **Do things that don't scale (Graham, 2013).** Early users are recruited by hand, and founders make the company take off rather than waiting for a channel to do it.
- **YC on first customers and sales.** Alströmer (2022) gives tactical advice on getting the first customers. Blomfield (2025) describes running a tight founder-led sales process that lands recurring revenue. Gupta (2026) argues that early products should be able to adapt to the needs of their first customers.
- **Inbound (HubSpot).** Inbound marketing attracts customers with useful content and experiences instead of interrupting them. It compounds slowly and depends on consistent output.

## Channel evaluation (original synthesis)

Each candidate channel is scored from 1 to 5 on six criteria. The GTM engine (`startup-kit gtm analyze`) does the arithmetic and refuses scores that have no rationale:

| Criterion | Question | Default weight |
|---|---|---|
| Customer fit | Is the ICP actually reachable here, and do they trust it? | 0.25 |
| Economics | Can the price and margin pay for this channel's likely CAC? | 0.20 |
| Speed to signal | How fast will a small test produce a readable result? | 0.15 |
| Resource fit | Can this team run it now (skills, hours, cash)? | 0.15 |
| Scalability | Will it still work at ten times the volume? | 0.10 |
| Evidence | *Computed* from the cited ledger entries, never self-assessed | 0.15 |

Rules:

- **Recommend at most three primary channels** (the default). Others become "test later" or "not now", each with a reason.
- **Model guards**: outbound sales to low-price consumers, paid ads before any retention evidence, referral programmes before there is an active user base, and PLG without a self-serve product all trigger warnings.
- **Each primary channel needs** a fit rationale, execution steps, resources, cost considerations, leading indicators, success metrics, risks, and an experiment with a budget, duration, metric, threshold and kill criterion.

## Channel notes

| Channel | Usually fits | Watch out for |
|---|---|---|
| Founder-led sales | B2B, high-touch, supply side of marketplaces, early creators | Doesn't scale; record every conversation as evidence |
| Outbound / direct sales | ACV that can pay for sales time | Consumer price points can't pay for it |
| Content / SEO | Problems people search for; long horizons | 3–9 months to signal; hard to attribute |
| Social media | Visual or creator products, consumer | Algorithm dependence |
| Community-led | Practitioners who learn from peers | Slow; needs a host |
| Referral | Products with an active, satisfied base | Can't create satisfaction, only amplify it |
| Partnerships | Trusted intermediaries own the customer | Long sales cycles; misaligned incentives |
| Influencer / creator | Consumer, education, creator platforms | Audience fit beats audience size; disclose paid promotion |
| Email | Owned audiences, waitlists, lifecycle | List quality and consent |
| Paid advertising | Transactional, measurable conversion, proven retention | Buys churn before PMF |
| Affiliate | Margin to share; trackable conversion | Fraud; brand control |
| Product-led | Self-serve, fast time to value | Needs instrumented onboarding |
| Developer-led | Developer tools, APIs | Docs and DX are the channel |
| PR | A genuine story or milestone | Spikes without retention |
| Events / offline | Dense local communities, trust-based markets | Cost per contact; follow-up discipline |
