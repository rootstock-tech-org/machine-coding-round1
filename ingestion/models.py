"""Result types returned by the ingestion service. This file is provided."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FileResult:
    file_id: str
    ok: bool
    checksum: str | None = None  # lowercase hex sha256 of the file bytes
    error: str | None = None  # human-readable reason when ok is False


@dataclass
class Report:
    results: list[FileResult] = field(default_factory=list)

    @property
    def succeeded(self) -> list[str]:
        return [r.file_id for r in self.results if r.ok]

    @property
    def failed(self) -> dict[str, str]:
        return {r.file_id: r.error or "unknown error" for r in self.results if not r.ok}

    def checksum_of(self, file_id: str) -> str | None:
        return next((r.checksum for r in self.results if r.file_id == file_id), None)
