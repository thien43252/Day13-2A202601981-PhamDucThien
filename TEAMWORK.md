# Phân công công việc nhóm B07 — Day 13 Observability

Tài liệu này chia 4 vai trò trong [README.md](README.md) thành 4 luồng làm việc **song song**, mỗi luồng sở hữu một tập file riêng để hạn chế tối đa conflict khi ghép code.

- Vai trò và evidence bắt buộc: [README.md](README.md#phân-vai-nhóm--tối-đa-4-vai-trò)
- Mốc thời gian gốc: [CHECKPOINTS.md](CHECKPOINTS.md).
- Cách chấm điểm: [RUBRIC.md](RUBRIC.md) — 60 điểm nhóm + 40 điểm cá nhân, nên **mỗi người phải có commit riêng có thể kiểm tra được**.

---

## 1. Bảng phân vai

| Vai                                      | Thành viên         | Mã học viên | Phạm vi chính                                          |
| ---------------------------------------- | -------------------- | -------------- | -------------------------------------------------------- |
| **R1 — Logging & PII**            | Phạm Đức Thiện   | 2A202601981    | correlation ID, enrichment metadata, JSON log, redaction |
| **R2 — Tracing & Prompt Version** | Phạm Khắc Duy      | 2A202601757    | Langfuse traces, prompt v1/v2, label & rollback          |
| **R3 — Dashboard, SLO & Alert**   | Nguyễn Ngọc Thuận | 2A202601949    | 6 panel, threshold, SLO, alert rules, runbook            |
| **R4 — Incident, Report & Demo**  | Trần Công Chiến   | 2A202601053    | challenge K4, Metrics → Traces → Logs, report, demo    |

> Vai trò có thể hoán đổi giữa các thành viên, nhưng **giữ nguyên ranh giới file ở mục 3** — đó là thứ quyết định việc merge có sạch hay không.

R4 kiêm luôn vai trò **integrator**: là người duy nhất được merge vào `main` và là người duy nhất sửa `submission/REPORT.md`.

---

## 2. Việc phải chốt chung trước khi ai đó viết dòng code đầu tiên (0:00–0:15)

Cả nhóm ngồi cùng nhau đúng 15 phút để chốt 4 hợp đồng dưới đây. Nếu bỏ qua bước này, R3 sẽ dựng dashboard trên tên trường mà R1 không hề ghi ra, và R4 sẽ không nối được trace với log.

### 2.1. Hợp đồng log (R1 sản xuất — R3 và R4 tiêu thụ)

Mọi log của `service == "api"` phải có đủ các trường sau (theo [config/logging_schema.json](config/logging_schema.json) và bộ chấm trong [scripts/validate_logs.py](scripts/validate_logs.py#L7-L8)):

```json
{
  "ts": "iso-utc", "level": "info", "service": "api",
  "event": "request_received | response_sent | request_failed",
  "correlation_id": "req-1a2b3c4d",
  "user_id_hash": "sha256-12-ký-tự", "session_id": "...",
  "feature": "...", "model": "claude-sonnet-4-5", "env": "dev",
  "latency_ms": 0, "tokens_in": 0, "tokens_out": 0,
  "cost_usd": 0.0, "quality_score": 0.0, "error_type": null,
  "payload": { }
}
```

- Tên event **không được đổi**: `request_received`, `response_sent`, `request_failed`. Cả 6 panel trong [config/dashboard.yaml](config/dashboard.yaml) đang query theo đúng 3 tên này.
- Định dạng correlation ID: `req-<8 ký tự hex>`.
- PII chỉ được phép nằm trong `payload` **sau khi đã đi qua** `scrub_text`.

### 2.2. Hợp đồng prompt (R2 sản xuất — R4 tiêu thụ)

| Biến                    | Giá trị chốt                                |
| ------------------------ | ---------------------------------------------- |
| `LANGFUSE_PROMPT_NAME` | `day13-chat`                                 |
| Label baseline           | `production` (trỏ vào v1)                  |
| Label candidate          | `candidate` (trỏ vào v2)                   |
| Biến trong template     | `{{feature}}`, `{{docs}}`, `{{message}}` |

Tên biến phải khớp tham số `compile()` trong [app/prompt_management.py:63-67](app/prompt_management.py#L63-L67), nếu không prompt v2 sẽ rơi về `local-fallback`.

### 2.3. Hợp đồng ngưỡng (R3 sản xuất — R4 trích dẫn trong report)

R3 chốt số cho `latency_p95_ms`, `error_rate_pct`, `daily_cost_usd`, `quality_score_avg` trong [config/slo.yaml](config/slo.yaml) và giữ cho các `threshold` trong `dashboard.yaml` **trùng số** với `slo.yaml`. Challenge K4 dùng `latency_threshold_ms: 2000`, nên đừng đặt SLO p95 lỏng đến mức incident không kích hoạt alert nào.

### 2.4. Hợp đồng Git

```
main                     ← chỉ R4 merge vào
├── feat/logging-pii     ← R1
├── feat/tracing-prompt  ← R2
├── feat/dashboard-slo   ← R3
└── feat/incident-report ← R4
```

- Commit message: `feat(logging): ...`, `fix(pii): ...`, `docs(report): ...` — prefix giúp R4 lọc commit theo người khi điền mục 7 của report.
- **Không ai commit `data/logs.jsonl`.** File này là JSONL append-only, 4 người cùng commit sẽ conflict ở mọi dòng. Xem mục 5.3.

---

## 3. Ranh giới file — ai sở hữu file nào

Nguyên tắc: **chỉ sửa file trong cột của mình**. Cần đổi file của người khác thì nhắn cho chủ sở hữu, không tự sửa.

| File / thư mục                                    | Chủ sở hữu                   | Ghi chú                                                        |
| --------------------------------------------------- | ------------------------------- | --------------------------------------------------------------- |
| [app/middleware.py](app/middleware.py)               | R1                              | 4 TODO: clear/extract/bind contextvars + response headers       |
| [app/logging_config.py](app/logging_config.py)       | R1                              | 1 TODO: đăng ký`scrub_event` vào processor chain          |
| [app/pii.py](app/pii.py)                             | R1                              | 1 TODO: bổ sung pattern (passport, địa chỉ VN)              |
| [app/main.py](app/main.py)                           | R1                              | 1 TODO ở`/chat` (dòng 47): `bind_contextvars(...)`        |
| [app/tracing.py](app/tracing.py)                     | R2                              | cấu hình client Langfuse, flush                               |
| [app/prompt_management.py](app/prompt_management.py) | R2                              | resolve prompt theo label                                       |
| [app/agent.py](app/agent.py)                         | R2                              | metadata trace/generation                                       |
| `.env` (local, **không commit**)           | R2 chốt key, cả nhóm copy    | `LANGFUSE_*`                                                  |
| [config/dashboard.yaml](config/dashboard.yaml)       | R3                              | 6 panel + threshold                                             |
| [config/slo.yaml](config/slo.yaml)                   | R3                              | thay`note: Replace with your group's target`                  |
| [config/alert_rules.yaml](config/alert_rules.yaml)   | R3                              | 3 alert đang là`TODO`                                       |
| [docs/alerts.md](docs/alerts.md)                     | R3                              | runbook cho`#alert-1..3`                                      |
| [submission/REPORT.md](submission/REPORT.md)         | **R4 duy nhất**          | người khác ghi vào file note riêng, xem 5.2                |
| [config/challenge.json](config/challenge.json)       | **không ai**             | sửa file này = vi phạm[RULES.md](RULES.md)                    |
| `submission/evidence/`                            | tất cả                        | mỗi người dùng**tiền tố tên file riêng**, xem 5.1 |
| `tests/`                                          | tất cả (chỉ thêm test mới) | không sửa test có sẵn để cho pass                         |

Điểm nóng duy nhất là `app/main.py` (R1) và `app/agent.py` (R2) — hai file này gọi lẫn nhau nhưng **không cần sửa chéo**: R1 chỉ thêm `bind_contextvars` ở đầu handler `/chat`, R2 chỉ sửa phần trong `LabAgent.run`. Nếu R2 thấy thiếu trường log, báo R1 thay vì tự sửa `main.py`.

---

## 4. Dòng thời gian 4 giờ — 4 luồng chạy song song

Vấn đề phụ thuộc lớn nhất: **R3 và R4 cần `data/logs.jsonl` đúng chuẩn, mà file đó chỉ đúng sau khi R1 xong.** Cách gỡ: trong giờ đầu R3 và R4 làm phần *không cần dữ liệu thật* (config, runbook, khung report, đọc challenge), R1 được ưu tiên merge sớm nhất.

| Khung giờ           | R1 — Logging & PII                                                                                                                     | R2 — Tracing & Prompt                                                                                 | R3 — Dashboard & Alert                                                                                                     | R4 — Incident & Report                                                                                                                      |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **0:00–0:15** | Chốt 4 hợp đồng ở mục 2 (cả nhóm)                                                                                               | ←                                                                                                     | ←                                                                                                                          | ←                                                                                                                                           |
| **0:15–0:30** | Setup env, chạy`load_test.py`, lưu baseline `validate_logs.py`                                                                    | Setup, lấy Langfuse key,`/health` báo `tracing_enabled: true`                                    | Chạy`validate_dashboard.py` để hiểu contract                                                                          | Đọc`config/challenge.json`, dựng khung report                                                                                           |
| **0:30–1:30** | **Đường găng.** Xong 4 TODO middleware + processor `scrub_event` + `bind_contextvars` + pattern PII. Mục tiêu ≥ 80/100 | Tạo prompt v1 trên Langfuse, gán label`production`, chạy 10+ trace có metadata                  | Điền`slo.yaml` + 3 alert + runbook `docs/alerts.md` (**chưa cần log thật**)                                  | Viết trước mục 1/2/5 của report; chuẩn bị kịch bản demo Metrics → Traces → Logs                                                   |
| **1:30**       | **Merge `feat/logging-pii` vào `main` trước tiên.** Cả nhóm rebase lên `main` mới                                   |                                                                                                        |                                                                                                                             |                                                                                                                                              |
| **1:30–2:30** | Bổ sung test PII, hỗ trợ R3 nếu thiếu trường log                                                                                 | Tạo prompt v2 + label`candidate`, chạy cùng input 2 label, thực hiện rollback, chụp 2 trace ID | Rebase → chạy load_test sinh log thật → dựng đủ 6 panel →`validate_dashboard.py` báo `6/6 panel` → chụp ảnh | Practice`inject_incident.py --scenario rag_slow` để tập luồng điều tra                                                               |
| **2:30**       | **Merge `feat/tracing-prompt` rồi `feat/dashboard-slo`**                                                                     |                                                                                                        |                                                                                                                             |                                                                                                                                              |
| **2:30–3:30** | Hỗ trợ chứng minh root cause bằng log + correlation ID                                                                              | Cung cấp trace ID của request chậm                                                                  | Đối chiếu triệu chứng với threshold panel, xác nhận alert nào lẽ ra phải bắn                                    | **Chủ trì:** chạy challenge K4 chính thức, xác định triệu chứng → span bất thường → log chứng minh → fix + preventive |
| **3:30–4:00** | Rà`git status`, không lộ `.env`/PII                                                                                              | Nộp evidence prompt                                                                                   | Nộp evidence dashboard                                                                                                     | Ghép report,`pytest -q`, commit SHA cuối, chạy demo thử                                                                                |

Lệnh challenge chính thức (chỉ R4 chạy, sau 2:30):

```bash
python scripts/inject_incident.py
python scripts/load_test.py --challenge --concurrency 5
```

---

## 5. Cách ghép việc của 4 người

### 5.1. Quy ước đặt tên evidence

Mỗi người tự đặt file trong `submission/evidence/` theo tiền tố vai trò → không bao giờ ghi đè lên nhau:

```
submission/evidence/
├── r1-validate-logs-before.png      ├── r3-dashboard-6panel.png
├── r1-validate-logs-after.png       ├── r3-validate-dashboard.png
├── r1-log-correlation-id.png        ├── r3-alert-threshold.png
├── r1-pii-redacted.png              ├── r4-challenge-metrics.png
├── r2-traces-list-10.png            ├── r4-challenge-trace.png
├── r2-trace-waterfall.png           ├── r4-challenge-log.png
├── r2-prompt-v1-v2.png              └── r4-demo-flow.png
└── r2-rollback-label.png
```

Danh sách evidence bắt buộc nằm ở [SUBMISSION.md](SUBMISSION.md#nội-dung-bắt-buộc) — đối chiếu lại trước khi nộp.

### 5.2. Cách ghép `submission/REPORT.md` mà không conflict

`REPORT.md` là file 4 người đều muốn sửa → nếu sửa trực tiếp sẽ conflict mỗi lần merge. Quy trình:

1. R1/R2/R3 **không mở `REPORT.md`**. Mỗi người viết nội dung phần mình vào file riêng:
   - `submission/evidence/notes-r1.md` → nội dung cho mục 3 (Logging và tracing)
   - `submission/evidence/notes-r2.md` → nội dung cho mục 4 (Prompt versioning)
   - `submission/evidence/notes-r3.md` → nội dung cho mục 5 (Dashboard, SLO và alerts)
2. R4 đọc 3 file note và dán vào `REPORT.md`, tự viết mục 6 (challenge).
3. Mục 7 (Đóng góp cá nhân) — mỗi người tự gửi R4 một dòng: phần việc, link commit, điều đã học. R4 tổng hợp.
4. Sau khi ghép xong, R4 xoá 3 file `notes-r*.md` trong commit cuối.

### 5.3. Xử lý `data/logs.jsonl`

File này hiện **chưa** được `.gitignore` bỏ qua và đang ở trạng thái untracked. Nó là log append-only nên nếu nhiều người commit sẽ conflict ở mọi dòng.

Chốt: **thêm `data/logs.jsonl` vào `.gitignore`** (R1 làm, trong commit đầu tiên). Ai cần log thì tự sinh lại trên máy mình:

```bash
uvicorn app.main:app --reload --env-file .env    # terminal 1
python scripts/load_test.py                       # terminal 2
```

Nếu Lab Coach yêu cầu nộp kèm log mẫu, R4 copy **một snapshot đã redact** vào `submission/evidence/logs-sample.jsonl` ở commit cuối — một lần duy nhất, do một người làm.

### 5.4. Thứ tự merge và cách xử lý conflict

```
1. feat/logging-pii      → main   (~1:30, ưu tiên tuyệt đối)
2. feat/tracing-prompt   → main   (~2:30)
3. feat/dashboard-slo    → main   (~2:30)
4. feat/incident-report  → main   (~3:45, cuối cùng)
```

Sau mỗi lần có người merge, ba người còn lại chạy:

```bash
git fetch origin && git rebase origin/main
python -m pytest -q
```

Nếu vẫn có conflict: người **đang rebase** là người sửa, và chỉ giữ thay đổi trong file thuộc quyền sở hữu của mình (mục 3). Conflict ở file không thuộc sở hữu của mình → luôn lấy bản trên `main`.

---

## 6. Định nghĩa "xong" cho từng vai

### R1 — Logging & PII

- [ ] `validate_logs.py` in `Estimated Score` ≥ 80/100 (mục tiêu 100).
- [ ] `Unique correlation IDs found` ≥ 2, không còn record nào có `correlation_id == "MISSING"`.
- [ ] `Potential PII leaks detected: 0` — kể cả email, phone VN, CCCD 12 số, số thẻ.
- [ ] Mọi log `service == "api"` có đủ `user_id_hash`, `session_id`, `feature`, `model`.
- [ ] Response header trả về `x-request-id` và `x-response-time-ms`.
- [ ] `python -m pytest tests/test_pii.py tests/test_chat_observability.py -q` pass.

### R2 — Tracing & Prompt Version

- [ ] ≥ 10 traces trên Langfuse, mỗi trace có `user_id` (đã hash), `session_id`, tags.
- [ ] Trace hiển thị `prompt_name`, `prompt_label`, `prompt_version` trong metadata.
- [ ] Có prompt `day13-chat` v1 (label `production`) và v2 (label `candidate`).
- [ ] Chạy cùng một input với 2 label, ghi lại 2 trace ID khác nhau.
- [ ] Có ảnh thao tác đổi label / rollback.
- [ ] `prompt_source` là `langfuse`, **không phải** `local-fallback` (nếu là fallback thì key hoặc tên biến đang sai).
- [ ] `python -m pytest tests/test_prompt_management.py tests/test_agent_prompt_trace.py tests/test_tracing_adapter.py -q` pass.

### R3 — Dashboard, SLO & Alert

- [ ] `python scripts/validate_dashboard.py` in `HỢP LỆ: 6/6 panel`.
- [ ] Dashboard runtime có đủ 6 nhóm: latency (p50/p95/p99), traffic, error, cost, token, quality.
- [ ] Ảnh dashboard thấy rõ **time range, đơn vị và đường threshold**.
- [ ] `slo.yaml` không còn dòng `note: Replace with your group's target`, số liệu khớp threshold trong `dashboard.yaml`.
- [ ] 3 alert trong `alert_rules.yaml` không còn chữ `TODO`, mỗi alert có severity, condition, owner thật.
- [ ] `docs/alerts.md` có runbook tương ứng `#alert-1`, `#alert-2`, `#alert-3`.
- [ ] `python -m pytest tests/test_dashboard_validator.py -q` pass.

### R4 — Incident, Report & Demo

- [ ] Chạy challenge `day13-k4-observability-v1` bằng file chính thức, **không sửa** `config/challenge.json`.
- [ ] Triệu chứng nêu bằng số từ metrics (p95 vượt ngưỡng 2000ms bao nhiêu).
- [ ] Có trace ID cụ thể của request chậm + tên span bất thường.
- [ ] Có dòng log + correlation ID chứng minh root cause (không nói chung chung).
- [ ] Có fix action và preventive measure riêng biệt, không trùng nhau.
- [ ] `REPORT.md` điền hết mục 1–7, không còn trường trống; commit SHA cuối đã điền.
- [ ] `python -m pytest -q` toàn bộ pass; `git status --short` sạch.
- [ ] Demo thử 1 lần theo đúng luồng Metrics → Traces → Logs → Root cause.

---

## 7. Rủi ro và cách gỡ

| Rủi ro                                         | Dấu hiệu                                                                                    | Cách gỡ                                                                                                                                                                                    |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R1 trễ → R3 và R4 đứng chờ                | Sau 1:30 vẫn chưa merge được                                                             | R1 merge trước phần correlation ID + enrichment, để pattern PII bổ sung sang commit sau. R3 tạm dùng`data/sample_queries.jsonl` để dựng khung panel                             |
| Không có Langfuse key                         | `prompt_source == "local-fallback"`, `/health` báo `tracing_enabled: false`            | App vẫn chạy, nhưng mất điểm trace. Ưu tiên xin key chung của lớp ngay trong 15 phút đầu; Docker local ở[SETUP.md](SETUP.md) là phương án dự phòng                        |
| Log đã redact nhưng validator vẫn báo leak | `Potential PII leaks detected > 0`                                                          | Validator quét**toàn bộ JSON record**, kể cả trường ngoài `payload`. Kiểm tra xem có trường nào (ví dụ `session_id`, `user_id`) đang mang giá trị thật không |
| Conflict`data/logs.jsonl`                     | Merge conflict hàng trăm dòng                                                              | Đã xử lý ở 5.3 — gitignore. Nếu lỡ commit rồi:`git rm --cached data/logs.jsonl`                                                                                                   |
| Số trong`slo.yaml` lệch `dashboard.yaml`  | Giám khảo hỏi tại sao alert không khớp SLO                                              | R3 rà lại 4 cặp giá trị trước 2:30, R4 kiểm tra chéo khi viết mục 5 report                                                                                                        |
| Một thành viên không có commit riêng      | Mất tới 20 điểm cá nhân theo[RUBRIC.md](RUBRIC.md#b2-bằng-chứng-đóng-góp-20-điểm) | Mỗi người commit**trên nhánh của mình**, tối thiểu 3 commit, không để một người push hộ                                                                                |

---

## 8. Checklist chung trước khi nộp (R4 chủ trì, cả nhóm xác nhận)

```bash
python -m pytest -q
python scripts/validate_logs.py
python scripts/validate_dashboard.py
git status --short
git log --oneline --author=<mỗi thành viên>   # xác nhận ai cũng có commit
```

- [ ] Không có `.env`, API key, `.venv/` trong Git.
- [ ] Không có log chứa PII chưa che.
- [ ] `config/challenge.json` giữ nguyên như lúc Lab Coach release.
- [ ] `submission/REPORT.md` đủ mục 1–7, đã điền commit SHA cuối.
- [ ] Evidence trong `submission/evidence/` khớp danh sách ở [SUBMISSION.md](SUBMISSION.md).
- [ ] Đã xoá `notes-r1.md`, `notes-r2.md`, `notes-r3.md`.
- [ ] Push và nộp repo URL + commit SHA lên Codelabs.
