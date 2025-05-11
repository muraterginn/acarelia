# acarelia/common/utils.py

import logging
import json

logger = logging.getLogger("common")

def parse_message(body: bytes) -> dict:
    """
    Kuyruktan gelen JSON mesajı decode edip dict’e çevirir.
    """
    try:
        return json.loads(body.decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to parse message: {e}")
        raise

def to_json_bytes(obj) -> bytes:
    """
    Pydantic model veya dict’i JSON bytes’a çevirir.
    """
    if hasattr(obj, "dict"):
        data = obj.dict()
    else:
        data = obj
    return json.dumps(data).encode("utf-8")
