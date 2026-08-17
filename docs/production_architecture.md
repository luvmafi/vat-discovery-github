# Production architecture

This is the smallest production shape suggested by the POC. It keeps the
evidence and verification rules intact, while replacing the manual parts that
would not work at a 40,000-supplier scale.

## Pipeline

```
Companies House snapshot
        |
   ingest and sample
        |
   discover candidate websites
        |
   fetch and retain source evidence
        |
   extract and normalise VAT candidates
        |
   authoritative VAT verification
        |
   entity-resolution score and decision
        |
   TIER_1: reportable row | TIER_2/3: review queue
```

Every candidate should keep its raw text, source URL, document hash, parser
version, verification response, and entity-match explanation. The checksum is
a useful signal, but it is not proof that a VAT number is valid or belongs to a
company.

## What must change before scaling

| Area | POC approach | Production change |
|---|---|---|
| Population and sampling | Python data structures held the 5.19M-company population in memory. | Stream input or load directly into a database once memory becomes the constraint. |
| Discovery | Agent-mediated search and fetches. | Implement `SearchProvider`, cache results, throttle by domain, and respect source terms and robots rules. |
| Verification | HMRC Sandbox only. | Obtain production credentials and preserve each verification response with its timestamp. |
| Review | Human re-checking of every promising case. | Route TIER_2 and conflicting cases to a review workflow; do not auto-accept them. |

The current architecture already separates these responsibilities. The key gap
is operational: the discovery adapter and review workflow have not yet been run
at volume, and HMRC production access is still missing.

## Controls worth monitoring

| Signal | Why it matters |
|---|---|
| Source-to-candidate rate | A large drop from the observed 4–6% baseline may signal a broken discovery source or a change in the population. |
| Claims rejected after source fetch | Search summaries generated several incorrect leads in the POC; this should be measured for every batch. |
| Checksum disagreement | A real checksum bug was found during the pilot, so changes to this code need regression data from verified records. |
| Verification age and company status | VAT registration, company status, and addresses can change after a record is created. |
| Website availability | One plausible site disappeared between checks; a confirmed source becoming unreachable should trigger a re-check. |

## Refresh approach

Use a quarterly Companies House refresh as the default. Re-check verified VAT
records through the verifier on the same cycle, and handle unreachable source
websites sooner when they affect an existing result. The POC has not yet
measured a real re-verification cycle, so this is an initial operating policy,
not a validated SLA.

## Boundaries of this POC

The 5.19M-row ingestion was exercised, but discovery was not: only about 160
companies were tested for website evidence. Costs at scale are modelled from
observed request ratios and published prices, not measured production costs.
See [economics.md](economics.md) and [findings.md](findings.md) for the basis.
