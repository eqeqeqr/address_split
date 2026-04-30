from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ColumnMode(StrEnum):
    level8 = "level8"
    level11 = "level11"
    raw = "raw"


class SplitJobStatus(StrEnum):
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class SplitJobResponse(BaseModel):
    job_id: str
    status: SplitJobStatus
    column_mode: ColumnMode
    scene_field: str
    total_rows: int
    processed_rows: int
    columns: list[str]
    preview: list[dict[str, Any]]
    download_url: str


class ExcelInspectResponse(BaseModel):
    filename: str
    total_rows: int
    address_rows: int
    address_column: str
    columns: list[str]


class SplitJobDetail(BaseModel):
    job_id: str
    status: SplitJobStatus
    column_mode: ColumnMode
    scene_field: str
    total_rows: int
    processed_rows: int
    columns: list[str]
    task_name: str = ""
    source: str = ""
    success_rows: int = 0
    failed_rows: int = 0
    created_at: str = ""
    raw_fields: list[str] | None = None
    result_file: str | None = None
    cache_key: str | None = None
    error: str | None = None


class SplitRecordResponse(BaseModel):
    id: str
    taskName: str
    source: str
    total: int
    success: int
    failed: int
    status: str
    startedAt: str
    columnMode: ColumnMode
    splitScheme: str
    sceneField: str
    downloadUrl: str


class SplitResultDetailResponse(BaseModel):
    stats: dict[str, str]
    rows: list[dict[str, Any]]
    columns: list[str]
    columnMode: ColumnMode
    sceneField: str
    failedRows: list[dict[str, Any]]
    downloadUrl: str
    page: int = 1
    pageSize: int = 200
    totalRows: int = 0


class ColumnSchemaResponse(BaseModel):
    raw_fields: list[str]
    level8_fields: list[str]
    level11_fields: list[str]
    level_descriptions: dict[str, str]
    default_scene_fields: dict[str, str]
    scene_field_options: dict[str, list[str]]


class AddressSplitRequest(BaseModel):
    addresses: list[str] = Field(min_length=1)
    column_mode: ColumnMode = ColumnMode.level11
    scene_field: str | None = None
    raw_fields: list[str] | None = None
    client_job_id: str | None = None


class SceneRuleResponse(BaseModel):
    id: str
    name: str
    pattern: str
    matchField: str = "level_7 / poi"
    priority: int
    statusText: str
    editable: bool


class SceneRulePayload(BaseModel):
    name: str = Field(min_length=1)
    pattern: str = Field(min_length=1)
    matchField: str = "level_7 / poi"
    priority: int = Field(ge=1)

    @field_validator("matchField")
    @classmethod
    def validate_match_field(cls, value: str) -> str:
        raw_fields = {"poi", "subpoi", "redundant", "others"}
        normalized = value.strip()
        if normalized == "level_7":
            return "level_7 / poi"
        if normalized in raw_fields:
            return f"level_7 / {normalized}"
        if normalized.startswith("level_7 / "):
            raw_field = normalized.split("/", 1)[1].strip()
            if raw_field in raw_fields:
                return f"level_7 / {raw_field}"
        raise ValueError("识别字段必须包含 level_7，并选择 poi、subpoi、redundant、others 之一作为原始字段")


class RedisConfigPayload(BaseModel):
    mode: str = "local"
    host: str = Field(default="127.0.0.1", min_length=1)
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0)
    password: str = ""


class RedisConfigResponse(RedisConfigPayload):
    updatedAt: str = ""


class RedisTestResponse(BaseModel):
    ok: bool
    message: str
