# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: B07
- Repository URL: [github.com/thien43252/Day13-2A202601981-PhamDucThien](https://github.com/thien43252/Day13-2A202601981-PhamDucThien)
- Commit SHA cuối: <!-- TODO(R4): điền sau lần push cuối cùng, trước khi nộp -->

| Thành viên         | Mã học viên | Vai trò                  |
| -------------------- | -------------- | ------------------------- |
| Phạm Đức Thiện   | 2A202601981    | Logging & PII             |
| Phạm Khắc Duy      | 2A202601757    | Tracing & Prompt Version  |
| Nguyễn Ngọc Thuận | 2A202601949    | Dashboard, SLO & Alert    |
| Trần Công Chiến   | 2A202601053    | Incident, Report & Demo   |

## 2. Kết quả kỹ thuật

> ⚠ Các số dưới đây là baseline tại thời điểm scaffold — cập nhật lại sau khi cả nhóm merge xong và chạy đủ checkpoint.

- Điểm `validate_logs.py`: **100/100** (4/4 tiêu chí PASSED)
- Tổng số traces: 21 <!-- TODO(R2): cập nhật sau khi chạy 10+ trace có metadata -->
- Số PII leak còn lại: **0**
- Link/đường dẫn dashboard: <!-- TODO(R3): cung cấp URL hoặc screenshot sau khi dựng dashboard runtime -->

## 3. Logging và tracing

### Evidence correlation ID

- `submission/evidence/r1-log-correlation-id.txt`
- `submission/evidence/r1-log-events-contract.txt`

Mỗi request nhận đúng một correlation ID dạng `req-<8 ký tự hex>`, do
[app/middleware.py](../app/middleware.py) sinh ra rồi `bind_contextvars` vào structlog,
nên cả `request_received`, `response_sent` và `request_failed` của cùng một request đều
mang cùng một ID. ID cũng được trả về client qua header `x-request-id`, kèm
`x-response-time-ms` — nhờ vậy khi điều tra incident có thể đi từ response của client về
đúng dòng log, không phải dò theo thời gian.

Nếu client tự gửi `x-request-id` đúng định dạng thì hệ thống dùng lại ID đó (trace xuyên
service); giá trị sai định dạng bị thay bằng ID mới để không vỡ contract log và không cho
phép chèn giá trị lạ vào response header.

Ví dụ một request hoàn chỉnh (13 correlation ID duy nhất trong lần chạy của R1):

```
req-59f5080d  request_received  service=api  feature=qa  model=claude-sonnet-4-5
req-59f5080d  response_sent     latency_ms=1071  tokens_in=36  tokens_out=102
                                cost_usd=0.001638  quality_score=0.9
```

### Evidence PII redaction

- `submission/evidence/r1-pii-redacted.txt`
- Trước/sau: `r1-validate-logs-before.txt` (30/100) → `r1-validate-logs-after.txt` (100/100)

Hai lớp bảo vệ:

1. `summarize_text()` chạy ngay tại handler `/chat`, che PII trước khi giá trị được đưa vào
   `payload`.
2. Processor `scrub_event` trong [app/logging_config.py](../app/logging_config.py) chạy
   **trước** khi record được ghi ra file/stdout. Đây là lớp chốt: `validate_logs.py` quét
   toàn bộ JSON record chứ không riêng `payload`, nên processor scrub **đệ quy mọi trường
   string** (kể cả dict/list lồng nhau), chỉ miễn `ts`, `level`, `correlation_id` để không
   làm sai định dạng định danh kỹ thuật.

Pattern đang bắt: email, số điện thoại VN (5 biến thể), CCCD 12 số, số thẻ 16 số, hộ chiếu
(1 chữ cái + 7 số) và địa chỉ VN theo từ khoá hành chính.

`user_id` không bao giờ vào log ở dạng thô: chỉ ghi `user_id_hash` = sha256 cắt 12 ký tự.

### Kết quả validator (đã xác minh lại trên log mới sinh)

```
Total log records analyzed: 21
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 10
Potential PII leaks detected: 0
Estimated Score: 100/100
```

### Trace waterfall / span đáng chú ý

<!-- TODO(R2): ảnh `r2-trace-waterfall.png` + mô tả span đáng chú ý -->

## 4. Prompt versioning

<!-- TODO(R2): dán nội dung từ `submission/evidence/notes-r2.md` vào mục này -->

- Prompt name: `day13-chat`
- Version/label baseline: `production` → v1
- Version/label candidate: `candidate` → v2
- Trace ID của mỗi version: <!-- TODO(R2): 2 trace ID khác nhau khi chạy cùng input -->
- Bằng chứng đổi label hoặc rollback: <!-- TODO(R2): ảnh `r2-rollback-label.png` -->

## 5. Dashboard, SLO và alerts

<!-- TODO(R3): dán nội dung từ `submission/evidence/notes-r3.md` vào mục này. R4 kiểm tra chéo: số trong `slo.yaml` phải trùng `dashboard.yaml` (TEAMWORK mục 2.3). -->

- Kết quả `validate_dashboard.py`: <!-- TODO(R3): phải in "HỢP LỆ: 6/6 panel" -->
- Evidence dashboard: <!-- TODO(R3): ảnh `r3-dashboard-6panel.png` — thấy rõ time range, đơn vị, threshold -->
- SLO đã chọn và lý do: <!-- TODO(R3): 4 SLI latency_p95 / error_rate / daily_cost / quality_score -->
- Alert rules và runbook: <!-- TODO(R3): từ `config/alert_rules.yaml` + `docs/alerts.md` -->

## 6. Điều tra challenge

> ⚠ Chỉ điền sau khi chạy challenge chính thức (sau 2:30). KHÔNG sửa `config/challenge.json`.

- Challenge ID: `day13-k4-observability-v1`
- Triệu chứng từ metrics: <!-- TODO(R4): p95 vượt ngưỡng 2000ms bao nhiêu — dẫn số cụ thể từ dashboard -->
- Trace ID liên quan: <!-- TODO(R4): trace ID request chậm + tên span bất thường -->
- Log line/correlation ID liên quan: <!-- TODO(R4): dòng log cụ thể + correlation ID chứng minh root cause -->
- Root cause: <!-- TODO(R4): kết luận từ log, không nói chung chung -->
- Fix action: <!-- TODO(R4) -->
- Preventive measure: <!-- TODO(R4): không trùng với fix action -->

## 7. Đóng góp cá nhân

<!-- TODO(R4): mỗi thành viên gửi 1 dòng: phần việc, link commit, điều đã học (TEAMWORK 5.2 bước 3). R4 tổng hợp. -->

| Thành viên | Phần việc | Commit/PR | Điều đã học |
| ------------ | ----------- | --------- | ---------------- |
| Phạm Đức Thiện (R1) | R1 — correlation ID, log enrichment, JSON log, PII redaction | `782413b`, `b058330`, `0ab7464`, `0419918`, `f428d5e` (PR #1) | Redaction phải đặt ở processor cuối chain, không phải ở từng call site: chỉ cần một chỗ log quên gọi `summarize_text` là leak. Và validator quét cả record nên scrub riêng `payload` là không đủ. |
| Phạm Khắc Duy (R2) | Tracing & Prompt Version | <!-- TODO(R2) --> | <!-- TODO(R2) --> |
| Nguyễn Ngọc Thuận (R3) | Dashboard, SLO & Alert | <!-- TODO(R3) --> | <!-- TODO(R3) --> |
| Trần Công Chiến (R4) | Incident, Report & Demo | <!-- TODO(R4) --> | <!-- TODO(R4) --> |
