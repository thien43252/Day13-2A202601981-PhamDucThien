# R4 — TODO các vấn đề phát hiện (sửa sau)

> File note nội bộ của R4, **KHÔNG nộp**. Xoá file này trước commit cuối (giống `notes-r*.md`).
> Đây là danh sách việc phát hiện khi scaffold `REPORT.md`, chưa xử lý ngay.

---

## 1. `data/logs.jsonl` đang bị Git theo dõi (tracked) — ✅ ĐÃ XỬ LÝ

- **Hiện trạng cũ:** `git ls-files --stage data/logs.jsonl` trả ra dòng `100644 ...` → file nằm trong index.
- **Trạng thái:** ✅ R1 đã xử lý trong PR #1: file **không còn được track** (`git ls-files` rỗng) và `.gitignore` dòng 222 có `data/logs.jsonl`.
- **Còn lại nếu cần:** Nếu Lab Coach yêu cầu nộp log mẫu → R4 copy một snapshot đã redact vào `submission/evidence/logs-sample.jsonl` ở commit cuối, một lần duy nhất.

## 2. `submission/REPORT.md` bảng mục 1 ghi đảo vai trò R2/R3 — đã sửa

- **Hiện trạng:** Bảng cũ ghi Duy = "Dashboard, SLO & Alert", Thuận = "Tracing & Prompt Version" — **ngược** với TEAMWORK mục 1 (Duy = Tracing & Prompt Version 2A202601757; Thuận = Dashboard, SLO & Alert 2A202601949).
- **Trạng thái:** ✅ Đã sửa đúng trong bản scaffold mới. Nhắc R2/R3 để ý tên trong evidence theo đúng vai của mình.

## 3. Branch đang là `role-4`, hợp đồng Git ghi `feat/incident-report`

- **Hiện trạng:** `git branch --show-current` = `role-4`; TEAMWORK mục 2.4 quy định nhánh R4 là `feat/incident-report`.
- **Việc cần làm:** Xác nhận với nhóm đây là đổi tên có chủ đích hay nhầm. Nếu cần đúng hợp đồng:
  ```bash
  git branch -m feat/incident-report
  ```
  (Chỉ làm khi chắc chắn, hoặc thống nhất lại TEAMWORK mục 2.4.)

## 4. Vai trò trong `REPORT.md` mục 7 giữ đúng thứ tự R1→R4

- Sau khi mọi người gửi dòng đóng góp, R4 tổng hợp theo bảng — kiểm tra không đảo cột `Commit/PR` (lọc theo `git log --oneline --author=<mỗi người>`).

---

## Danh sách TODO đang chờ trong `REPORT.md` (cập nhật sau khi merge R1)

| Mục | Chờ ai | Trạng thái |
|---|---|---|
| Mục 2 — validate_logs | R1 | ✅ 100/100 đã điền, đã xác minh lại trên log mới (21 records, 10 correlation ID, 0 PII) |
| Mục 2 — traces | R2 | ⏳ TODO còn lại |
| Mục 2 — dashboard link | R3 | ⏳ TODO còn lại |
| Mục 3 — Logging | R1 | ✅ đã dán từ notes-r1.md; phần trace waterfall vẫn TODO(R2) |
| Mục 4 | R2 | ⏳ TODO còn lại |
| Mục 5 | R3 | ⏳ TODO còn lại (notes-r3.md + kiểm tra chéo slo↔dashboard) |
| Mục 6 | R4 (sau 2:30) | ⏳ chạy challenge chính thức |
| Mục 7 | cả nhóm | ✅ R1 đã điền; R2/R3/R4 TODO |

**Ghi chú khi merge R2/R3:** nhánh R4 cần `git fetch origin && git rebase origin/main` rồi kiểm tra REPORT không bị đè (REPORT là file duy nhất của R4 — nếu conflict, giữ bản R4 và lấy lại số liệu từ notes-r*).
