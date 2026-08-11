# R4 — TODO các vấn đề phát hiện (sửa sau)

> File note nội bộ của R4, **KHÔNG nộp**. Xoá file này trước commit cuối (giống `notes-r*.md`).
> Đây là danh sách việc phát hiện khi scaffold `REPORT.md`, chưa xử lý ngay.

---

## 1. `data/logs.jsonl` đang bị Git theo dõi (tracked) — nên gitignore

- **Hiện trạng:** `git ls-files --stage data/logs.jsonl` trả ra dòng `100644 ... data/logs.jsonl` → file đang ở trong index.
- **Vì sao phải sửa:** TEAMWORK mục 5.3 — file này append-only, 4 người commit sẽ conflict mọi dòng. Hợp đồng chốt: thêm `data/logs.jsonl` vào `.gitignore` (R1 làm trong commit đầu tiên), ai cần log tự sinh lại.
- **Kiểm tra hiện tại:** `.gitignore` **chưa có** dòng `data/logs.jsonl`.
- **Việc cần làm:**
  ```bash
  git rm --cached data/logs.jsonl
  echo "data/logs.jsonl" >> .gitignore
  ```
  Nếu Lab Coach yêu cầu nộp log mẫu → R4 copy một snapshot đã redact vào `submission/evidence/logs-sample.jsonl` ở commit cuối, một lần duy nhất.

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

## Danh sách TODO đang chờ trong `REPORT.md`

| Mục | Chờ ai | Nội dung |
|---|---|---|
| Mục 2 — validate_logs | R1 | cập nhật điểm sau khi đạt ≥80 |
| Mục 2 — traces | R2 | cập nhật tổng trace ≥10 có metadata |
| Mục 2 — dashboard link | R3 | URL/screenshot dashboard |
| Mục 3 | R1, R2 | notes-r1.md, notes-r2.md |
| Mục 4 | R2 | 2 trace ID + ảnh rollback |
| Mục 5 | R3 | notes-r3.md, kiểm tra chéo slo↔dashboard |
| Mục 6 | R4 (sau 2:30) | chạy challenge chính thức |
| Mục 7 | cả nhóm | mỗi người 1 dòng đóng góp |
