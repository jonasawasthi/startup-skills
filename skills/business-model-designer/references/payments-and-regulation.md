# Payments, geography and regulation

Background: [payment infrastructure and settlement](../../../knowledge/business-model/payment-infrastructure.md). **Nothing here is legal, tax or payment advice;** the skill's job is to list what must be confirmed and by whom.

## Every money movement is a dependency

Register a dependency for each of: collecting customer payments, paying out sellers, holding funds (refund holds, escrow), foreign currency, tax (VAT, withholding), consumer and platform obligations, and any licence. Each has:

- `status`: verified · in-progress · unverified · assumed · blocked;
- `evidence`: ledger entries (a provider contract, approval letter, live test, official page);
- `question`: the exact thing to confirm;
- `confirm_with`: legal, tax, payment-provider, bank, regulator, accountant, partner;
- `confirmed_by`: required before a regulatory, tax or legal item can be `verified`.

A revenue stream cannot reach *available* while a linked dependency is unverified.

## Never assume a provider is available

- Every provider named anywhere in the spec (Stripe, PayPal, Razorpay, Adyen, Wise, card acquiring, Visa, Mastercard, Apple Pay, Google Pay…) must appear in a dependency, or the engine reports an error.
- Availability depends on where the *business* is registered, not where its customers are. Check the provider's own country list and get written confirmation.
- Stripe's global availability page (checked 2026-11-08) does not list Nepal. A foreign-entity route is a legal and tax question, not a workaround to recommend casually.

## Nepal-specific cautions

- Domestic collection is typically through licensed payment service providers and operators (wallets, QR networks, banks) regulated by Nepal Rastra Bank's Payment Systems Department, which publishes the licensed PSO and PSP list, the Payment and Settlement Act 2075, bylaws and the annual Integrated Payment System Directives. Which channel a startup may use, and whether holding sellers' money needs a licence or a licensed partner, are questions for a lawyer and the provider.
- **Cross-border QR is not online checkout.** Since 2024, Indian UPI users can pay Nepali merchants by scanning merchant QR codes in person (Fonepay with NPCI International). This says nothing about whether a Nepali platform can accept international *online* payments from learners abroad, or pay out sellers' earnings. The engine and the document guard reject text that treats one as evidence of the other.
- Foreign-currency receipts, VAT on a seller-of-record marketplace and creator payouts each need confirmation from a bank, tax adviser and provider respectively.

## Questions to ask (template)

| To | Question |
|---|---|
| Payment provider | Can a company registered in <country> use you to collect <method> payments online? Fees, settlement time, payout limits? In writing? |
| Bank | How are payouts to many individual sellers disbursed, at what cost and with what limits? Can we receive foreign currency online? |
| Tax adviser | As seller of record, is VAT due on the whole price or on our commission? Withholding on seller payouts? |
| Lawyer / regulator | Does collecting buyers' money and holding sellers' earnings before payout require a licence or a licensed partner? |
