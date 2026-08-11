# R2 — Tracing & Prompt Version

## Triển khai

- `app/agent.py` tạo generation scope tường minh bằng cùng một Langfuse client cho generation và trace metadata. Mỗi trace ghi `user_id` đã hash, `session_id`, tags (`lab`, feature, model) và `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`.
- `app/tracing.py` dùng client singleton và flush các event Langfuse khi tiến trình kết thúc.
- Prompt text `day13-chat` trên Langfuse giữ đủ biến `{{feature}}`, `{{docs}}`, `{{message}}`.

## Prompt versions và labels đã xác minh

| Version | Labels | Nội dung thay đổi |
|---|---|---|
| v1 | `baseline`, `production` | Trả lời ngắn gọn theo tài liệu đã cung cấp. |
| v2 | `candidate` | Yêu cầu trả lời có bằng chứng và nêu rõ khi tài liệu không đủ. |

Đã chuyển `production` sang v2 để xác minh rồi rollback về v1. Trạng thái cuối: `production → v1`, `candidate → v2`.

## Trace IDs đã tạo trên Langfuse

| Label | Trace ID | Link |
|---|---|---|
| production (v1) | `7d6bd672b40a199bb38f15982553b59b` | [trace](https://cloud.langfuse.com/project/cmso26irx03c2ad0jh6oelzzd/traces/7d6bd672b40a199bb38f15982553b59b) |
| production (v1) | `7909a3d205b86385a1042917e137ba83` | Langfuse trace |
| production (v1) | `556e46c7031202f13657c377daddf392` | Langfuse trace |
| production (v1) | `eae209ad794ddaa68534bcc03446db38` | Langfuse trace |
| production (v1) | `afed83d4b8203efcdc881fc929d54063` | Langfuse trace |
| candidate (v2) | `0b2847f9197ab4864acf9eeef103f7fd` | [trace](https://cloud.langfuse.com/project/cmso26irx03c2ad0jh6oelzzd/traces/0b2847f9197ab4864acf9eeef103f7fd) |
| candidate (v2) | `2509a2bfc6fc48e730999e31e8d7deb3` | Langfuse trace |
| candidate (v2) | `905f4c839f73b7ac45b3f7e59b728c69` | Langfuse trace |
| candidate (v2) | `51cd3cce532a021a2df88c948ee85dcb` | Langfuse trace |
| candidate (v2) | `1183157140c24ecddc61dcb5c4feb5c7` | Langfuse trace |

Cùng input `How do we investigate an alert?` đã chạy qua v1/`production` và v2/`candidate`.

## Chứng minh đổi label và rollback

| Mốc | `production` version | Trace ID |
|---|---:|---|
| Sau khi chuyển sang v2 | 2 | `3a66d16295fcb62c3871ff80c952e92c` ([trace](https://cloud.langfuse.com/project/cmso26irx03c2ad0jh6oelzzd/traces/3a66d16295fcb62c3871ff80c952e92c)) |
| Sau rollback | 1 | `0f1cce8a6e85483311c887931c35a9c9` ([trace](https://cloud.langfuse.com/project/cmso26irx03c2ad0jh6oelzzd/traces/0f1cce8a6e85483311c887931c35a9c9)) |

## Kiểm tra mã nguồn

`uv run --python 3.13 python -m pytest tests/test_prompt_management.py tests/test_agent_prompt_trace.py tests/test_agent_trace_context.py tests/test_tracing_adapter.py tests/test_tracing_flush.py -q`
