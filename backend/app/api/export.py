"""Export endpoints (CONTRACTS section 7)."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.export.markdown import render_markdown
from app.export.pdf import render_pdf
from app.schemas import Assessment

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportRequest(BaseModel):
    assessment: Assessment


def _headers(a: Assessment, ext: str) -> dict[str, str]:
    return {"Content-Disposition": f'attachment; filename="ai-act-assessment-{a.id[:8]}.{ext}"'}


@router.post("/markdown")
def export_markdown(body: ExportRequest, request: Request) -> Response:
    store = request.app.state.pipeline.store
    md = render_markdown(body.assessment, store)
    return Response(md.encode("utf-8"), media_type="text/markdown; charset=utf-8",
                    headers=_headers(body.assessment, "md"))


@router.post("/pdf")
def export_pdf(body: ExportRequest, request: Request) -> Response:
    store = request.app.state.pipeline.store
    return Response(render_pdf(body.assessment, store), media_type="application/pdf",
                    headers=_headers(body.assessment, "pdf"))
