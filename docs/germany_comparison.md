# Germany comparison

The UK pipeline would not transfer unchanged to Germany. The discovery and
matching stages are reusable, but the target identifier and population source
are different enough to require a new feasibility phase.

## Identifier model

| Identifier | Purpose | Coverage |
|---|---|---|
| Handelsregister number | Company registration | Registered companies |
| Steuernummer | Domestic tax and invoicing | Taxpayers |
| USt-IdNr | EU cross-border VAT | Only businesses that need it |

The closest analogue to a UK VAT number is the USt-IdNr. Not every German
company has one, so "no evidence found" can be the correct outcome rather than
a discovery failure. A German project would need to define its target identifier
and eligible population before choosing sources or metrics.

## Population acquisition is the main blocker

The UK POC used a free, dated Companies House bulk snapshot. The German
Handelsregister is free to search one company at a time, but its terms restrict
automated bulk access. The open bulk data identified during research was old and
third-party rather than a current official source.

A German version would therefore need a commercial data licence or a different,
smaller population-acquisition strategy. That is a feasibility question before
the rest of the pipeline is built.

## What could transfer

HTML extraction, provenance storage, entity matching, conflict handling, and
the candidate-versus-verified decision model could transfer with changes to the
identifier patterns (`USt-IdNr` / `DE` prefix) and source adapters. VIES may be
a more accessible verifier for German VAT IDs, but this project did not test it;
it should be validated early rather than assumed to remove the UK HMRC blocker.
