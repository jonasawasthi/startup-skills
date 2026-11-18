---
title: Payment infrastructure and settlement dependencies
source: Stripe; Nepal Rastra Bank; Fonepay; Nepal Clearing House; The Kathmandu Post
urls:
  - https://stripe.com/global
  - https://docs.stripe.com/connect/charges
  - https://docs.stripe.com/connect/marketplace
  - https://docs.stripe.com/payouts
  - https://www.nrb.org.np/departments/psd/
  - https://nchl.com.np/
  - https://fonepay.com/blogs/upi-in-nepal
  - https://f1soft.com/corporate-news/fonepay-npci-international-over-million-upi-transactions
  - https://kathmandupost.com/money/2026/05/09/two-years-on-nepalis-still-unable-to-scan-and-pay-in-india
sources:
  - {title: "Stripe global availability", url: "https://stripe.com/global", author: Stripe, verification: read-at-source (country list read 2026-11-08)}
  - {title: "Understand how charges work in a Connect integration", url: "https://docs.stripe.com/connect/charges", author: Stripe, verification: read-at-source}
  - {title: "Build a marketplace", url: "https://docs.stripe.com/connect/marketplace", author: Stripe, verification: url-verified}
  - {title: "Receive payouts from Stripe", url: "https://docs.stripe.com/payouts", author: Stripe, verification: url-verified}
  - {title: "Payment Systems Department - the official site of the Central Bank of Nepal", url: "https://www.nrb.org.np/departments/psd/", author: Nepal Rastra Bank, verification: read-at-source}
  - {title: "Homepage - Nepal Clearing House Limited", url: "https://nchl.com.np/", author: Nepal Clearing House Limited, verification: url-verified}
  - {title: "UPI in Nepal: Seamless Cross-Border Payments via Fonepay", url: "https://fonepay.com/blogs/upi-in-nepal", author: Fonepay, published: 2025-05-21, verification: read-at-source}
  - {title: "Fonepay and NPCI International Mark Over 1 Million UPI Transactions in Nepal", url: "https://f1soft.com/corporate-news/fonepay-npci-international-over-million-upi-transactions", author: F1Soft, verification: url-verified}
  - {title: "Two years on, Nepalis still unable to scan and pay in India", url: "https://kathmandupost.com/money/2026/05/09/two-years-on-nepalis-still-unable-to-scan-and-pay-in-india", author: The Kathmandu Post, published: 2026-05-09, verification: url-verified (search summary only; article not read)}
authors: [Stripe, Nepal Rastra Bank, Fonepay]
date_checked: 2026-11-08
type: attributed-summary + original-analysis
verification: read-at-source (Stripe global, Stripe Connect charges, NRB PSD, Fonepay UPI); url-verified (others)
related_skills: [business-model-designer, gtm-strategy-maker, startup-research]
---

# Payment infrastructure and settlement dependencies

See also: [emerging markets framework](../frameworks/emerging-markets.md), [marketplace business models](marketplace-business-models.md). **Nothing here is legal, tax or payment advice; availability and rules change. Confirm with the provider, a bank and qualified advisers.**

## Attributed

- **Stripe availability is per country of the business.** Stripe's global availability page, read on 2026-11-08, listed 51 countries and regions; Nepal was not listed, and India was marked as preview.
- **Stripe Connect charge types** (direct; destination; separate charges and transfers) decide whose balance takes payments, fees, refunds and chargebacks, and whether the platform or the seller is the business of record. They illustrate the design questions any marketplace faces, whichever provider it uses.
- **Nepal Rastra Bank's Payment Systems Department** publishes the list of licensed payment system operators (PSOs) and payment service providers (PSPs), the Payment and Settlement Act 2075, the Payment and Settlement Bylaws, and annual Integrated Payment System Directives.
- **Cross-border QR (Fonepay, 2025):** Indian users can pay Nepali merchants with UPI apps by scanning merchant QR codes **in person** (person-to-merchant), in sectors such as hospitality, retail, travel and restaurants. The page does not describe online or e-commerce checkout, or payouts to Nepali sellers. F1Soft reports over a million such transactions; the Kathmandu Post reported in May 2026 that the reverse direction (Nepalis paying in India) was still not live.

## Original synthesis: payment questions every model must answer

| Flow | Question to verify |
|---|---|
| Collection | Which licensed provider or bank collects buyers' payments for *this* entity, by which methods, at what fee? |
| Holding | Does the platform hold others' money (refund holds, escrow)? Does that need a licence or a licensed partner? |
| Payout | How are sellers paid, at what cost, with what limits and KYC? |
| Refunds and disputes | Who is debited, and how is the money recovered from the seller? |
| Cross-border | Can the entity receive foreign currency online? Can it pay sellers abroad? Under which foreign-exchange rules? |
| Tax | Is the platform seller of record? Is VAT due on the full price or on the commission? |

**Two confusions to avoid.**

1. *"Provider X works in country Y"* usually means for businesses registered in Y. A Nepal-registered company cannot assume Stripe, PayPal or international card acquiring is available.
2. *Visitors paying local merchants by QR* is not *a local platform accepting international online payments* and is not *settling creators' earnings*. The engine and document guard reject text that treats one as evidence for the other.
