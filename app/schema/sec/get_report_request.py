from pydantic import BaseModel


class GetReportRequest(BaseModel):
    report_type: str
    companies: list[str]
