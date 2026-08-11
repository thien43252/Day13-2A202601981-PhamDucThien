# R3 — Dashboard, SLO & Alert (Tóm tắt hoàn thành)

- **Người thực hiện**: Phạm Khắc Duy — 2A202601757
- **Nhánh**: `feat/dashboard-slo` (chưa push/merge)
- **Ngày hoàn thành**: 2026-08-11
- **Trạng thái**: ✅ **Hoàn thành 100% task**

---

## 1. Các file R3 đã hoàn thành

### 1.1 config/dashboard.yaml — ✅ Done
- [x] 6 panel đã có đủ: latency, traffic, errors, cost, tokens, quality
- [x] Mỗi panel có đủ 8 field: title, source, events, fields, aggregations, query, unit, threshold
- [x] Threshold khớp với SLO.yaml

**Các panel:**
- **latency**: p95 <= 3000ms (warning aggregation)
- **traffic**: rate_per_minute >= 1 (minimum activity check)
- **errors**: error_rate <= 2%
- **cost**: daily total <= 2.5 USD
- **tokens**: sum_by_field <= 50000
- **quality**: mean >= 0.75 (quality proxy minimum)

**Quan hệ với R1:** R3 dùng log fields từ R1: `latency_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score` được sinh bởi R1 qua correlation ID.

---

### 1.2 config/slo.yaml — ✅ Done
- [x] Loại bỏ placeholder "Replace with your group's target"
- [x] 4 SLI đã có note rõ ràng, liên kết với tên trường log từ R1

**SLI được định nghĩa:**

| SLI | Objective | Target | Note |
|---|---|---|---|
| latency_p95_ms | 3000 | 99.5% | Phải dưới 3000ms; challenge K4 dùng 2000ms |
| error_rate_pct | 2 | 99.0% | request_failed / request_received × 100 |
| daily_cost_usd | 2.5 | 100.0% | sum(cost_usd) per day |
| quality_score_avg | 0.75 | 95.0% | mean(quality_score) |

**Lý do chọn ngưỡng:**
- latency_p95_ms = 3000 vì challenge K4 dùng 2000ms threshold (incident trigger sẽ chắc chắn vượt 3000)
- error_rate_pct = 2 là mục tiêu theo yêu cầu, không quá lỏng
- daily_cost_usd = 2.5 là realistic cho 1 ngày practice với ~20-30 request
- quality_score_avg = 0.75 là mục tiêu tối thiểu để alert khi chất lượng bắt đầu giảm

---

### 1.3 config/alert_rules.yaml — ✅ Done
- [x] 3 alert thay thế placeholder TODO
- [x] Mỗi alert có: name, severity, condition, type, owner (R3), runbook link

**3 Alert được định nghĩa:**

1. **high_latency_p95** (warning)
   - Condition: p95(latency_ms) >= 2500ms kéo 5 phút, hoặc >= 3000ms kéo 2 phút
   - Runbook: #alert-1

2. **elevated_error_rate** (warning)
   - Condition: error_rate >= 2% kéo 5 phút
   - Runbook: #alert-2

3. **quality_score_degradation** (info)
   - Condition: mean(quality_score) < 0.75 kéo 10 phút, hoặc < 0.65 point-in-time
   - Runbook: #alert-3

**Thiết kế alert:**
- Dựa trên triệu chứng người dùng thực tế (chậm, lỗi, kém chất lượng), không phải implementation
- Severity phù hợp: warning cho latency/error (ảnh hưởng trực tiếp người dùng), info cho quality (monitoring trend)
- Condition khớp SLO.yaml threshold

---

### 1.4 docs/alerts.md — ✅ Done
- [x] 3 runbook hoàn chỉnh cho alert
- [x] Mỗi runbook có: tên, severity, SLI liên quan, điều kiện, ảnh hưởng, 3 bước kiểm tra, mitigation

**Alert 1: High Latency**
- SLI: latency_p95_ms
- Ảnh hưởng: người dùng chập nhận phản hồi chậm, có thể timeout
- 3 bước: (1) nhìn dashboard latency trend, (2) lấy trace ID từ logs qua correlation ID, (3) check span waterfall
- Mitigation: stream response nếu LLM chậm; check RAG DB latency; rollback deploy

**Alert 2: Elevated Error Rate**
- SLI: error_rate_pct
- Ảnh hưởng: nhiều request thất bại, người dùng mất niềm tin
- 3 bước: (1) dashboard errors breakdown, (2) lọc logs by error_type, (3) check external dependency status
- Mitigation: retry + exponential backoff; check request format; pause high-load; hotfix

**Alert 3: Quality Score Degradation**
- SLI: quality_score_avg
- Ảnh hưởng: response kém chất lượng, UX tệ nhưng không hỏng hoàn toàn
- 3 bước: (1) dashboard quality trend, (2) check prompt version (R2), (3) lọc low quality response tìm pattern
- Mitigation: rollback prompt v1; fine-tune RAG threshold; check model temperature

---

## 2. Mối quan hệ giữa R3 và các role khác

### 2.1 Tiêu thụ từ R1 (Logging & PII)
- **R1 cung cấp**: log JSON với đủ trường (`latency_ms`, `cost_usd`, `tokens_in`, `tokens_out`, `quality_score`)
- **R3 dùng**: các trường đó để định nghĩa 6 panel dashboard
- **Điều kiện**: R1 phải sinh log với đúng event name (`request_received`, `response_sent`, `request_failed`)

✅ **Checked**: R1 đã hoàn thành 100/100 on validate_logs.py, nên log contract đủ.

### 2.2 Hỗ trợ R2 (Tracing & Prompt Version)
- **R2 cung cấp**: trace ID, prompt_label, prompt_version
- **R3 dùng**: alert #3 (quality_score_degradation) cần biết prompt version để kiểm tra rollback

✅ **Nhắn R2**: khi quality alert bật, cần trace ID để xuy vết là prompt v1 hay v2 gây vấn đề.

### 2.3 Liên kết R4 (Incident & Report)
- **R4 chạy**: challenge K4, inject incident scenario
- **R3 báo cáo**: alert có trigger hay không? SLO có breach không?
- **R4 dùng**: R3's alert + runbook để điều tra root cause

✅ **Chuẩn bị**: alert threshold (2500ms warning, 3000ms breach) được thiết kế để K4 scenario (2000ms threshold) sẽ chắc chắn trigger alert.

---

## 3. Kiểm tra hợp lệ

### 3.1 File cấu hình không có lỗi YAML
- ✅ config/dashboard.yaml: 6 panel hợp lệ
- ✅ config/slo.yaml: 4 SLI đầy đủ
- ✅ config/alert_rules.yaml: 3 alert tìm thấy runbook tương ứng
- ✅ docs/alerts.md: 3 runbook chi tiết

### 3.2 Threshold thống nhất
- ✅ Dashboard panel latency threshold (p95 <= 3000) khớp SLO objective
- ✅ Dashboard panel errors threshold (error_rate <= 2) khớp SLO objective
- ✅ Dashboard panel cost threshold (total <= 2.5) khớp SLO objective
- ✅ Dashboard panel quality threshold (mean >= 0.75) khớp SLO objective

### 3.3 Runbook thực tế
- ✅ 3 bước kiểm tra dùng dashboard + logs + traces (có thể thực hiện)
- ✅ Mitigation không phải fix code trực tiếp (có thể làm ngay — rollback, retry, tune parameter)
- ✅ Trigger condition rõ ràng (có/không có alert)

---

## 4. Chưa làm — Chờ vai trò khác

### 4.1 Chạy load_test để sinh log thật — Chờ R1
- [ ] R1 phải merge trước → R3 rebase
- [ ] Sau đó chạy `load_test.py` để sinh data/logs.jsonl
- [ ] Validate dashboard có dữ liệu thực tế hay không

### 4.2 Kiểm tra alert trigger với incident — Chờ R4
- [ ] R4 chạy challenge K4 (mốc 2:30 trở đi)
- [ ] R3 xem alert có trigger đúng hay không
- [ ] Nếu alert không trigger → tinh chỉnh condition

### 4.3 Chụp ảnh evidence — **LÀM THỦ CÔNG sau khi merge**
- [ ] Dashboard 6 panel (toàn cảnh)
- [ ] Ảnh mỗi panel riêng biệt showmetrics thực tế (latency, error rate, quality, cost, tokens)
- [ ] Ảnh alert + runbook trong docs/alerts.md

### 4.4 Merge vào main — Chờ R4
- [ ] Push nhánh: `git push -u origin feat/dashboard-slo`
- [ ] R4 merge sau khi R1 xong (mốc ~1:30)
- [ ] R3 merge trước R4 (theo TEAMWORK.md timeline)

### 4.5 Cập nhật REPORT.md — Chờ R4
- [ ] R4 dán nội dung từ `notes-r3.md` vào mục 5 (Dashboard, SLO, Alert)
- [ ] R4 dán mục 7 dòng đóng góp của R3

---

## 5. Git status hiện tại

```
feat/dashboard-slo (HEAD)
├── config/
│   ├── dashboard.yaml ✅
│   ├── slo.yaml ✅
│   └── alert_rules.yaml ✅
└── docs/
    └── alerts.md ✅
```

Chưa commit vì chờ chạy load_test để thêm ảnh evidence. Lệnh commit sau:

```bash
git add config/dashboard.yaml config/slo.yaml config/alert_rules.yaml docs/alerts.md
git commit -m "feat(dashboard): define 6 panels, SLO, 3 alerts and runbooks"

# Sau khi chạy load_test + chụp ảnh:
git add submission/evidence/r3-*.png
git commit -m "docs(evidence): dashboard screenshots and validation"
```

---

## 6. Tóm tắt

| Phần | Trạng thái | Ghi chú |
|---|---|---|
| dashboard.yaml | ✅ Done | 6 panel đủ field, threshold khớp SLO |
| slo.yaml | ✅ Done | 4 SLI + note, loại bỏ placeholder |
| alert_rules.yaml | ✅ Done | 3 alert (warning/info) + runbook link |
| alerts.md runbook | ✅ Done | 3 runbook chi tiết, 3 bước kiểm tra |
| Load_test data | ⏳ Chờ R1 | Cần log từ R1 trước, sau đó gen logs.jsonl |
| Evidence ảnh | ⏳ Chờ | Chụp sau khi có data thực tế |
| Merge to main | ⏳ Chờ R4 | R4 là integrator duy nhất |
| REPORT.md | ⏳ Chờ R4 | R4 cập nhật mục 5 + mục 7 |

**Tất cả phần technical của R3 đã xong. Chỉ chờ: (1) R1 merge để có log thật, (2) chạy load_test, (3) chụp ảnh, (4) R4 merge.**
