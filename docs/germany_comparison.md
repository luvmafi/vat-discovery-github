# Germany comparison (optional, brief section 45)

Would the UK pipeline built in this project survive an unmodified move to Germany? **No — the population-acquisition step specifically would not, and the identifier landscape is structurally different in a way that changes what "found a VAT number" even means.** Everything below is drawn from published sources checked during this session, not assumed by analogy to the UK.

## Identifier structure: not one identifier, but three

A UK company has one VAT number (if registered) and one Companies House number, and this project's whole design leans on that separation staying clean. A German company can have **three separate identifiers issued by three separate authorities**, and critically, not every company has all three:

| Identifier | Issued by | Purpose | Every company has one? |
|---|---|---|---|
| Handelsregister number (HRB/HRA) | Register courts (Registergerichte) | Company registration | Yes, for registered entities |
| Steuernummer | Local tax office (Finanzamt) | Domestic tax/invoicing | Yes |
| USt-IdNr (VAT ID) | Bundeszentralamt für Steuern (BZSt) | EU cross-border VAT | **No — only businesses engaged in intra-Community trade need one** |

This last point breaks the UK project's core assumption directly. In the UK, "does this company have a VAT number" is mostly a function of turnover threshold. In Germany, a domestic-only business below the relevant threshold may have a Steuernummer but legitimately **no USt-IdNr at all** — meaning the equivalent of this project's target identifier may not exist for a meaningful share of the population, independent of discoverability. Any German version of this project would need to decide up front whether it's targeting USt-IdNr specifically (the closest UK-VAT-number analogue) or accept that a large share of "no evidence found" results are structurally correct, not a discovery failure.

## Population acquisition: the UK's easiest step is Germany's hardest

This project's Phase 1 relied on Companies House publishing a free, monthly, bulk-downloadable snapshot with no formal reuse restriction stated. Germany's equivalent, the Handelsregister, is the opposite on every count found:

- The official portal (handelsregister.de) is free to *search* one company at a time, but its terms of use **explicitly prohibit automated bulk scraping or mass download**.
- The official bulk/company-announcement sources (Bundesanzeiger, Unternehmensregister) were described in the sources checked as having "adverse terms of use" restricting redistribution.
- The one open bulk dataset found (offeneregister.de, OpenCorporates-derived) is a third-party effort covering roughly June 2017 to January 2019 — **not current**, and not an official source this project's own "no fabrication, no unverified licence" standard (`docs/methodology.md`) would accept without further checking.

**This is the single biggest reason the UK pipeline would not survive an unmodified move to Germany**: Phase 1 of this project (a defensible, free, bulk, dated population snapshot) has no equivalent free/open path identified here. A German version would need either a paid data-licence relationship with a commercial register-data provider, or a fundamentally different, non-bulk population-acquisition strategy (e.g. sampling via the one-at-a-time portal search, which conflicts with the portal's own anti-automation terms).

## Verification: possibly *easier* than the UK, not harder

This is the one place Germany looks more favorable than the UK based on what was checked. VAT ID verification across the EU runs through VIES (VAT Information Exchange System), a Commission-operated cross-border lookup that — unlike HMRC's gated, credentialed "Check a UK VAT Number" API this project could not get access to — is described as broadly accessible for checking validity, and in some member states returns registered name/address alongside the valid/invalid result. If VIES access for German (DE-prefixed) numbers turns out to be genuinely easier to obtain than HMRC credentials, the verification bottleneck that is this UK project's single binding constraint (`docs/decision.md`) might not be the binding constraint in a German version at all — but this project did not attempt to actually call VIES, so this is a hypothesis worth testing early in any German pilot, not a confirmed advantage.

## Discovery and web evidence: untested, no reason to assume it differs

Nothing checked here suggests German company websites would be structurally more or less likely to publish a USt-IdNr in a footer than UK companies publish a VAT number — this project has no data either way, since no German company was ever searched. The extraction module (`extraction/html.py`) would need a new regex pattern set for `USt-IdNr` / `DE\d{9}` instead of `VAT` / `GB\d{9}`, which is a small, mechanical change, not a redesign.

## Legal/publication requirements and commercial data availability

Companies House data being explicitly stated as free-to-reuse statutory public information was this project's basis for treating it as usable without a formal licence document (`docs/methodology.md`, still flagged as needing written confirmation). Germany's Handelsregister terms explicitly restricting automated access means the equivalent legal footing does not exist here — a German pipeline would need either a commercial data licence (cost not modeled in this project) or a materially slower manual-search-based population strategy, which conflicts with the "reproducible, deterministic sample" standard this UK project set for itself in Phase 1.

## Bottom line

**The UK pipeline's discovery, extraction, normalization, and entity-resolution stages (Phases 2-3, 6, 8) would very likely transfer to Germany with only mechanical changes** (new regex patterns, new identifier field names). **The UK pipeline's population-acquisition and sampling strategy (Phase 1) would not transfer at all** — it depends on exactly the kind of free, bulk, terms-permissive public register access that Germany's Handelsregister explicitly does not offer. A German version of this project would need to either resolve a paid data-licensing relationship first, treat that as its own separate feasibility gate before anything else, or accept a fundamentally smaller, slower, non-bulk sampling approach. **This is not a "would the pipeline survive" question with one answer — parts of it clearly would, and the part this UK project treated as the easy first step would not.**
