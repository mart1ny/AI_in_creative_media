from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata as md
import json
import os
import platform
import time

import torch
from diffusers import AutoPipelineForText2Image


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "run_config.json"
OUT = ROOT / "artifacts" / "run_001"
REPORTS = ROOT / "reports"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    prompt = config["prompt"]
    if not prompt or prompt.startswith("PLACEHOLDER"):
        raise SystemExit(
            "Сначала зафиксируйте prompt варианта 2 в configs/run_config.json."
        )

    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    model_id = config["model_id"]
    revision = config["revision"]
    seed = int(config["seed"])
    steps = int(config["num_inference_steps"])
    guidance = float(config["guidance_scale"])
    size = int(config["height"])

    torch.set_num_threads(1)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    load_args = dict(revision=revision, use_safetensors=True, torch_dtype=dtype)
    if device == "cuda":
        load_args["variant"] = "fp16"
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    started = time.perf_counter()
    pipe = AutoPipelineForText2Image.from_pretrained(model_id, **load_args)
    pipe = pipe.to(device)
    # CPU generator is required by the lab even on CUDA: it keeps the seed
    # path comparable across machines that do not share a GPU.
    generator = torch.Generator(device="cpu").manual_seed(seed)
    image = pipe(
        prompt=prompt,
        num_inference_steps=steps,
        guidance_scale=guidance,
        height=size,
        width=size,
        generator=generator,
    ).images[0]
    elapsed = time.perf_counter() - started

    image_path = OUT / "result.png"
    image.save(image_path)
    packages = {
        name: md.version(name)
        for name in ["torch", "diffusers", "transformers", "accelerate", "safetensors"]
    }
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "student": config.get("student"),
        "group": config.get("group"),
        "variant": config.get("variant"),
        "model_id": model_id,
        "revision": revision,
        "prompt": prompt,
        "seed": seed,
        "steps": steps,
        "guidance_scale": guidance,
        "height": size,
        "width": size,
        "device": device,
        "dtype": str(dtype),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "packages": packages,
        "elapsed_seconds_measured": elapsed,
        "artifact": str(image_path.relative_to(ROOT)),
        "sha256": sha256(image_path),
        "hf_home": os.environ.get("HF_HOME"),
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (REPORTS / "run_001.log").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
