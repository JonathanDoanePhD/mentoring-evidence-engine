"""Show pipeline progress and list pending batches (what a resume should run next).

python3 -I scripts/status.py            # human-readable summary
python3 -I scripts/status.py --json     # {"screen_pending": [...], "code_pending": {...}, ...}
A batch is done when its output file exists AND validates.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "data" / "interim" / "batches"
C = ROOT / "data" / "coded"


def valid(kind, out):
    if not out.exists():
        return False
    r = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "validate.py"), kind, str(out)],
                       capture_output=True, text=True)
    return r.returncode == 0


def pending(kind, batch_sub, out_dir):
    batches = sorted((B / batch_sub).glob("batch_*.jsonl")) if (B / batch_sub).exists() else []
    return [b.stem for b in batches if not valid(kind, out_dir / f"{b.stem}.json")], len(batches)


status = {}
status["screen_pending"], status["screen_total"] = pending("screen", "screen", C / "screen")
for coder in ("coder_a", "coder_b"):
    status[f"code_{coder}_pending"], status["code_total"] = pending("code", "code", C / "code" / coder)
status["adjudicate_pending"], status["adjudicate_total"] = pending("adjudicate", "adjudicate", C / "adjudicate")

if "--json" in sys.argv:
    print(json.dumps(status))
else:
    print(f"Screening:   {status['screen_total'] - len(status['screen_pending'])}/{status['screen_total']} batches done")
    for coder in ("coder_a", "coder_b"):
        print(f"Coding {coder}: {status['code_total'] - len(status[f'code_{coder}_pending'])}/{status['code_total']} batches done")
    print(f"Adjudication: {status['adjudicate_total'] - len(status['adjudicate_pending'])}/{status['adjudicate_total']} batches done")
    if status["screen_pending"]:
        print("Next screening batches:", ", ".join(status["screen_pending"][:10]), "..." if len(status["screen_pending"]) > 10 else "")
