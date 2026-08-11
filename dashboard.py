"""Six-panel Streamlit dashboard for the Day 13 JSONL observability logs."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yaml


ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "data" / "logs.jsonl"
CONFIG_FILE = ROOT / "config" / "dashboard.yaml"


@st.cache_data(show_spinner=False)
def load_logs(path: str, modification_time: int) -> tuple[pd.DataFrame, list[str]]:
    """Read complete JSONL records; a malformed partial write does not stop the UI."""
    records, warnings = [], []
    file = Path(path)
    if not file.exists():
        return pd.DataFrame(), ["Không tìm thấy data/logs.jsonl. Hãy chạy load test trước."]
    for line_no, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            warnings.append(f"Bỏ qua JSON không hợp lệ ở dòng {line_no}.")
    data = pd.DataFrame(records)
    if data.empty or "ts" not in data:
        return pd.DataFrame(), [*warnings, "Không có event nào chứa timestamp `ts`."]
    data["ts"] = pd.to_datetime(data["ts"], utc=True, errors="coerce")
    data = data.dropna(subset=["ts"]).sort_values("ts")
    for field in ("latency_ms", "tokens_in", "tokens_out", "cost_usd", "quality_score"):
        if field in data:
            data[field] = pd.to_numeric(data[field], errors="coerce")
    return data, warnings


def within_window(data: pd.DataFrame, minutes: int) -> pd.DataFrame:
    if data.empty:
        return data
    return data[data["ts"] >= data["ts"].max() - timedelta(minutes=minutes)].copy()


def threshold(panel: dict) -> tuple[float, str]:
    spec = panel["threshold"]
    return float(spec["value"]), "≤" if spec["operator"] == "lte" else "≥"


def is_breach(value: float, panel: dict) -> bool:
    spec = panel["threshold"]
    return value > spec["value"] if spec["operator"] == "lte" else value < spec["value"]


def chart(data: pd.DataFrame, limit: float) -> None:
    if data.empty:
        st.info("Chưa có dữ liệu trong cửa sổ đã chọn.")
        return
    data = data.copy()
    data["SLO threshold"] = limit
    st.line_chart(data, height=240)


def event_data(data: pd.DataFrame, *events: str) -> pd.DataFrame:
    return data[data["event"].isin(events)].copy()


def metric_delta(value: float, panel: dict, ok: str) -> tuple[str, str]:
    return ("SLO breach", "inverse") if is_breach(value, panel) else (ok, "normal")


def latency_panel(data: pd.DataFrame, panel: dict) -> tuple[float, bool]:
    points = event_data(data, "response_sent").dropna(subset=["latency_ms"])
    value = points["latency_ms"].quantile(.95) if not points.empty else float("nan")
    limit, symbol = threshold(panel)
    st.subheader(panel["title"])
    st.caption(f"P50 / P95 / P99 · SLO P95 {symbol} {limit:,.0f} ms")
    delta, color = metric_delta(value, panel, "Trong SLO")
    st.metric("P95 latency", "—" if pd.isna(value) else f"{value:,.0f} ms", delta, delta_color=color)
    if not points.empty:
        grouped = points.set_index("ts")["latency_ms"].resample("1min")
        series = pd.DataFrame({"P50": grouped.quantile(.5), "P95": grouped.quantile(.95), "P99": grouped.quantile(.99)}).ffill()
        chart(series, limit)
    else:
        chart(pd.DataFrame(), limit)
    return value, is_breach(value, panel) if not pd.isna(value) else False


def traffic_panel(data: pd.DataFrame, panel: dict) -> tuple[float, bool]:
    points = event_data(data, "request_received")
    duration = max(1, (data.ts.max() - data.ts.min()).total_seconds() / 60) if not data.empty else 1
    value = len(points) / duration
    limit, symbol = threshold(panel)
    st.subheader(panel["title"])
    st.caption(f"request_received theo phút · signal floor {symbol} {limit:g} request/min")
    st.metric("Requests", f"{len(points):,}", f"{value:.2f} req/min")
    series = points.set_index("ts").resample("1min").size().rename("Requests/min").to_frame() if not points.empty else pd.DataFrame()
    chart(series, limit)
    return value, is_breach(value, panel)


def errors_panel(data: pd.DataFrame, panel: dict) -> tuple[float, bool]:
    received, failed = event_data(data, "request_received"), event_data(data, "request_failed")
    value = 100 * len(failed) / len(received) if len(received) else 0.0
    limit, symbol = threshold(panel)
    st.subheader(panel["title"])
    st.caption(f"request_failed / request_received · SLO {symbol} {limit:g}%")
    delta, color = metric_delta(value, panel, "Trong SLO")
    st.metric("Error rate", f"{value:.2f}%", delta, delta_color=color)
    if not data.empty:
        index = pd.date_range(data.ts.min().floor("min"), data.ts.max().ceil("min"), freq="1min", tz="UTC")
        denominator = received.set_index("ts").resample("1min").size().reindex(index, fill_value=0)
        numerator = failed.set_index("ts").resample("1min").size().reindex(index, fill_value=0)
        series = (100 * numerator / denominator.replace(0, pd.NA)).fillna(0).rename("Error rate %").to_frame()
        chart(series, limit)
    else:
        chart(pd.DataFrame(), limit)
    if not failed.empty and "error_type" in failed:
        st.caption("Breakdown: " + ", ".join(f"{k}: {v}" for k, v in failed.error_type.fillna("unknown").value_counts().items()))
    return value, is_breach(value, panel)


def cost_panel(data: pd.DataFrame, panel: dict) -> tuple[float, bool]:
    points = event_data(data, "response_sent").dropna(subset=["cost_usd"])
    value = points.cost_usd.sum() if not points.empty else 0.0
    limit, symbol = threshold(panel)
    st.subheader(panel["title"])
    st.caption(f"Tổng chi phí theo phút · budget {symbol} ${limit:g}")
    delta, color = metric_delta(value, panel, "Trong budget")
    st.metric("Window cost", f"${value:.4f}", delta, delta_color=color)
    series = points.set_index("ts").cost_usd.resample("1min").sum().cumsum().rename("Accumulated cost").to_frame() if not points.empty else pd.DataFrame()
    chart(series, limit)
    return value, is_breach(value, panel)


def tokens_panel(data: pd.DataFrame, panel: dict) -> tuple[float, bool]:
    points = event_data(data, "response_sent")
    tokens_in = points.get("tokens_in", pd.Series(dtype=float)).sum()
    tokens_out = points.get("tokens_out", pd.Series(dtype=float)).sum()
    value, limit = max(tokens_in, tokens_out), threshold(panel)[0]
    st.subheader(panel["title"])
    st.caption(f"Input / output tokens theo phút · per-field limit ≤ {limit:,.0f}")
    st.metric("Token usage", f"In {tokens_in:,.0f} · Out {tokens_out:,.0f}")
    series = points.set_index("ts")[["tokens_in", "tokens_out"]].resample("1min").sum() if not points.empty else pd.DataFrame()
    chart(series, limit)
    return value, value > limit


def quality_panel(data: pd.DataFrame, panel: dict) -> tuple[float, bool]:
    points = event_data(data, "response_sent").dropna(subset=["quality_score"])
    value = points.quality_score.mean() if not points.empty else float("nan")
    limit, symbol = threshold(panel)
    st.subheader(panel["title"])
    st.caption(f"Mean quality score · quality floor {symbol} {limit:.2f}")
    delta, color = metric_delta(value, panel, "Trong SLO")
    st.metric("Quality", "—" if pd.isna(value) else f"{value:.2f}", delta, delta_color=color)
    series = points.set_index("ts").quality_score.resample("1min").mean().ffill().rename("Mean quality").to_frame() if not points.empty else pd.DataFrame()
    chart(series, limit)
    return value, is_breach(value, panel) if not pd.isna(value) else False


def main() -> None:
    st.set_page_config(page_title="AI Observability", page_icon="📊", layout="wide")
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))["dashboard"]
    panels = {item["id"]: item for item in config["panels"]}
    st.sidebar.header("View controls")
    minutes = st.sidebar.selectbox("Time range", [15, 30, 60, 180, 1440], index=2, format_func=lambda n: f"Last {n} minutes")
    auto_refresh = st.sidebar.toggle("Auto refresh", value=True)
    st.sidebar.caption(f"Refresh interval: {config['refresh_seconds']} seconds")
    if st.sidebar.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
    st.sidebar.divider()
    st.sidebar.caption("Source: `data/logs.jsonl`")
    st.sidebar.caption("SLO values: `config/dashboard.yaml`")

    modified = LOG_FILE.stat().st_mtime_ns if LOG_FILE.exists() else 0
    data, warnings = load_logs(str(LOG_FILE), modified)
    data = within_window(data, minutes)
    st.title("Observability Control Center")
    latest = data.ts.max().strftime("%H:%M:%S UTC") if not data.empty else "no events"
    st.caption(f"Last {minutes} minutes · data interval 1 minute · latest event {latest}")
    for warning in warnings:
        st.warning(warning)

    renderers = [("latency", latency_panel), ("traffic", traffic_panel), ("errors", errors_panel), ("cost", cost_panel), ("tokens", tokens_panel), ("quality", quality_panel)]
    results = []
    for pair in (renderers[:2], renderers[2:4], renderers[4:]):
        for column, (panel_id, render) in zip(st.columns(2), pair):
            with column.container(border=True):
                _, breached = render(data, panels[panel_id])
                results.append((panels[panel_id]["title"], breached))
    breached = [title for title, value in results if value]
    (st.error if breached else st.success)("SLO threshold breach: " + ", ".join(breached) if breached else "All evaluated SLO thresholds are within target.")
    if auto_refresh:
        # This isolated component reloads the Streamlit page without blocking request handling.
        milliseconds = config["refresh_seconds"] * 1000
        components.html(
            f"<script>setTimeout(() => window.parent.location.reload(), {milliseconds});</script>",
            height=0,
        )


if __name__ == "__main__":
    main()