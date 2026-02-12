import streamlit as st
import json
import time
from pathlib import Path
from datetime import datetime
import pandas as pd
from PIL import Image

st.set_page_config(
    page_title="Safety AI Dashboard",
    page_icon="🎥",
    layout="wide",
)

st.title("🎥 Safety CCTV AI Dashboard")

# Sidebar Configuration
st.sidebar.header("Configuration")
default_jsonl = "events.jsonl"
jsonl_path = st.sidebar.text_input("Events JSONL Path", default_jsonl)
snapshot_base = st.sidebar.text_input("Snapshot Base Dir", "/tmp/snapshots")
auto_refresh = st.sidebar.checkbox("Auto Refresh (1s)", value=True)

# Metrics placeholders
m1, m2, m3 = st.columns(3)
latest_event_container = st.container()
history_container = st.container()

def load_events(path, limit=100):
    events = []
    p = Path(path)
    if not p.exists():
        return []
    
    # Read last N lines efficiently would be better, but for demo just read all
    # and take tail.
    try:
        lines = p.read_text(encoding="utf-8").strip().splitlines()
        for line in lines[-limit:]:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except Exception as e:
        st.error(f"Error reading file: {e}")
    return events[::-1]  # Newest first

def get_snapshot_image(base_dir, relative_path):
    if not relative_path:
        return None
    # Handle both absolute and relative
    full_path = Path(base_dir) / relative_path
    if full_path.exists():
        return Image.open(full_path)
    # Check if path in jsonl is absolute
    abs_path = Path(relative_path)
    if abs_path.exists():
        return Image.open(abs_path)
    return None

placeholder = st.empty()

while True:
    with placeholder.container():
        events = load_events(jsonl_path, limit=50)
        
        if not events:
            st.warning(f"No events found at {jsonl_path}")
        else:
            # Metrics
            total_events = len(events) # In current window
            latest = events[0]
            last_ts = latest.get("ts", "N/A")
            event_types = pd.DataFrame(events)["event_type"].value_counts().to_dict()
            
            with m1:
                st.metric("Latest Event", last_ts)
            with m2:
                st.metric("Event Count (Window)", total_events)
            with m3:
                st.metric("Top Event Type", list(event_types.keys())[0] if event_types else "-")

            # Latest Event Detail
            st.subheader("🚨 Latest Detection")
            c1, c2 = st.columns([1, 1])
            with c1:
                # Image
                snap_path = latest.get("snapshot_path")
                if snap_path:
                    img = get_snapshot_image(snapshot_base, snap_path)
                    if img:
                        st.image(img, caption=f"{latest['event_type']} - {latest['confidence']:.2f}", use_container_width=True)
                    else:
                        st.info(f"Snapshot not found: {snap_path}")
                else:
                    st.info("No snapshot path in event")
            
            with c2:
                st.json(latest)

            # History Table
            st.subheader("📜 Event History")
            df = pd.DataFrame(events)
            # Select columns if they exist
            cols = ["ts", "event_type", "object_type", "confidence", "camera_id", "severity"]
            display_cols = [c for c in cols if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True)

    if not auto_refresh:
        break
    time.sleep(1)
