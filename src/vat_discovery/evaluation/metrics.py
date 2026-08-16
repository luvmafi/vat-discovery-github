from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FunnelMetrics:
    companies_sampled: int
    companies_processed: int
    websites_discovered: int
    candidates_found: int
    verified_candidates: int
    correctly_matched_vats: int

    def rate(self, numerator: int, denominator: int) -> float | None:
        return numerator / denominator if denominator else None

    @property
    def website_discovery_rate(self) -> float | None:
        return self.rate(self.websites_discovered, self.companies_processed)

    @property
    def high_confidence_observed_coverage(self) -> float | None:
        return self.rate(self.correctly_matched_vats, self.companies_processed)
