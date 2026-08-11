# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: B07
- Repository URL: [github.com/thien43252/Day13-2A202601981-PhamDucThien](https://github.com/thien43252/Day13-2A202601981-PhamDucThien)
- Commit SHA cuối:
- Thành viên và vai trò:

| Thành viên         | Mã học viên | Vai trò                  |
| -------------------- | -------------- | ------------------------- |
| Phạm Đức Thiện   | 2A202601981    | Logging & PII             |
| Phạm Khắc Duy      | 2A202601757    | Dashboard, SLO & Alert    |
| Nguyễn Ngọc Thuận | 2A202601949    | Tracing & Prompt Version  |
| Trần Công Chiến   | 2A202601053    | Incident, Report & Demo   |

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces: 20
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID: submission\evidence\r1-log-correlation-id.png
- Evidence PII redaction: submission\evidence\r1-pii-redacted.png
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên        | Phần việc                                                    | Commit/PR                                                        | Điều đã học                                                                                                                                                                                                               |
| ------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phạm Đức Thiện  | R1 — correlation ID, log enrichment, JSON log, PII redaction  | `782413b`, `b058330`, `0ab7464`, `0419918`, `f428d5e`  | Redaction phải đặt ở processor cuối chain, không phải ở từng call site: chỉ cần một chỗ log quên gọi`summarize_text` là leak. Và validator quét cả record nên scrub riêng `payload` là không đủ.  |
