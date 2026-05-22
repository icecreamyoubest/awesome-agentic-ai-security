#!/usr/bin/env python3
"""Run monitor -> triage -> roadmap update pipeline."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(cmd):
    print('+',' '.join(cmd)); subprocess.check_call(cmd,cwd=ROOT)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--network',action='store_true'); ap.add_argument('--offline',action='store_true'); ap.add_argument('--max-per-source',type=int,default=5); ap.add_argument('--update-seen',action='store_true'); args=ap.parse_args()
    mode='--network' if args.network else '--offline'
    monitor=[sys.executable,'agents/update_monitor.py',mode,'--max-per-source',str(args.max_per_source)]
    if args.update_seen: monitor.append('--update-seen')
    run(monitor)
    run([sys.executable,'agents/update_triage_agent.py'])
    run([sys.executable,'agents/roadmap_update_agent.py'])
    try: run([sys.executable,'agents/build_source_index.py','--output','data/source_index.json'])
    except Exception as e: print('source index rebuild skipped:',e)
    try: run([sys.executable,'scripts/validate_catalog.py'])
    except Exception as e: print('catalog validation warning:',e)
