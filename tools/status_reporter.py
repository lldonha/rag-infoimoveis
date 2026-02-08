#!/usr/bin/env python3
"""
Quick status reporter for 1000 properties workflow
Run this anytime to get a detailed progress report
"""

import json
from pathlib import Path
from datetime import datetime


def get_status():
    """Get comprehensive status of the workflow"""
    base_dir = Path(".tmp/batch_1000_imoveis")

    if not base_dir.exists():
        return {"error": "No data directory found"}

    # Count processed properties
    data_files = list(base_dir.glob("property_*/data.json"))
    count = len(data_files)

    # Count images
    image_count = sum(1 for _ in base_dir.glob("property_*/images/*.jpg"))

    # Get data size
    total_size = sum(f.stat().st_size for f in base_dir.rglob("*") if f.is_file())

    # Read sample data for quality check
    sample_data = {}
    if data_files:
        with open(data_files[0], "r") as f:
            sample_data = json.load(f)

    # Check log
    log_file = Path(".tmp/auto_complete.log")
    last_log = ""
    if log_file.exists():
        with open(log_file, "r") as f:
            lines = f.readlines()
            if lines:
                last_log = lines[-1].strip()

    # Calculate ETA
    if count > 0:
        # Estimate based on ~3.5 properties per minute
        remaining = 1000 - count
        minutes_remaining = remaining / 3.5
        hours = int(minutes_remaining // 60)
        minutes = int(minutes_remaining % 60)
        eta = f"{hours}h {minutes}m"
        percent = count / 10
    else:
        eta = "Unknown"
        percent = 0

    return {
        "properties_processed": count,
        "total_target": 1000,
        "percent_complete": percent,
        "images_downloaded": image_count,
        "data_size_mb": total_size / (1024 * 1024),
        "eta": eta,
        "last_log": last_log,
        "sample_price": sample_data.get("prices", {}).get("price_formatted", "N/A"),
        "sample_neighborhood": sample_data.get("location", {}).get(
            "neighborhood", "N/A"
        ),
    }


def print_report(status):
    """Print formatted status report"""
    print("=" * 70)
    print("🏠 INFOIMÓVEIS 1000 PROPERTIES - STATUS REPORT")
    print("=" * 70)
    print()

    if "error" in status:
        print(f"❌ Error: {status['error']}")
        return

    # Progress bar
    percent = status["percent_complete"]
    bar_width = 50
    filled = int(percent * bar_width / 100)
    empty = bar_width - filled
    bar = "█" * filled + "░" * empty

    print(f"📊 Progress: {status['properties_processed']}/1000 ({percent:.1f}%)")
    print(f"   [{bar}]")
    print()

    print(f"⏱️  Estimated Time Remaining: {status['eta']}")
    print()

    print(f"📁 Data Statistics:")
    print(f"   • Images downloaded: {status['images_downloaded']}")
    print(f"   • Total data size: {status['data_size_mb']:.1f} MB")
    print()

    print(f"✅ Sample Data Quality Check:")
    print(f"   • Price extraction: {status['sample_price']}")
    print(f"   • Neighborhood: {status['sample_neighborhood']}")
    print()

    print(f"📝 Last Activity:")
    print(f"   {status['last_log']}")
    print()

    print("=" * 70)
    print("Next Steps (Auto-Triggered):")
    print("   1. AI Analysis (Mistral) - Starts at 1000 properties")
    print("   2. Excel Generation - After AI completes")
    print("   3. GitHub Commit - After Excel ready")
    print("=" * 70)


if __name__ == "__main__":
    status = get_status()
    print_report(status)
