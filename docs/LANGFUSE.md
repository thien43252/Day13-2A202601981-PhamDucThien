# Langfuse Integration Guide

This guide explains how to set up, connect to, and view traces in Langfuse for the Day 13 Observability Lab.

## Table of Contents

1. [Overview](#overview)
2. [Quick Setup](#quick-setup)
3. [Langfuse Dashboard](#langfuse-dashboard)
4. [Environment Variables](#environment-variables)
5. [How Tracing Works](#how-tracing-works)
6. [Files Using Langfuse](#files-using-langfuse)
7. [Viewing Traces](#viewing-traces)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Langfuse is an open-source LLM observability platform that tracks:
- **Traces**: Complete request flows from user input to agent response
- **Generations**: Individual LLM calls with tokens, costs, and model metadata
- **Prompt Versions**: Managed prompts with version control and A/B testing
- **Metadata**: Custom tags, user IDs, session IDs, and structured data

In this lab, Langfuse captures:
- User queries and agent responses
- Token counts and cost estimation
- Prompt versions (managed vs. local fallback)
- Quality scores and latency metrics
- Correlation IDs for request tracking

---

## Quick Setup

### 1. Sign up or get credentials from Lab Coach

- Visit [https://cloud.langfuse.com](https://cloud.langfuse.com)
- Create an account or use your lab project credentials provided by Lab Coach

### 2. Get your API keys

In the Langfuse dashboard:
1. Go to **Settings → API Keys**
2. Copy your **Public Key** (starts with `pk-lf-`)
3. Copy your **Secret Key** (starts with `sk-lf-`)

### 3. Update `.env` file

Create or edit `.env` in the project root:

```dotenv
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PROMPT_NAME=day13-chat
LANGFUSE_PROMPT_LABEL=production
```

### 4. Start the app with tracing enabled

**Terminal 1: Start the FastAPI server**
```bash
uvicorn app.main:app --reload --env-file .env
```

App output should show:
```
app_started service=day13-observability-lab ... payload={"tracing_enabled": true}
```

**Terminal 2: Generate and collect traces**
```bash
python scripts/check_langfuse_traces.py
```

This script will:
1. Send 5 test requests to the running app
2. Wait briefly for server to process and flush events
3. Fetch up to 20 traces from Langfuse Cloud
4. Display trace IDs and metadata

### 5. View traces in Langfuse Dashboard

- Open [https://cloud.langfuse.com](https://cloud.langfuse.com)
- Click **Traces** in the left sidebar
- Traces should appear with tag `"lab"`

---

## Langfuse Dashboard

### Accessing the Dashboard

- **Cloud**: [https://cloud.langfuse.com](https://cloud.langfuse.com)
- Navigate using the left sidebar

### Key Dashboard Sections

#### 1. **Traces View**
- Shows all captured traces (complete request flows)
- **Click on a trace** to see:
  - Trace ID and timing
  - User ID, session ID, tags
  - Full request/response metadata
  - Associated generations (LLM calls)

#### 2. **Generations View**
- Individual LLM calls within traces
- Shows:
  - Model name (e.g., `claude-sonnet-4-5`)
  - Tokens consumed (input/output)
  - Estimated cost
  - Latency
  - Temperature, max_tokens, etc.

#### 3. **Prompt Management**
- View all managed prompts and versions
- See which traces used each prompt version
- Compare versions side-by-side
- Mark versions as active/archived

#### 4. **Analytics & Monitoring**
- Cost breakdown by model
- Latency distribution
- Token usage trends
- Error/failure rates
- Custom metrics dashboard

---

## Environment Variables

| Variable | Purpose | Example | Required |
|----------|---------|---------|----------|
| `LANGFUSE_PUBLIC_KEY` | Authentication (public) | `pk-lf-xxx` | Yes* |
| `LANGFUSE_SECRET_KEY` | Authentication (private) | `sk-lf-xxx` | Yes* |
| `LANGFUSE_HOST` | Langfuse server URL | `https://cloud.langfuse.com` | No (default: cloud) |
| `LANGFUSE_PROMPT_NAME` | Managed prompt name | `day13-chat` | No (default: `day13-chat`) |
| `LANGFUSE_PROMPT_LABEL` | Prompt version label | `production` | No (default: `production`) |

**\* Required for tracing to work. App will run with local prompts if keys are missing, but traces won't be sent to Langfuse.**

### What happens without keys?

- ✅ API still works (using local prompts)
- ✅ Logs and metrics are recorded locally
- ✅ Unit tests pass
- ❌ No traces sent to Langfuse
- ❌ No prompt version tracking
- ❌ No observability evidence

---

## How Tracing Works

### Tracing Flow

```
User Request → FastAPI Handler
    ↓
LabAgent.run()
    ↓
[Langfuse Trace Started]
    ├─ Retrieve context (RAG docs)
    ├─ Resolve prompt (managed or local)
    ├─ Generate response (LLM call)
    │   └─ [Langfuse Generation Created]
    ├─ Update trace metadata (tags, user_id, session_id)
    ├─ Update generation metadata (tokens, cost, prompt version)
    └─ Get trace ID
    ↓
Return response with trace ID
    ↓
[On app shutdown] → Flush buffered events to Langfuse
```

### Key Decorators & Functions

#### `@observe` Decorator
```python
from langfuse import observe

@observe()
def some_function():
    # This function's execution will be traced
    pass
```
**Currently not used** in this lab, but can be applied to any function for automatic tracing.

#### Tracing Functions

| Function | Purpose |
|----------|---------|
| `get_langfuse_client()` | Get the singleton Langfuse client |
| `tracing_enabled()` | Check if tracing is configured |
| `flush_langfuse()` | Force flush buffered events (called on shutdown) |

---

## Files Using Langfuse

### 1. **[app/tracing.py](app/tracing.py)** — Core Tracing Module

**Purpose**: Initialize and manage Langfuse client connection.

**Key Components**:
- `get_langfuse_client()`: Returns singleton Langfuse client or dummy client if SDK unavailable
- `flush_langfuse()`: Sends buffered events to Langfuse without blocking shutdown
- `tracing_enabled()`: Returns `True` if both public and secret keys are in environment

**Features**:
- Graceful fallback if Langfuse SDK not installed
- Automatic flush on app shutdown (registered with `atexit`)
- Handles errors gracefully (tracing never blocks app execution)

**Usage**:
```python
from app.tracing import get_langfuse_client, tracing_enabled

client = get_langfuse_client()
if tracing_enabled():
    # Send traces
    pass
```

---

### 2. **[app/agent.py](app/agent.py)** — Agent Tracing Logic

**Purpose**: Main AI agent that creates traces for each request.

**Key Components**:

#### `LabAgent.run()` Method
```python
def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
```

**What it traces**:
1. **Trace Setup** (context manager `_generation_scope`)
   - Starts LLM generation with model name
   - Ends generation on function exit

2. **Trace Metadata** via `langfuse_client.update_current_trace()`
   ```python
   langfuse_client.update_current_trace(
       user_id=hash_user_id(user_id),        # Hashed for PII protection
       session_id=session_id,
       tags=["lab", feature, self.model],
       metadata={
           "prompt_name": prompt.name,
           "prompt_label": prompt.label,
           "prompt_version": prompt.version,    # e.g., "v123" or "local-v1"
           "prompt_source": prompt.source,      # "langfuse" or "local-fallback"
       },
   )
   ```

3. **Generation Metadata** via `langfuse_client.update_current_generation()`
   ```python
   langfuse_client.update_current_generation(
       model=self.model,
       metadata={
           "doc_count": len(docs),
           "query_preview": summarize_text(message),
           "prompt_name": prompt.name,
           "prompt_version": prompt.version,
           "prompt_source": prompt.source,
           "prompt_fetch_error": prompt.fetch_error,  # "LangfuseFallback" if failed
       },
       usage_details={
           "prompt_tokens": response.usage.input_tokens,
           "completion_tokens": response.usage.output_tokens,
       },
       cost_details={"total": cost_usd},
       prompt=prompt.managed_prompt,  # Links to managed prompt in Langfuse
   )
   ```

**Trace ID Capture**:
```python
get_trace_id = getattr(langfuse_client, "get_current_trace_id", lambda: None)
trace_id = get_trace_id()  # Returned in AgentResult
```

**Returned in Response**:
```python
AgentResult(
    trace_id=trace_id,  # Can be displayed to user or logged
    ...
)
```

**Functions It Uses**:
| Function | Source | Purpose |
|----------|--------|---------|
| `get_langfuse_client()` | `app.tracing` | Get Langfuse client |
| `tracing_enabled()` | `app.tracing` | Check if tracing active |
| `resolve_prompt()` | `app.prompt_management` | Get managed or local prompt |
| `retrieve()` | `app.mock_rag` | Fetch context docs |
| `hash_user_id()` | `app.pii` | Hash user ID for privacy |

---

### 3. **[app/prompt_management.py](app/prompt_management.py)** — Prompt Versioning

**Purpose**: Fetch and resolve managed prompts from Langfuse, with automatic fallback to local prompts.

**Key Function**: `resolve_prompt()`
```python
def resolve_prompt(
    client: Any,
    *,
    feature: str,
    docs: list[str],
    message: str,
    enabled: bool,
) -> ResolvedPrompt:
```

**How it works:**
1. Attempts to fetch managed prompt from Langfuse using:
   ```python
   managed_prompt = client.get_prompt(
       name=os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat"),
       label=os.getenv("LANGFUSE_PROMPT_LABEL", "production"),
       type="text",
       fallback=DEFAULT_PROMPT_TEMPLATE,
       cache_ttl_seconds=60,           # Cache for 60s
       fetch_timeout_seconds=2,         # Don't wait too long
       max_retries=0,                   # No retries (fail fast)
   )
   ```

2. **Success** → Returns managed prompt with metadata:
   - `source="langfuse"`
   - `version=managed_prompt.version` (e.g., "123")

3. **Fallback** → Falls back to local prompt if:
   - `enabled=False` (Langfuse disabled)
   - Fetch times out (2 seconds)
   - Fetch returns fallback marker
   - Any exception occurs

   Returns:
   - `source="local-fallback"`
   - `version="local-v1"`
   - `fetch_error` with reason (e.g., `"LangfuseFallback"`, `"TimeoutError"`)

**ResolvedPrompt Data**:
```python
@dataclass
class ResolvedPrompt:
    text: str                     # Final compiled prompt text
    name: str                     # Prompt name (e.g., "day13-chat")
    label: str                    # Label used (e.g., "production")
    version: str                  # Version ID or "local-v1"
    source: str                   # "langfuse" or "local-fallback"
    managed_prompt: Any | None    # Reference to managed prompt object
    fetch_error: str | None       # Error reason if applicable
```

---

### 4. **[app/main.py](app/main.py)** — FastAPI Application

**Purpose**: Provides HTTP API and health endpoints that expose tracing status.

**Tracing Usage**:

#### Health Endpoint
```python
@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "tracing_enabled": tracing_enabled(),  # Reports if Langfuse configured
        "incidents": status()
    }
```

**Health check can verify**:
- `curl http://127.0.0.1:8000/health`
- Check if `tracing_enabled` is `true`

#### Startup Logging
```python
@app.on_event("startup")
async def startup() -> None:
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "day13-observability-lab"),
        env=os.getenv("APP_ENV", "dev"),
        payload={"tracing_enabled": tracing_enabled()},  # Logs tracing status
    )
```

**Chat Endpoint**:
- Calls `LabAgent.run()` which creates Langfuse traces
- Returns trace ID in response (if enabled)

---

### 5. **[tests/test_tracing_flush.py](tests/test_tracing_flush.py)** — Flush Tests

**Purpose**: Verify that buffered Langfuse events are properly flushed.

**Test Cases**:
1. `test_flush_langfuse_flushes_buffered_events()` — Ensures flush is called
2. `test_flush_langfuse_ignores_clients_without_flush()` — Handles gracefully
3. `test_flush_langfuse_does_not_initialize_a_client_when_disabled()` — No-op when disabled

**Why it matters**: Langfuse buffers events for efficiency; shutdown must flush to prevent data loss.

---

### 6. **[scripts/check_langfuse_traces.py](scripts/check_langfuse_traces.py)** — Test Generator & Trace Collector

**Purpose**: Automatically send test requests and collect traces from Langfuse Cloud.

**How to use**:
```bash
python scripts/check_langfuse_traces.py
```

**What it does**:
1. Loads test queries from `data/sample_queries.jsonl`
2. Sends requests to the running app (generates traces)
3. Waits for server to flush events to Langfuse
4. Attempts to fetch up to 20 traces from Langfuse Cloud
5. Displays trace IDs and metadata

**Output example**:
```
Client type: <class 'langfuse.client.Langfuse'>
[attempt] client.list_traces(limit=20) -> returned 5 items
Collected traces (up to 20):
[
  {
    "id": "trace-abc123...",
    "start_time": "2024-01-15T10:30:00Z",
    "tags": ["lab", "docs-rewrite", "claude-sonnet-4-5"]
  },
  ...
]
SUCCESS: traces found
```

---

## Viewing Traces

### Step-by-Step: Find Your Traces

1. **Start the app**
   ```bash
   uvicorn app.main:app --reload --env-file .env
   ```

2. **Generate some traces**
   ```bash
   python scripts/load_test.py
   ```

3. **Open Langfuse Dashboard**
   - Cloud: [https://cloud.langfuse.com](https://cloud.langfuse.com)
   - Local: [http://localhost:3000](http://localhost:3000)

4. **Navigate to Traces**
   - Click **Traces** in the left sidebar
   - You should see traces with names like `lab-agent.run`

5. **Click a trace to view details**
   - **Trace ID**: Unique identifier
   - **User ID**: Hashed user identifier
   - **Session ID**: Grouped requests
   - **Tags**: `["lab", "<feature>", "<model>"]`
   - **Metadata**: Prompt name, version, source
   - **Timeline**: Nested generations with timing

### Understanding Trace Details

**Example Trace**:
```
Trace ID: abc123def456
├─ User ID: (hashed)
├─ Session ID: sess-xxxx
├─ Tags: lab, docs-rewrite, claude-sonnet-4-5
├─ Start Time: 2024-01-15T10:30:00Z
├─ Duration: 245 ms
│
└─ Generation: lab-agent.run
   ├─ Model: claude-sonnet-4-5
   ├─ Input Tokens: 450
   ├─ Output Tokens: 128
   ├─ Total Cost: $0.0032
   ├─ Latency: 245 ms
   └─ Metadata:
      ├─ prompt_name: day13-chat
      ├─ prompt_version: 42
      ├─ prompt_source: langfuse
      ├─ doc_count: 3
      └─ query_preview: What is...
```

### Filtering Traces

In the Traces view, use filters:
- **Model**: `claude-sonnet-4-5`, etc.
- **Tags**: Search for specific feature tags
- **User ID**: Find traces for a specific user
- **Session ID**: Group related interactions
- **Time Range**: Last 24h, 7d, custom

### Comparing Prompt Versions

1. Go to **Prompts** in the sidebar
2. Find `day13-chat` prompt
3. Click to see all versions
4. Click **Compare** to see differences
5. See which traces used each version

---

## Troubleshooting

### Problem: "Tracing not enabled" / No traces appearing

**Check 1: Verify environment variables**
```bash
# In your terminal where the app is running:
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY
```

**Check 2: Verify .env file**
```bash
# Make sure .env contains:
cat .env | grep LANGFUSE
```

**Check 3: Reload the app**
```bash
# Stop the app (Ctrl+C) and restart
uvicorn app.main:app --reload --env-file .env
```

**Check 4: Health endpoint**
```bash
curl http://127.0.0.1:8000/health
# Should show: "tracing_enabled": true
```

---

### Problem: "Prompt source: local-fallback" instead of "langfuse"

**Possible causes**:

1. **Wrong prompt name or label**
   ```bash
   # Check what you're using
   grep LANGFUSE_PROMPT .env
   # Should match prompt name in Langfuse dashboard
   ```

2. **Langfuse unreachable**
   - Verify Langfuse is running (cloud or local)
   - Test connectivity: `ping cloud.langfuse.com`
   - Check `LANGFUSE_HOST` in `.env`

3. **Wrong credentials**
   - Verify public/secret keys match your project
   - Test in Langfuse dashboard: Settings → API Keys

4. **Prompt not created yet**
   - In Langfuse, create a prompt named `day13-chat` with label `production`
   - Or set different name/label in `.env`

**Fix**: Wait 60 seconds (cache TTL) and try again.

---

### Problem: "LANGFUSE_SDK_AVAILABLE = False"

**Cause**: Langfuse package not installed.

**Fix**:
```bash
pip install langfuse
# or
pip install -r requirements.txt
```

---

### Problem: 401 Unauthorized errors in logs

**Cause**: Invalid public/secret keys or expired credentials.

**Fix**:
1. Get fresh keys from Langfuse dashboard: **Settings → API Keys**
2. Update `.env` with correct public/secret keys
3. Restart the app: `Ctrl+C` then run `uvicorn app.main:app --reload --env-file .env`
4. Verify health endpoint: `curl http://127.0.0.1:8000/health`

---

### Problem: App shows "tracing_enabled: false" but I have keys set

**Cause**: `.env` file not loaded or keys are empty strings.

**Fix**:
1. Verify `.env` file has non-empty keys:
   ```bash
   cat .env | grep LANGFUSE
   ```
2. Verify app started with `--env-file .env`:
   ```bash
   uvicorn app.main:app --reload --env-file .env
   ```
3. Restart the app after any `.env` changes

---

### Problem: Still no traces after running check_langfuse_traces

**Checklist**:
1. App is running: `curl http://127.0.0.1:8000/health` should return `{"ok":true,"tracing_enabled":true,...}`
2. `.env` file has valid Langfuse credentials
3. Network connection to `https://cloud.langfuse.com` is available (no corporate proxy blocking)
4. Wait 2-3 seconds for server to flush events to Langfuse
5. Check Langfuse dashboard after traces are collected:
   - Open [https://cloud.langfuse.com](https://cloud.langfuse.com)
   - Click **Traces** in sidebar
   - Filter by tag `"lab"`

---

## Summary

| Aspect | Details |
|--------|---------|
| **Core Library** | `langfuse==3.2.1` (Python SDK) |
| **Configuration** | `.env` file with 3 required variables |
| **Entry Point** | `app/tracing.py` (initialization & client management) |
| **Main Tracer** | `app/agent.py` → `LabAgent.run()` method |
| **Prompt Versioning** | `app/prompt_management.py` → `resolve_prompt()` |
| **Health Check** | `GET /health` → reports `tracing_enabled` |
| **Dashboard** | [cloud.langfuse.com](https://cloud.langfuse.com) |
| **Key Metrics** | Tokens, cost, latency, quality, prompt version, user ID, session ID |
| **Shutdown Flush** | Automatic via `atexit.register(flush_langfuse)` |

---

## Quick Reference

### Common Commands

**Start app with tracing enabled**:
```bash
uvicorn app.main:app --reload --env-file .env
```

**Generate traces and collect results**:
```bash
python scripts/check_langfuse_traces.py
```

**Check tracing status**:
```bash
curl http://127.0.0.1:8000/health
```

**View traces in Langfuse**:
- Open [https://cloud.langfuse.com](https://cloud.langfuse.com)
- Click **Traces** in sidebar
- Click any trace to drill down

### Files at a Glance

| File | Purpose |
|------|---------|
| `app/tracing.py` | Client lifecycle & flush logic |
| `app/agent.py` | Creates traces for each request |
| `app/prompt_management.py` | Fetches managed prompts, with fallback |
| `app/main.py` | FastAPI app, health endpoint |
| `scripts/check_langfuse_traces.py` | Send test requests and collect traces |
| `tests/test_tracing_flush.py` | Verify shutdown behavior |
| `.env` | Configuration (LANGFUSE_*) |

---

## Related Documentation

- [SETUP.md](SETUP.md) — Initial setup instructions
- [README.md](README.md) — Project overview
- [Langfuse Docs](https://langfuse.com/docs) — Official documentation
- [Langfuse Python SDK](https://github.com/langfuse/langfuse-python) — Source code
