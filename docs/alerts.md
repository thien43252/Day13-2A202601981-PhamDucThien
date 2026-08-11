# Alert và Runbook — Day 13 Observability

Mỗi alert dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1: High Latency (p95)

- **Tên**: `high_latency_p95`
- **Severity**: warning
- **SLI/SLO liên quan**: `latency_p95_ms` — objective 3000ms, target 99.5%
- **Điều kiện**: p95(latency_ms) >= 2500ms liên tục 5 phút, hoặc >= 3000ms kéo 2 phút
- **Ảnh hưởng**: Người dùng cảm nhận phản hồi chậm, có thể timeout. UX bị ảnh hưởng nặng.
- **Ba bước kiểm tra**:
  1. Nhìn dashboard panel latency: xem p50, p95, p99 có tăng không
  2. Lấy trace ID của request chậm từ logs dùng correlation ID
  3. Kiểm tra span waterfall: span nào chậm nhất?
- **Mitigation**: Nếu LLM chậm bật stream; nếu RAG check DB; nếu systemic rollback deploy
- **Owner**: R3

---

- **Tên**: `elevated_error_rate`
- **Severity**: warning
- **SLI/SLO liên quan**: `error_rate_pct` — objective 2%, target 99.0%
- **Điều kiện**: error_rate >= 2% liên tục 5 phút
- **Ảnh hưởng**: Tỷ lệ lớn request thất bại, người dùng mất niềm tin.
- **Ba bước kiểm tra**:
  1. Nhìn dashboard panel errors: breakdown by error_type
  2. Lọc logs theo error_type chính để xem chi tiết
  3. Kiểm tra external dependency (LLM API, RAG DB)
- **Mitigation**: Tăng timeout + retry; check request format; pause high-load; deploy hotfix
- **Owner**: R3

---

- **Tên**: `quality_score_degradation`
- **Severity**: info
- **SLI/SLO liên quan**: `quality_score_avg` — objective 0.75, target 95.0%
- **Điều kiện**: mean(quality_score) < 0.75 liên tục 10 phút
- **Ảnh hưởng**: Response kém chất lượng, UX tệ nhưng không hỏng toàn bộ.
- **Ba bước kiểm tra**:
  1. Nhìn dashboard panel quality: trend có drop không
  2. Kiểm tra prompt version (R2): v1 hay v2?
  3. Lọc response quality_score thấp tìm pattern
- **Mitigation**: Rollback v1 nếu v2 kém; fine-tune RAG; check model temp
- **Owner**: R3

---

## Ghi chú chung

- Tất cả alert dựa trên triệu chứng người dùng, không phải implementation detail
- Threshold phải khớp dashboard.yaml và slo.yaml
