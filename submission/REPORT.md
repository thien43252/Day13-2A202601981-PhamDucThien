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

- Điểm `validate_logs.py`: 30/100 <!-- TODO(R1): cập nhật sau khi đạt ≥80/100, mục tiêu 100 -->
- Tổng số traces: 21 <!-- TODO(R2): cập nhật sau khi chạy 10+ trace có metadata -->
- Số PII leak còn lại: 0 <!-- TODO(R1): xác nhận "Potential PII leaks detected: 0" trên toàn bộ JSON record -->
- Link/đường dẫn dashboard: <!-- TODO(R3): cung cấp URL hoặc screenshot sau khi dựng dashboard runtime -->

## 3. Logging và tracing

<!-- TODO(R1): dán nội dung từ `submission/evidence/notes-r1.md` vào mục này -->

- Evidence correlation ID: <!-- TODO(R1): ảnh `r1-log-correlation-id.png` -->
- Evidence PII redaction: <!-- TODO(R1): ảnh `r1-pii-redacted.png` -->
- Evidence trace waterfall: <!-- TODO(R2): ảnh `r2-trace-waterfall.png` -->
- Giải thích một span đáng chú ý: <!-- TODO(R2): mô tả span + lý do đáng chú ý -->

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
| Phạm Đức Thiện (R1) | Logging & PII | <!-- TODO(R1) --> | <!-- TODO(R1) --> |
| Phạm Khắc Duy (R2) | Tracing & Prompt Version | <!-- TODO(R2) --> | <!-- TODO(R2) --> |
| Nguyễn Ngọc Thuận (R3) | Dashboard, SLO & Alert | <!-- TODO(R3) --> | <!-- TODO(R3) --> |
| Trần Công Chiến (R4) | Incident, Report & Demo | <!-- TODO(R4) --> | <!-- TODO(R4) --> |
