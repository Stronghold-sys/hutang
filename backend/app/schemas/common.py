from typing import Generic, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel

T = TypeVar('T')


class MetaData(BaseModel):
    page: Optional[int] = None
    limit: Optional[int] = None
    total_items: Optional[int] = None
    total_pages: Optional[int] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Data berhasil diproses"
    data: Optional[T] = None
    meta: Optional[MetaData] = None


class ErrorDetail(BaseModel):
    code: str
    details: Optional[Dict[str, Any]] = None


class APIErrorResponse(BaseModel):
    success: bool = False
    message: str = "Permintaan tidak dapat diproses"
    error: ErrorDetail


import json
from datetime import date, datetime
from decimal import Decimal


def dump_model(obj: Any, **kwargs) -> Dict[str, Any]:
    if hasattr(obj, "json"):
        try:
            return json.loads(obj.json(**kwargs))
        except Exception:
            pass
    if hasattr(obj, "model_dump"):
        raw = obj.model_dump(**kwargs)
    elif hasattr(obj, "dict"):
        raw = obj.dict(**kwargs)
    else:
        raw = dict(obj)
    
    clean = {}
    for k, v in raw.items():
        if isinstance(v, (date, datetime)):
            clean[k] = v.isoformat()
        elif isinstance(v, Decimal):
            clean[k] = float(v)
        else:
            clean[k] = v
    return clean


