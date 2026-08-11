# Tổng kết vai R1 — Logging & PII

- **Người thực hiện:** Phạm Đức Thiện — 2A202601981
- **Nhánh:** `feat/logging-pii` (6 commit, đi trước `main` 6 commit, chưa push/merge)
- **Ngày:** 2026-08-11
- **Điểm `validate_logs.py`:** 30/100 (baseline) → **100/100** — vượt mục tiêu 80/100
- **Test:** `python -m pytest -q` → **35 passed**

---

## 1. Đã làm xong

### 1.1. Code — 7 TODO trong phạm vi R1 đã hết

| File | Việc | Trạng thái |
| --- | --- | --- |
| [app/middleware.py](app/middleware.py) | `clear_contextvars()` chống rò rỉ context giữa request | ✅ |
| [app/middleware.py](app/middleware.py) | Nhận `x-request-id` từ header hoặc sinh mới dạng `req-<8 hex>` | ✅ |
| [app/middleware.py](app/middleware.py) | `bind_contextvars(correlation_id=...)` | ✅ |
| [app/middleware.py](app/middleware.py) | Response header `x-request-id` + `x-response-time-ms` | ✅ |
| [app/logging_config.py](app/logging_config.py) | Đăng ký `scrub_event` vào processor chain | ✅ |
| [app/pii.py](app/pii.py) | Bổ sung pattern passport + địa chỉ VN | ✅ |
| [app/main.py](app/main.py) | `bind_contextvars` enrichment ở `/chat` | ✅ |

Ba quyết định thiết kế đáng ghi lại (nằm ngoài yêu cầu tối thiểu của TODO):

1. **Không tin `x-request-id` của client vô điều kiện.** ID sai định dạng bị thay bằng ID mới
   (`normalize_correlation_id`). Nếu nhận nguyên xi thì contract `req-<8 hex>` mà R3/R4 đang
   dựa vào sẽ vỡ, và client có thể chèn giá trị lạ vào response header.
2. **`scrub_event` scrub đệ quy MỌI trường string, không chỉ `payload`.**
   `validate_logs.py` quét `json.dumps(rec)` — toàn bộ record. Chỉ scrub `payload` là chưa đủ:
   một trường bị lọt (ví dụ `session_id` mang email thật) vẫn bị tính là leak. Miễn `ts`,
   `level`, `correlation_id` để không làm sai định dạng định danh kỹ thuật.
3. **Pattern địa chỉ VN cố tình không dùng `(?i)` và không match dạng không dấu.**
   "quan sát", "phương pháp" là từ xuất hiện liên tục trong nội dung lab này; match không dấu
   + không phân biệt hoa/thường sẽ che sai chỗ. Đánh đổi recall để tránh false positive, có
   test `test_lab_vocabulary_is_not_over_redacted` giữ ràng buộc.

### 1.2. Hợp đồng log đã bàn giao cho R3 và R4

Cả 3 event name trong [TEAMWORK.md §2.1](TEAMWORK.md) đều đã sinh ra thật và có đủ trường —
R3 dựng 6 panel được, R4 nối Metrics → Traces → Logs được:

| Event | Trường đã có | Panel dùng nó |
| --- | --- | --- |
| `request_received` | ts, level, service, event, correlation_id, user_id_hash, session_id, feature, model, env, error_type=null, payload | traffic, errors (mẫu số) |
| `response_sent` | + latency_ms, tokens_in, tokens_out, cost_usd, quality_score | latency, cost, tokens, quality |
| `request_failed` | + error_type (ví dụ `RuntimeError`), payload.detail | errors (tử số + count_by_value) |

Nhánh lỗi đã được kiểm tra thật bằng cách bật incident `tool_fail`: log ra
`error_type: "RuntimeError"`, đủ enrichment, PII trong message vẫn bị che.

### 1.3. Git

| Commit | Nội dung |
| --- | --- |
| `782413b` | `chore(logging)`: gitignore `data/logs.jsonl` + `git rm --cached` (TEAMWORK.md §5.3) |
| `b058330` | `feat(logging)`: correlation ID xuyên suốt + enrich metadata |
| `0ab7464` | `fix(pii)`: passport + địa chỉ VN + scrub toàn bộ record |
| `0419918` | `test(logging)`: 13 test mới |
| `f428d5e` | `docs(evidence)`: evidence dạng text |
| _(HEAD)_ | `docs(logging)`: file tổng kết này + `notes-r1.md` |

`data/logs.jsonl` đã được bỏ theo dõi khỏi Git → 4 người không còn conflict ở file
append-only này. `.env` vẫn được `.gitignore` bỏ qua, không có key nào bị commit.

### 1.4. Test mới (13 test, tất cả pass)

- [tests/test_logging_correlation.py](tests/test_logging_correlation.py) — 6 test: định dạng ID,
  ID duy nhất mỗi request, dùng lại ID hợp lệ của client, thay ID sai định dạng, log API đủ
  enrichment, `user_id` thô không bao giờ vào log.
- [tests/test_pii_scrub_processor.py](tests/test_pii_scrub_processor.py) — 7 test: passport,
  địa chỉ VN, CCCD, thẻ, không over-redact từ vựng lab, scrub payload lồng nhau, scrub trường
  ngoài payload, giữ nguyên định danh kỹ thuật.

Không sửa test có sẵn để cho pass.

### 1.5. Evidence đã nộp (dạng text)

Trong [submission/evidence/](submission/evidence/):

| File | Nội dung |
| --- | --- |
| `r1-validate-logs-before.txt` | Baseline 30/100 |
| `r1-validate-logs-after.txt` | 100/100, 4/4 PASSED |
| `r1-log-correlation-id.txt` | 1 request đầy đủ + 13 correlation ID duy nhất |
| `r1-log-events-contract.txt` | 3 event name với đủ trường |
| `r1-pii-redacted.txt` | Các dòng đã redact (email, phone VN, credit card) |
| `notes-r1.md` | Nội dung cho mục 3 REPORT.md + dòng mục 7, để R4 dán vào |

### 1.6. Định nghĩa "xong" của R1 — [TEAMWORK.md §6](TEAMWORK.md)

- [x] `validate_logs.py` ≥ 80/100 → đạt **100/100**
- [x] `Unique correlation IDs found` ≥ 2 → **13**, không còn record nào `correlation_id == "MISSING"`
- [x] `Potential PII leaks detected: 0` — email, phone VN, CCCD 12 số, số thẻ
- [x] Mọi log `service == "api"` đủ `user_id_hash`, `session_id`, `feature`, `model`
- [x] Response header trả về `x-request-id` và `x-response-time-ms`
- [x] `pytest tests/test_pii.py tests/test_chat_observability.py -q` pass
- [ ] Ảnh chụp evidence — xem §2.1
- [ ] Merge `feat/logging-pii` vào `main` — xem §2.2

---

## 2. Chưa làm được — việc còn lại

### 2.1. Ảnh chụp evidence — **PHẢI LÀM THỦ CÔNG** (không tự động hoá được)

**Lý do:** cần chụp màn hình terminal/editor thật. Nội dung đã có sẵn ở dạng `.txt` nên chỉ
còn việc chụp lại, nhưng [SUBMISSION.md](SUBMISSION.md) và
[TEAMWORK.md §5.1](TEAMWORK.md) yêu cầu ảnh.

- [ ] `submission/evidence/r1-validate-logs-before.png`
- [ ] `submission/evidence/r1-validate-logs-after.png`
- [ ] `submission/evidence/r1-log-correlation-id.png`
- [ ] `submission/evidence/r1-pii-redacted.png`

**Hướng dẫn — làm đúng thứ tự này:**

```powershell
# Terminal 1 — chạy app (nếu chưa chạy)
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --env-file .env

# Terminal 2
# (1) Ảnh "before": mở file baseline đã lưu và chụp
notepad submission\evidence\r1-validate-logs-before.txt
#     -> chụp -> lưu thành r1-validate-logs-before.png

# (2) Sinh log mới rồi chụp kết quả validator ngay trên terminal
Remove-Item data\logs.jsonl -ErrorAction SilentlyContinue
.venv\Scripts\python.exe scripts\load_test.py
.venv\Scripts\python.exe scripts\validate_logs.py
#     -> chụp cả khối output (phải thấy rõ dòng "Estimated Score: 100/100"
#        và 4 dòng "+ [PASSED]") -> r1-validate-logs-after.png

# (3) Ảnh correlation ID: 2 dòng log cùng 1 ID (đã test chạy được)
$cid = (Get-Content data\logs.jsonl | Where-Object { $_ -match '"service": "api"' } | Select-Object -First 1 | ConvertFrom-Json).correlation_id
Write-Output "Correlation ID: $cid"
Select-String -Path data\logs.jsonl -Pattern $cid | ForEach-Object { $_.Line }
#     -> chụp -> r1-log-correlation-id.png
#     Ảnh phải thấy CÙNG MỘT correlation_id ở cả request_received và response_sent.

# (4) Ảnh PII đã redact
Select-String -Path data\logs.jsonl -Pattern "REDACTED"
#     -> chụp -> r1-pii-redacted.png
#     Ảnh phải thấy REDACTED_EMAIL, REDACTED_PHONE_VN, REDACTED_CREDIT_CARD.
```

Chụp bằng `Win + Shift + S`, lưu vào `submission/evidence/` đúng tên trên, rồi:

```powershell
git add submission/evidence/r1-*.png
git commit -m "docs(evidence): anh chup evidence R1 logging va PII"
```

> Lưu ý khi chụp: đảm bảo trong khung ảnh **không lộ** nội dung `.env` hay API key
> (đừng chụp tab editor đang mở `.env`).

### 2.2. Merge `feat/logging-pii` vào `main` — **CHỜ ROLE KHÁC (R4)**

**Lý do:** theo [TEAMWORK.md §2.4](TEAMWORK.md), R4 (Trần Công Chiến) kiêm vai integrator và là
**người duy nhất** được merge vào `main`. R1 không tự merge.

- [ ] Push nhánh: `git push -u origin feat/logging-pii`
- [ ] Báo R4 merge — R1 là ưu tiên tuyệt đối, merge **đầu tiên** (~mốc 1:30) vì R3 và R4
      đứng chờ `data/logs.jsonl` đúng chuẩn.
- [ ] Sau khi R4 merge xong, cả nhóm rebase: `git fetch origin && git rebase origin/main`

Trạng thái hiện tại: nhánh `feat/logging-pii` đi trước `main` 5 commit, chưa push.

### 2.3. Cập nhật `submission/REPORT.md` — **CHỜ ROLE KHÁC (R4)**

**Lý do:** [TEAMWORK.md §3](TEAMWORK.md) ghi `submission/REPORT.md` là của **R4 duy nhất**.
R1 không được mở file này. Nội dung R1 đã viết sẵn trong
[submission/evidence/notes-r1.md](submission/evidence/notes-r1.md) để R4 dán vào.

Ba việc cần nhắn R4:

- [ ] Mục 2: `Điểm validate_logs.py` đang ghi **30/100** — đó là baseline. Số đúng sau khi
      R1 xong là **100/100**.
- [ ] Mục 3: dán nội dung từ `notes-r1.md` (phần correlation ID + PII redaction).
      Phần trace waterfall và "span đáng chú ý" là của R2.
- [ ] Mục 1: bảng vai đang **gán ngược R2 và R3** so với TEAMWORK.md — REPORT.md ghi
      Phạm Khắc Duy = *Dashboard, SLO & Alert* và Nguyễn Ngọc Thuận = *Tracing & Prompt
      Version*, trong khi TEAMWORK.md ghi ngược lại. Cần chốt lại cho khớp.
- [ ] Mục 7: dán dòng đóng góp của R1 từ `notes-r1.md`.

### 2.4. Hỗ trợ R3 và R4 — **CHỜ ROLE KHÁC**

**Lý do:** đây là việc phản ứng theo yêu cầu, chỉ phát sinh khi R3/R4 chạy dữ liệu thật.

- [ ] **Chờ R3:** nếu R3 dựng dashboard mà thiếu trường log nào, R3 báo → R1 thêm vào
      `app/main.py`. R2/R3 **không tự sửa** `app/main.py` (TEAMWORK.md §3).
      Hiện tại đã kiểm tra: cả 6 panel trong `config/dashboard.yaml` đều có đủ trường nguồn.
- [ ] **Chờ R4:** khi R4 chạy challenge K4 (mốc 2:30), R1 hỗ trợ chứng minh root cause bằng
      log + correlation ID. Cách làm: lấy correlation ID của request chậm từ metrics/trace rồi

      ```powershell
      Select-String -Path data\logs.jsonl -Pattern "req-xxxxxxxx"
      ```

      Log sẽ cho `latency_ms`, `error_type` và `payload` của đúng request đó.
- [ ] **Chờ R2:** không có phụ thuộc nào từ R1 sang R2. R1 đã kiểm tra `app/agent.py` dùng
      `hash_user_id` và `summarize_text` từ `app/pii.py` — đổi pattern PII không làm vỡ
      phần trace của R2.

### 2.5. Rà soát cuối trước khi nộp — **LÀM Ở MỐC 3:30, sau khi R4 merge hết**

**Lý do:** phải chạy sau khi tất cả nhánh đã merge, nên chưa làm được lúc này.

- [ ] `git status --short` sạch, không lộ `.env`/PII
- [ ] `python -m pytest -q` toàn bộ pass sau khi merge cả 4 nhánh
- [ ] `python scripts/validate_logs.py` vẫn 100/100 trên `main` sau merge
- [ ] Gửi R4 dòng đóng góp cá nhân cho mục 7 (đã soạn sẵn trong `notes-r1.md`)
- [ ] Nhắc R4 xoá `notes-r1.md` ở commit cuối (TEAMWORK.md §5.2 bước 4)

---

## 3. Lệnh kiểm tra lại toàn bộ phần R1

```powershell
# Terminal 1
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --env-file .env

# Terminal 2
Remove-Item data\logs.jsonl -ErrorAction SilentlyContinue
.venv\Scripts\python.exe scripts\load_test.py
.venv\Scripts\python.exe scripts\validate_logs.py     # ky vong: 100/100
.venv\Scripts\python.exe -m pytest -q                 # ky vong: 35 passed
```

Kết quả kỳ vọng của `validate_logs.py`:

```
--- Lab Verification Results ---
Total log records analyzed: 21
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 10
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
+ [PASSED] Basic JSON schema
+ [PASSED] Correlation ID propagation
+ [PASSED] Log enrichment
+ [PASSED] PII scrubbing

Estimated Score: 100/100
```

## 4. Tóm tắt trạng thái

| Nhóm việc | Trạng thái | Vướng ở đâu |
| --- | --- | --- |
| 7 TODO code của R1 | ✅ Xong | — |
| `validate_logs.py` ≥ 80 | ✅ 100/100 | — |
| Gitignore `data/logs.jsonl` | ✅ Xong | — |
| Test mới | ✅ 13 test, 35 passed | — |
| Evidence dạng text | ✅ Xong | — |
| `notes-r1.md` cho R4 | ✅ Xong | — |
| Ảnh chụp evidence (4 ảnh) | ⬜ Chưa | **Thủ công** — phải chụp màn hình |
| Push + merge vào `main` | ⬜ Chưa | **Chờ R4** (integrator duy nhất) |
| Điền `REPORT.md` | ⬜ Chưa | **Chờ R4** (chủ sở hữu duy nhất file) |
| Thêm trường log nếu R3 thiếu | ⬜ Chưa | **Chờ R3** báo |
| Chứng minh root cause K4 | ⬜ Chưa | **Chờ R4** chạy challenge (mốc 2:30) |
| Rà soát cuối | ⬜ Chưa | **Chờ** merge xong cả 4 nhánh |
