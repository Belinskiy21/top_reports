from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SecReportRequest:
    report_type: str
    public_base_url: str
    created_by: int
    temp_path: Path
