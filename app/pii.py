from __future__ import annotations

import hashlib
import re

# Tu khoa dia chi VN. Giu ca dang co dau/khong dau cua tu de bat duoc du bien the,
# nhung khong dung (?i) toan cuc: "quan sat"/"phuong phap" la tu thuong gap trong
# noi dung lab, neu match khong dau + khong phan biet hoa/thuong se che sai.
_ADDRESS_KEYWORDS = "|".join(
    (
        "Số nhà", "số nhà",
        "Đường", "đường",
        "Phố", "phố",
        "Phường", "phường",
        "Quận", "quận",
        "Xã", "xã",
        "Huyện", "huyện",
        "Thị trấn", "thị trấn",
        "Thành phố", "thành phố",
        "Tỉnh", "tỉnh",
    )
)

PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    "cccd": r"\b\d{12}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    # Ho chieu VN/quoc te pho bien: 1 chu cai in hoa + 7 chu so (B1234567).
    "passport": r"\b[A-Z]\d{7}\b",
    # Dia chi VN: tu khoa hanh chinh + so nha hoac cac tu viet hoa theo sau.
    "address_vn": (
        rf"(?:{_ADDRESS_KEYWORDS})\s+"
        r"(?:\d+[A-Za-z]?(?:/\d+)*|[A-ZĐÀ-Ỹ]\w*)"
        r"(?:\s+[A-ZĐÀ-Ỹ]\w*)*"
    ),
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
