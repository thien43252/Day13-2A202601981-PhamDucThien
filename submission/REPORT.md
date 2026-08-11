# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: B07
- Repository URL: [github.com/thien43252/Day13-2A202601981-PhamDucThien](https://github.com/thien43252/Day13-2A202601981-PhamDucThien)
- Commit SHA cuối: `37133bf` (`check`)
- Thành viên và vai trò:

| Thành viên         | Mã học viên | Vai trò                  |
| -------------------- | -------------- | ------------------------- |
| Phạm Đức Thiện   | 2A202601981    | Logging & PII             |
| Phạm Khắc Duy      | 2A202601757    | Tracing & Prompt Version  |
| Nguyễn Ngọc Thuận | 2A202601949    | Dashboard, SLO & Alert    |
| Trần Công Chiến   | 2A202601053    | Incident, Report & Demo   |

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces đã xác minh: 0 (Langfuse không kết nối được; xem mục 4)
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `dashboard.py` — chạy bằng `uv run streamlit run dashboard.py`, mặc định tại `http://localhost:8501`.
- Snapshot dữ liệu dùng để đối chiếu: 133 records, 60 `request_received`, 60 `response_sent`, 0 `request_failed`; P95 latency 1,459.9ms, error rate 0%, window cost $0.121035, tokens in/out 1,980/7,673 và quality trung bình 0.88.

## 3. Logging và tracing

- Evidence correlation ID: [r1-log-events-contract.txt](evidence/r1-log-events-contract.txt) và [r1-log-correlation-id.png](evidence/r1-log-correlation-id.png). Một request giữ cùng correlation ID từ `request_received` đến `response_sent`/`request_failed`; ID đó cũng được trả qua header `x-request-id`.
- Evidence PII redaction: [r1-pii-redacted.png](evidence/r1-pii-redacted.png) và kết quả validator 100/100. `scrub_event` redaction đệ quy toàn bộ string trong record (kể cả payload lồng nhau), còn `user_id` chỉ được log dưới dạng `user_id_hash`.
- Evidence trace waterfall: Chưa có evidence hợp lệ vì client Langfuse trả về HTTP 401 khi gọi `auth_check()`.
- Giải thích một span đáng chú ý: Không thể kết luận từ trace/span khi chưa xác thực được Langfuse. Ở tầng log, `latency_ms` của `response_sent` là chỉ số thay thế đang dùng để theo dõi tail latency; việc quy nguyên nhân về một span cụ thể cần trace waterfall sau khi khôi phục kết nối.

## 4. Prompt versioning

- Trạng thái: **không kết nối được Langfuse Cloud**. `LANGFUSE_HOST` đang là `https://cloud.langfuse.com`, nhưng `client.auth_check()` trả về HTTP 401: `Invalid credentials. Confirm that you've configured the correct host.` Vì vậy không dùng các trace/prompt trên dashboard Langfuse làm evidence.
- Prompt name dự kiến theo cấu hình: `day13-chat`.
- Version/label baseline và candidate: chưa thể xác minh trên Langfuse; không khẳng định label nào đang trỏ tới version nào khi xác thực thất bại.
- Trace ID của mỗi version: không có trace ID đã xác minh trong lần nộp này.
- Bằng chứng đổi label hoặc rollback: chưa có. Hướng xử lý là tạo/rotate cặp public key + secret key thuộc đúng project tại `cloud.langfuse.com`, cập nhật `.env`, chạy lại `auth_check()`, rồi mới thực hiện và chụp evidence label/rollback.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: **HỢP LỆ: 6/6 panel có trong dashboard contract** ([r3-validate-dashboard-results.txt](evidence/r3-validate-dashboard-results.txt)).
- Evidence dashboard: [r3-dashboard.png](evidence/r3-dashboard.png) và [r3-dashboard-2.png](evidence/r3-dashboard-2.png). Dashboard Streamlit hiện có đủ 6 panel: latency (P50/P95/P99), traffic, errors, cost, tokens và quality; mỗi panel đọc `data/logs.jsonl` và hiển thị threshold từ `config/dashboard.yaml`.
- SLO đã chọn và lý do: P95 latency ≤ 3,000ms (target 99.5%; incident K4 dùng ngưỡng 2,000ms nên đủ nhạy); error rate ≤ 2% (target 99%); daily cost ≤ $2.5; quality score mean ≥ 0.75 (target 95%). Các ngưỡng này đồng nhất giữa `dashboard.yaml` và `slo.yaml`.
- Alert rules và runbook: `high_latency_p95` (warning: ≥2,500ms/5m hoặc ≥3,000ms/2m), `elevated_error_rate` (warning: ≥2%/5m) và `quality_score_degradation` (info: <0.75/10m hoặc <0.65 tức thời). Runbook tại `docs/alerts.md` hướng dẫn điều tra theo luồng dashboard → correlation ID/log → trace khi Langfuse khả dụng.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1`; scenario được cấu hình là `rag_slow`, feature ảnh hưởng `monitoring`, ngưỡng latency 2,000ms.
- Triệu chứng từ metrics: Chưa có kết quả challenge được chạy để báo cáo. Dataset hiện tại là baseline: P95 1,459.9ms, P99 1,725.01ms, không có response nào ≥2,000ms và error rate 0%; vì vậy không được diễn giải baseline là một incident `rag_slow`.
- Trace ID liên quan: Không có trace ID đã xác minh vì Langfuse HTTP 401.
- Log line/correlation ID liên quan: Không có correlation ID của challenge; log hiện tại chỉ có feature `qa`/`summary`, không có feature `monitoring` của K4.
- Root cause: Chưa xác nhận. Giả thuyết điều tra cho scenario `rag_slow` là span retrieval/RAG chậm, nhưng phải được chứng minh bằng log có correlation ID và trace waterfall trước khi kết luận.
- Fix action: Chưa áp dụng fix do chưa tái tạo challenge. Nếu trace xác nhận retrieval chậm, kiểm tra latency của RAG DB, điều chỉnh timeout/retry phù hợp và rollback thay đổi gây suy giảm nếu có.
- Preventive measure: Giữ alert P95 theo SLO, chạy lại challenge sau khi Langfuse được xác thực, liên kết dashboard → log correlation ID → trace, và lưu evidence trước/sau khi mitigation.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên        | Phần việc                                                    | Commit/PR                                                        | Điều đã học                                                                                                                                                                                                               |
| ------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phạm Đức Thiện  | R1 — correlation ID, log enrichment, JSON log, PII redaction  | `782413b`, `b058330`, `0ab7464`, `0419918`, `f428d5e`  | Redaction phải đặt ở processor cuối chain, không phải ở từng call site: chỉ cần một chỗ log quên gọi`summarize_text` là leak. Và validator quét cả record nên scrub riêng `payload` là không đủ.  |
| Phạm Khắc Duy | R2 — tracing context, generation metadata, prompt-version observability và flush Langfuse | [`45212b1`](https://github.com/thien43252/Day13-2A202601981-PhamDucThien/commit/45212b1) trên `feat/tracing-prompt` (đã merge qua PR #3) | Khi trace có metadata nhất quán (`user_id` đã hash, session, feature, model và prompt label/version), việc so sánh hai prompt không còn phụ thuộc vào việc đọc log thủ công. Flush cũng là bước quan trọng để tránh mất event khi process kết thúc. |
| Nguyễn Ngọc Thuận | R3 — định nghĩa 6 dashboard panel, SLO, symptom-based alert và runbook | [`cff7b32`](https://github.com/thien43252/Day13-2A202601981-PhamDucThien/commit/cff7b32) trên `feat/dashboard-slo` (đã merge qua PR #2) | SLO phải xuất phát từ hành vi người dùng và dùng chung một nguồn ngưỡng giữa dashboard, alert và runbook. Nếu ba nơi dùng ba con số khác nhau thì alert không còn là tín hiệu đáng tin để điều tra. |
| Trần Công Chiến | R4 — incident, tổng hợp report và demo | Chưa thấy nhánh/commit `feature/incident` trong local hoặc remote Git history hiện tại; cần bổ sung SHA/PR thực tế trước khi nộp | Bài học được ghi ở dạng kế hoạch điều tra: luôn đi theo chuỗi metrics → correlation ID/log → trace trước khi kết luận root cause; không suy diễn nguyên nhân chỉ từ một đường biểu đồ. |
