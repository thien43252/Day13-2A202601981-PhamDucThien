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

- Điểm `validate_logs.py`: **100/100** (4/4 tiêu chí PASSED)
- Tổng số traces: **10+ traces trên Langfuse** (5 production/v1 + 5 candidate/v2, xem mục 4)
- Số PII leak còn lại: **0**
- `validate_dashboard.py`: **HỢP LỆ: 6/6 panel**
- Link/đường dẫn dashboard: <!-- TODO(R3): URL dashboard runtime sau khi dựng (chưa có ảnh evidence) -->
- Runbook alerts: `docs/alerts.md` (#alert-1, #alert-2, #alert-3)

## 3. Logging và tracing

### Evidence correlation ID

- `submission/evidence/r1-log-correlation-id.png`
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

Ví dụ một request hoàn chỉnh (16 correlation ID duy nhất trong lần chạy của R1):

```
req-59f5080d  request_received  service=api  feature=qa  model=claude-sonnet-4-5
req-59f5080d  response_sent     latency_ms=1071  tokens_in=36  tokens_out=102
                                cost_usd=0.001638  quality_score=0.9
```

### Evidence PII redaction

- `submission/evidence/r1-pii-redacted.png`
- Trước/sau: `r1-validate-logs-before.png` (30/100) → `r1-validate-logs-after.png` (100/100)

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
Total log records analyzed: 33
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 16
Potential PII leaks detected: 0
Estimated Score: 100/100
```

### Tracing (R2)

- `app/agent.py` tạo generation scope tường minh bằng cùng một Langfuse client cho generation và trace metadata. Mỗi trace ghi `user_id` đã hash, `session_id`, tags (`lab`, feature, model) và `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`.
- `app/tracing.py` dùng client singleton và flush các event Langfuse khi tiến trình kết thúc.
- Prompt text `day13-chat` trên Langfuse giữ đủ biến `{{feature}}`, `{{docs}}`, `{{message}}`.
- Trace waterfall: <!-- TODO(R2): ảnh `r2-trace-waterfall.png` + mô tả span đáng chú ý -->

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: **v1** — label `baseline`, `production`
- Version/label candidate: **v2** — label `candidate`

### Thay đổi giữa v1 và v2

| Version | Labels | Nội dung thay đổi |
|---|---|---|
| v1 | `baseline`, `production` | Trả lời ngắn gọn theo tài liệu đã cung cấp. |
| v2 | `candidate` | Yêu cầu trả lời có bằng chứng và nêu rõ khi tài liệu không đủ. |

### Trace ID của từng label

Cùng input `How do we investigate an alert?` đã chạy qua v1/`production` và v2/`candidate`.

| Label | Trace ID |
|---|---|
| production (v1) | `7d6bd672b40a199bb38f15982553b59b`, `7909a3d205b86385a1042917e137ba83`, `556e46c7031202f13657c377daddf392`, `eae209ad794ddaa68534bcc03446db38`, `afed83d4b8203efcdc881fc929d54063` |
| candidate (v2) | `0b2847f9197ab4864acf9eeef103f7fd`, `2509a2bfc6fc48e730999e31e8d7deb3`, `905f4c839f73b7ac45b3f7e59b728c69`, `51cd3cce532a021a2df88c948ee85dcb`, `1183157140c24ecddc61dcb5c4feb5c7` |

### Bằng chứng đổi label và rollback

| Mốc | `production` version | Trace ID |
|---|---:|---|
| Sau khi chuyển sang v2 | 2 | `3a66d16295fcb62c3871ff80c952e92c` |
| Sau rollback | 1 | `0f1cce8a6e85483311c887931c35a9c9` |

Đã chuyển `production` sang v2 để xác minh rồi rollback về v1. Trạng thái cuối: `production → v1`, `candidate → v2`.
<!-- TODO(R2): ảnh `r2-rollback-label.png` và `r2-prompt-v1-v2.png` (chưa có) -->

## 5. Dashboard, SLO và alerts

### Kết quả validator

`python scripts/validate_dashboard.py` → **HỢP LỆ: 6/6 panel** (đã chạy lại trên log thật).

### 6 panel dashboard (`config/dashboard.yaml`)

| Panel | Aggregation | Threshold | Đơn vị |
|---|---|---|---|
| latency | p50/p95/p99 | p95 ≤ 3000ms | ms |
| traffic | count, rate_per_minute | ≥ 1 | requests/min |
| errors | error_rate_pct | ≤ 2% | percent |
| cost | sum_by_minute, total | total ≤ 2.5 | usd |
| tokens | sum_by_field | ≤ 50000 | tokens |
| quality | mean | ≥ 0.75 | score 0–1 |

Nguồn: `data/logs.jsonl` — các trường `latency_ms`, `tokens_in/out`, `cost_usd`, `quality_score` do R1 sinh qua correlation ID.

### SLO đã chọn và lý do (`config/slo.yaml`)

| SLI | Objective | Target | Lý do |
|---|---|---|---|
| latency_p95_ms | 3000ms | 99.5% | Challenge K4 dùng ngưỡng 2000ms nên incident chắc chắn vượt 3000ms → alert bắn được |
| error_rate_pct | 2% | 99.0% | Mục tiêu theo yêu cầu, không quá lỏng |
| daily_cost_usd | 2.5 USD | 100.0% | Realistic cho practice ~20–30 request/ngày |
| quality_score_avg | 0.75 | 95.0% | Cảnh báo khi chất lượng bắt đầu giảm |

### Alert rules (`config/alert_rules.yaml`) và runbook (`docs/alerts.md`)

| Alert | Severity | Condition | Runbook |
|---|---|---|---|
| high_latency_p95 | warning | p95 ≥ 2500ms kéo 5 phút, hoặc ≥ 3000ms kéo 2 phút | `#alert-1` |
| elevated_error_rate | warning | error_rate ≥ 2% kéo 5 phút | `#alert-2` |
| quality_score_degradation | info | mean(quality_score) < 0.75 kéo 10 phút, hoặc < 0.65 point-in-time | `#alert-3` |

Thiết kế dựa trên triệu chứng người dùng (chậm, lỗi, kém chất lượng), không theo implementation. 3 bước điều tra mỗi alert: dashboard → trace/log qua correlation ID → span waterfall.

### Evidence

<!-- TODO(R3): ảnh `r3-dashboard-6panel.png`, `r3-validate-dashboard.png`, `r3-alert-threshold.png` (chưa chụp — cần dựng dashboard runtime và chụp) -->

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
| Phạm Khắc Duy (R2) | R2 — Langfuse traces, prompt v1/v2, label `production`/`candidate`, rollback | `45212b1`, PR #3 | Tạo generation scope tường minh bằng chung một Langfuse client cho generation + trace metadata; dùng client singleton + flush khi kết thúc. |
| Nguyễn Ngọc Thuận (R3) | R3 — 6 panel dashboard, SLO, 3 alert + runbook | `cff7b32`, PR #2 | Threshold phải khớp giữa `slo.yaml` và `dashboard.yaml`; thiết kế alert theo triệu chứng (symptom-based) để ngưỡng chắc chắn bắn đúng incident. |
| Trần Công Chiến (R4) | Incident, Report & Demo | <!-- TODO(R4) --> | <!-- TODO(R4) --> |
