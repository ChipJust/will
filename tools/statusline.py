#!/usr/bin/env python3
"""
statusline.py — Claude Code status line script for the will agent ecosystem.
Reads JSON from stdin, writes a formatted status line to stdout.
Logs all raw input and errors (with tracebacks) to ~/.claude/statusline-debug.log.

Input sample
    {
        "session_id":"ca4b9956-b108-4737-a7d1-8d9801e0a07d",
        "transcript_path":"C:\\Users\\chipj\\.claude\\projects\\D---code-will\\ca4b9956-b108-4737-a7d1-8d9801e0a07d.jsonl",
        "cwd":"D:\\_code\\will",
        "model":{
            "id":"claude-sonnet-4-6",
            "display_name":"Sonnet 4.6"},
        "workspace":{
            "current_dir":"D:\\_code\\will",
            "project_dir":"D:\\_code\\will",
            "added_dirs":[
                "C:\\Users\\chipj\\.claude"]},
        "version":"2.1.104",
        "output_style":{
            "name":"default"},
        "cost":{
            "total_cost_usd":0.45525250000000006,
            "total_duration_ms":1371622,
            "total_api_duration_ms":236036,
            "total_lines_added":148,
            "total_lines_removed":2},
        "context_window":{
            "total_input_tokens":2076,
            "total_output_tokens":13188,
            "context_window_size":200000,
            "current_usage":{
                "input_tokens":1,
                "output_tokens":239,
                "cache_creation_input_tokens":1453,
                "cache_read_input_tokens":31521},
            "used_percentage":16,
            "remaining_percentage":84},
        "exceeds_200k_tokens":false
    }

Output sample
    Sonnet 4.6 | 32,974 / 200,000 (16%) | $0.46 | D:/_code/will


"""

import json
import os
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "statusline-debug.log"


def log(message: str) -> None:
    """Append a timestamped message to the debug log. Never raises."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except Exception:
        pass


def build_statusline(data: dict) -> str:
    return (
        f"{data.get('model', {}).get('display_name', 'Unknown Model')} | "
        f"{data.get('context_window', {}).get('current_usage', {}).get('cache_creation_input_tokens', 0) + data.get('context_window', {}).get('current_usage', {}).get('cache_read_input_tokens', 0):,} / "
        f"{data.get('context_window', {}).get('context_window_size', 0):,} "
        f"({data.get('context_window', {}).get('used_percentage', 0)}%) | "
        f"${data.get('cost', {}).get('total_cost_usd', 0):,.2f} | "
        f"{Path(data.get('cwd', 'UNKNOWN'))}"
    )



def main():
    raw = sys.stdin.read()

    log(f"=== CALL {datetime.now().isoformat()} ===")
    log(f"INPUT:\n{raw}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log(f"JSON parse error: {e}")
        print(f"JSON parse error: {e}")
        return

    try:
        line = build_statusline(data)
        print(line)
        log(f"OUTPUT: {line}")
    except Exception:
        tb = traceback.format_exc()
        log(f"ERROR building statusline:\n{tb}")
        print(f"statusline error — check {LOG_FILE}")


if __name__ == "__main__":
    main()
