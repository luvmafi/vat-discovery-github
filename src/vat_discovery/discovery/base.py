"""Interfaces only: Phase 0 deliberately includes no live search or crawler implementation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    rank: int
    retrieved_at: datetime
    provider: str


class SearchProvider(Protocol):
    def search(self, query: str) -> list[SearchResult]: ...
