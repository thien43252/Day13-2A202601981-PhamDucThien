# Notes R1 — nội dung cho mục 3 của REPORT.md (phần Logging)

> R4 dán nội dung dưới đây vào `submission/REPORT.md` mục 3. Phần trace waterfall / span
> đáng chú ý thuộc R2, R1 không viết. Xoá file này ở commit cuối (TEAMWORK.md 5.2).

## Cần sửa giúp ở mục 2 của REPORT.md

- `Điểm validate_logs.py`: hiện ghi **30/100** — đó là baseline trước khi R1 làm.
  Số sau khi hoàn thiện là **100/100** (4/4 tiêu chí PASSED).
- `Số PII leak còn lại: 0` — đúng, giữ nguyên.
- Mục 1 đang gán sai vai: theo [TEAMWORK.md](../../TEAMWORK.md) thì Phạm Khắc Duy là
  *Tracing & Prompt Version*, Nguyễn Ngọc Thuận là *Dashboard, SLO & Alert*.
  REPORT.md đang ghi ngược hai vai này.

## Evidence correlation ID

- File: `submission/evidence/r1-log-correlation-id.txt`
- File: `submission/evidence/r1-log-events-contract.txt`
- Ảnh chụp: `submission/evidence/r1-log-correlation-id.png` *(chưa có — cần chụp thủ công)*

Mỗi request nhận đúng một correlation ID dạng `req-<8 ký tự hex>`, do
[app/middleware.py](../../app/middleware.py) sinh ra rồi `bind_contextvars` vào structlog,
nên cả `request_received`, `response_sent` và `request_failed` của cùng một request đều
mang cùng một ID. ID cũng được trả về client qua header `x-request-id`, kèm
`x-response-time-ms` — nhờ vậy khi điều tra incident có thể đi từ response của client về
đúng dòng log, không phải dò theo thời gian.

Nếu client tự gửi `x-request-id` đúng định dạng thì hệ thống dùng lại ID đó (trace xuyên
service); giá trị sai định dạng bị thay bằng ID mới để không vỡ contract log và không cho
phép chèn giá trị lạ vào response header.

Ví dụ một request hoàn chỉnh (13 correlation ID duy nhất trong lần chạy gần nhất):

```
req-59f5080d  request_received  service=api  feature=qa  model=claude-sonnet-4-5
req-59f5080d  response_sent     latency_ms=1071  tokens_in=36  tokens_out=102
                                cost_usd=0.001638  quality_score=0.9
```

## Evidence PII redaction

- File: `submission/evidence/r1-pii-redacted.txt`
- Trước/sau: `r1-validate-logs-before.txt` (30/100) → `r1-validate-logs-after.txt` (100/100)
- Ảnh chụp: `r1-pii-redacted.png`, `r1-validate-logs-before.png`, `r1-validate-logs-after.png`
  *(chưa có — cần chụp thủ công)*

Hai lớp bảo vệ:

1. `summarize_text()` chạy ngay tại handler `/chat`, che PII trước khi giá trị được đưa vào
   `payload`.
2. Processor `scrub_event` trong [app/logging_config.py](../../app/logging_config.py) chạy
   **trước** khi record được ghi ra file/stdout. Đây là lớp chốt: `validate_logs.py` quét
   toàn bộ JSON record chứ không riêng `payload`, nên processor scrub **đệ quy mọi trường
   string** (kể cả dict/list lồng nhau), chỉ miễn `ts`, `level`, `correlation_id` để không
   làm sai định dạng định danh kỹ thuật.

Pattern đang bắt: email, số điện thoại VN (5 biến thể `0901234567`, `090 123 4567`,
`090.123.4567`, `090-123-4567`, `+84 90 123 4567`), CCCD 12 số, số thẻ 16 số, hộ chiếu
(1 chữ cái + 7 số) và địa chỉ VN theo từ khoá hành chính.

Với địa chỉ VN, pattern **cố tình không** dùng `(?i)` và không nhận dạng không dấu:
"quan sát", "phương pháp" là từ xuất hiện thường xuyên trong nội dung lab này, nếu match
không dấu + không phân biệt hoa/thường thì log bị che sai chỗ. Đây là đánh đổi có ý thức
giữa recall và false positive — có test `test_lab_vocabulary_is_not_over_redacted` giữ
ràng buộc này.

`user_id` không bao giờ vào log ở dạng thô: chỉ ghi `user_id_hash` = sha256 cắt 12 ký tự.

## Kết quả validator

```
Total log records analyzed: 27
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 13
Potential PII leaks detected: 0
Estimated Score: 100/100
```

## Dòng cho mục 7 (Đóng góp cá nhân)

| Thành viên | Phần việc | Commit | Điều đã học |
| --- | --- | --- | --- |
| Phạm Đức Thiện (2A202601981) | R1 — correlation ID, log enrichment, JSON log, PII redaction | `782413b`, `b058330`, `0ab7464`, `0419918`, `f428d5e` | Redaction phải đặt ở processor cuối chain, không phải ở từng call site: chỉ cần một chỗ log quên gọi `summarize_text` là leak. Và validator quét cả record nên scrub riêng `payload` là không đủ. |
