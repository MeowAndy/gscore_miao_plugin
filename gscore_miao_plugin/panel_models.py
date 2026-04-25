from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PanelResult:
    source: str
    uid: str
    raw: Dict[str, Any]
    nickname: str = ""
    level: Optional[int] = None
    signature: str = ""
    avatars: Optional[List[Dict[str, Any]]] = None
    characters: Optional[List[Dict[str, Any]]] = None
    game: str = "gs"


class PanelSourceError(RuntimeError):
    def __init__(self, source: str, message: str):
        super().__init__(message)
        self.source = source
        self.message = message


class BasePanelSource:
    source_name = "base"

    async def fetch(self, uid: str) -> PanelResult:
        raise NotImplementedError
