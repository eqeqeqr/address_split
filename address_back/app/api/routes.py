from pathlib import Path
import json

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.config import DEFAULT_SAMPLE_SIZE, UPLOAD_DIR
from app.schemas.address import (
    AddressSplitRequest,
    ColumnMode,
    ColumnSchemaResponse,
    ExcelInspectResponse,
    RedisConfigPayload,
    RedisConfigResponse,
    RedisTestResponse,
    SceneRulePayload,
    SceneRuleResponse,
    SplitJobResponse,
    SplitRecordResponse,
    SplitResultDetailResponse,
)
from app.services.constants import (
    DEFAULT_SCENE_FIELDS,
    LEVEL8_FIELDS,
    LEVEL11_FIELDS,
    LEVEL_DESCRIPTIONS,
    RAW_FIELDS,
    SCENE_FIELD_OPTIONS,
)
from app.services.scene_service import create_scene_rule, delete_scene_rule, list_scene_rules, update_scene_rule
from app.services.environment_config import get_redis_config, save_redis_config
from app.services.redis_store import reset_redis_connection, test_connection
from app.services.split_service import (
    get_cached_job,
    delete_job,
    get_job,
    inspect_excel_file,
    list_jobs,
    read_result_rows,
    split_addresses,
    split_excel_file,
)
from app.services.job_store import build_cache_key

router = APIRouter(prefix="/api")


def _parse_raw_fields(raw_fields: str | None) -> list[str] | None:
    if not raw_fields:
        return None

    try:
        value = json.loads(raw_fields)
    except json.JSONDecodeError:
        value = [item.strip() for item in raw_fields.split(",") if item.strip()]

    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise HTTPException(status_code=400, detail="raw_fields 必须是字符串数组")

    return value


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/schemas", response_model=ColumnSchemaResponse)
def get_schemas() -> ColumnSchemaResponse:
    return ColumnSchemaResponse(
        raw_fields=RAW_FIELDS,
        level8_fields=LEVEL8_FIELDS,
        level11_fields=LEVEL11_FIELDS,
        level_descriptions=LEVEL_DESCRIPTIONS,
        default_scene_fields={key.value: value for key, value in DEFAULT_SCENE_FIELDS.items()},
        scene_field_options={key.value: value for key, value in SCENE_FIELD_OPTIONS.items()},
    )


@router.get("/environment/redis", response_model=RedisConfigResponse)
def read_redis_environment() -> RedisConfigResponse:
    return get_redis_config()


@router.put("/environment/redis", response_model=RedisConfigResponse)
def update_redis_environment(payload: RedisConfigPayload) -> RedisConfigResponse:
    result = save_redis_config(payload)
    reset_redis_connection()
    return result


@router.post("/environment/redis/test", response_model=RedisTestResponse)
def test_redis_environment(payload: RedisConfigPayload) -> RedisTestResponse:
    ok, message = test_connection(payload.model_dump())
    return RedisTestResponse(ok=ok, message=message)


@router.post("/excels/inspect", response_model=ExcelInspectResponse)
async def inspect_excel(file: UploadFile = File(...)) -> ExcelInspectResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 或 .xls 文件")

    upload_path = UPLOAD_DIR / f"inspect_{Path(file.filename or 'upload.xlsx').stem}_{id(file)}{suffix}"
    upload_path.write_bytes(await file.read())

    try:
        result = inspect_excel_file(upload_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Excel 检测失败：{exc}") from exc
    finally:
        if upload_path.exists():
            upload_path.unlink()

    return ExcelInspectResponse(
        filename=file.filename or upload_path.name,
        total_rows=result["total_rows"],
        address_rows=result["address_rows"],
        address_column=result["address_column"],
        columns=result["columns"],
    )


@router.get("/scenes", response_model=list[SceneRuleResponse])
def get_scenes() -> list[SceneRuleResponse]:
    return list_scene_rules()


@router.post("/scenes", response_model=SceneRuleResponse)
def create_scene(payload: SceneRulePayload) -> SceneRuleResponse:
    try:
        return create_scene_rule(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/scenes/{rule_id}", response_model=SceneRuleResponse)
def update_scene(rule_id: str, payload: SceneRulePayload) -> SceneRuleResponse:
    try:
        rule = update_scene_rule(rule_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if rule is None:
        raise HTTPException(status_code=404, detail="场景规则不存在")
    return rule


@router.delete("/scenes/{rule_id}")
def delete_scene(rule_id: str) -> dict[str, bool]:
    try:
        deleted = delete_scene_rule(rule_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="场景规则不存在")
    return {"deleted": True}


@router.post("/splits", response_model=SplitJobResponse)
async def create_split(
    file: UploadFile = File(...),
    column_mode: ColumnMode = Form(ColumnMode.level11),
    scene_field: str | None = Form(None),
    sample_size: int = Form(DEFAULT_SAMPLE_SIZE),
    raw_fields: str | None = Form(None),
) -> SplitJobResponse:
    if sample_size <= 0:
        raise HTTPException(status_code=400, detail="sample_size 必须大于 0")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 或 .xls 文件")

    filename = file.filename or "upload.xlsx"
    cache_key = build_cache_key(filename, sample_size)
    cached_job = get_cached_job(cache_key)
    if cached_job is not None:
        preview_rows, _ = read_result_rows(cached_job, page=1, page_size=20)
        return SplitJobResponse(
            job_id=cached_job.job_id,
            status=cached_job.status,
            column_mode=cached_job.column_mode,
            scene_field=cached_job.scene_field,
            total_rows=cached_job.total_rows,
            processed_rows=cached_job.processed_rows,
            columns=cached_job.columns,
            preview=preview_rows,
            download_url=f"/api/splits/{cached_job.job_id}/download",
        )

    upload_path = UPLOAD_DIR / f"{Path(file.filename or 'upload.xlsx').stem}_{id(file)}{suffix}"
    upload_path.write_bytes(await file.read())

    try:
        job_id, result_df, detail = split_excel_file(
            upload_path,
            column_mode,
            scene_field,
            sample_size,
            _parse_raw_fields(raw_fields),
            filename,
            cache_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"地址拆分失败：{exc}") from exc

    return SplitJobResponse(
        job_id=job_id,
        status=detail.status,
        column_mode=detail.column_mode,
        scene_field=detail.scene_field,
        total_rows=detail.total_rows,
        processed_rows=detail.processed_rows,
        columns=detail.columns,
        preview=result_df.head(20).fillna("").to_dict(orient="records"),
        download_url=f"/api/splits/{job_id}/download",
    )


@router.get("/splits", response_model=list[SplitRecordResponse])
def list_splits() -> list[SplitRecordResponse]:
    records: list[SplitRecordResponse] = []
    for job in list_jobs():
        records.append(
            SplitRecordResponse(
                id=job.job_id,
                taskName=job.task_name or job.job_id,
                source=job.source,
                total=job.total_rows,
                success=job.success_rows,
                failed=job.failed_rows,
                status="success" if job.status.value == "completed" else "partial",
                startedAt=job.created_at,
                columnMode=job.column_mode,
                sceneField=job.scene_field,
                downloadUrl=f"/api/splits/{job.job_id}/download",
            )
        )

    return records


@router.post("/splits/text", response_model=SplitJobResponse)
def create_text_split(payload: AddressSplitRequest) -> SplitJobResponse:
    try:
        job_id, result_df, detail = split_addresses(
            payload.addresses,
            payload.column_mode,
            payload.scene_field,
            payload.raw_fields,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"地址拆分失败：{exc}") from exc

    return SplitJobResponse(
        job_id=job_id,
        status=detail.status,
        column_mode=detail.column_mode,
        scene_field=detail.scene_field,
        total_rows=detail.total_rows,
        processed_rows=detail.processed_rows,
        columns=detail.columns,
        preview=result_df.head(20).fillna("").to_dict(orient="records"),
        download_url=f"/api/splits/{job_id}/download",
    )


@router.get("/splits/{job_id}")
def get_split(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job


@router.get("/splits/{job_id}/result", response_model=SplitResultDetailResponse)
def get_split_result(
    job_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=1000),
) -> SplitResultDetailResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    rows, row_total = read_result_rows(job, page=page, page_size=page_size)
    total = job.total_rows
    success = job.success_rows
    failed = job.failed_rows
    processed = job.processed_rows
    success_rate = f"{(success / processed * 100):.2f}%" if processed else "0.00%"

    return SplitResultDetailResponse(
        stats={
            "total": f"{total:,}",
            "success": f"{success:,}",
            "failed": f"{failed:,}",
            "successRate": success_rate,
        },
        rows=rows[:200],
        columns=job.columns,
        columnMode=job.column_mode,
        sceneField=job.scene_field,
        failedRows=[],
        downloadUrl=f"/api/splits/{job.job_id}/download",
        page=page,
        pageSize=page_size,
        totalRows=row_total,
    )


@router.get("/splits/{job_id}/download")
def download_split(job_id: str) -> FileResponse:
    job = get_job(job_id)
    if job is None or not job.result_file:
        raise HTTPException(status_code=404, detail="结果文件不存在")

    result_file = Path(job.result_file)
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="结果文件不存在")

    return FileResponse(
        result_file,
        filename=f"address_split_{job_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.delete("/splits/{job_id}")
def delete_split(job_id: str) -> dict[str, bool]:
    deleted = delete_job(job_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"deleted": True}
