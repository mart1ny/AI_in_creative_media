"""Intentional lab error: CUDA generator on a CPU-only process.

The methodical notes ask to replace
    torch.Generator(device="cpu").manual_seed(SEED)
with
    torch.Generator(device="cuda").manual_seed(SEED)
and observe the failure on a machine without a usable CUDA generator device.
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SEED = 20260920


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    record = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "torch.cuda.is_available": torch.cuda.is_available(),
        "selected_device": device,
        "broken_line": 'torch.Generator(device="cuda").manual_seed(SEED)',
        "symptom": None,
        "status": None,
    }

    try:
        torch.Generator(device="cuda").manual_seed(SEED)
        record["status"] = "NO_EXCEPTION"
        record["symptom"] = (
            "Генератор CUDA создался. На этой машине ошибка методички "
            "не воспроизводится, потому что CUDA доступна. Для симптома "
            "нужен CPU-only процесс либо принудительно недоступный cuda."
        )
        print(json.dumps(record, ensure_ascii=False, indent=2))
        (REPORTS / "cuda_generator_error.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return
    except Exception as exc:  # noqa: BLE001 — we want the exact lab symptom
        record["status"] = "EXCEPTION_AS_EXPECTED"
        record["symptom"] = f"{type(exc).__name__}: {exc}"

    record["fix"] = 'torch.Generator(device="cpu").manual_seed(SEED)'
    record["why_cpu_generator"] = (
        "Diffusers принимает CPU Generator даже при инференсе на GPU. "
        "Так seed задаётся одинаковым способом на CPU-ноутбуке и на Colab GPU."
    )
    (REPORTS / "cuda_generator_error.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
