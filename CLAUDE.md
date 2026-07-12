# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is a university course "云原生 AI 基础设施：原理与实践" (Cloud-Native AI Infrastructure: Principles and Practice) — 8 modules, 90 min each, from Linux containers to inference serving platforms. Everything is in Chinese.

## Repo structure

```
module-name/
├── README.md              # Module overview with links to visuals
├── syllabus.md            # 90-min time allocation
├── ppt-outline.md         # Slide-by-slide PPT outline (45 slides/module)
├── hands-on-exercise.md   # In-class exercises with solutions
├── homework.md            # After-class assignments
├── lab-environment.md     # Server/software setup instructions
├── code/                  # Runnable code (CUDA, Python, Shell, YAML)
└── visuals/               # Interactive SVG HTMLs for PPT projection
```

8 modules: `01-linux-containers/` → `02-gpu-cuda/` → `02b-gpu-memory/` → `03-gpu-virtualization/` → `04-kubernetes-gpu/` → `05-vllm-inference/` → `06-kvcache-optimization/` → `07-maas-infra/` → `08-summary-outlook/`.

Root-level `course-overview.html` is the interactive landing page with 7-layer request-path stack and clickable module cards. Links in `README.md` reference internal paths and GitHub URLs under `ForceInjection/`.

## Design conventions

### HTML visuals

All visuals are standalone HTML files with embedded SVG, designed for projection at 16:9. Consistent styling:

- Background: `#1A0F2E` (deep purple body), `#231440` (surface panels)
- Border: `#432879` (subtle), `#E97132` (highlight)
- Accent colors: blue `#156082` / `#0F9ED5`, orange `#E97132`, purple `#A02B93`, green `#196B24` / `#4ade80`, lime `#4EA72E`, yellow `#fbbf24`
- Text: `#F8F6FB` (primary), `#C8BEE0` (body), `#8A7BB5` (muted)
- Font: `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`; monospace: `monospace`
- Root `<svg viewBox="0 0 1100 H">` with rounded-rect border, header in `<div class="header">` outside SVG
- Page is full-viewport (`height:100vh; overflow:hidden`) with flexbox centering for PPT projection

### Visualization patterns by module

- **Sequence diagrams** (module 4): UML lifelines at evenly-spaced x-positions, helper functions `lbl(a,b,y,text,...)` and `mid(a,b)` for arrow midpoints
- **Bit-level layouts** (module 6): colored bar rects for S (yellow), E (blue), M (green) bit groups
- **3D/stacked** (module 2b, 6): layered polygons with decreasing opacity for depth; offset by 5px per layer
- **Interactive** (module 1, 3): CSS `:target` or simple click handlers for step-by-step reveal

### Code conventions

- Python scripts: zero-dependency where possible (`calculate_qwen3_memory.py`, `03_token_bucket.py`). Use `argparse` for CLI. Have a module docstring explaining what it does and how to run it.
- CUDA kernels (`.cu`): compile with `nvcc -o prog prog.cu`. Include thinking questions as comments at end of file.
- Shell scripts: numbered (`01_*.sh`, `02_*.sh`), each designed to run independently. Heavy inline comments explaining each command.
- YAML (K8s manifests): always include `namespace: gpu-demo`. Use `nvidia.com/gpu: 1` resource requests.

### PPT theme

Slide decks use the same deep-purple color scheme as HTML visuals. All `ppt-outline.md` files follow the format: slide number, title, content bullet points, and notes on when to open which visual.

## Environment

- Linux servers: seetacloud (RTX 3090 + 4090D, `/home/student/` user accounts) and aliyun ECS (CPU-only, K3s control-plane)
- Software stack: CUDA 12.4, PyTorch 2.6.0+cu124, flash-attn 2.7.4.post1, nano-vllm, K3s, Docker
- **Critical compatibility**: flash-attn ≥ 2.8.x requires CUDA 12.6+ (new C++ ABI). For PyTorch 2.6.0+cu124, use flash-attn 2.7.4.post1.
- Models: Qwen3-0.6B from ModelScope (not HuggingFace — blocked in China). Mirror: `pip install -i https://mirrors.aliyun.com/pypi/simple/`

## Key disclaimers embedded in course materials

- KV Cache formula `2 × L × H_kv × D × T × B` applies to MHA/GQA/MQA only. MLA (DeepSeek V2/V3) is different.
- MoE model KV Cache is **not** affected by expert count.
- `nvidia-smi` shows compute-mode MIG configs but actual partition status requires `nvidia-mig-manager`.
- docker.io is blocked in mainland China; use daocloud or ACR mirrors.
- K3s in AutoDL/containers may lack CAP_SYS_ADMIN — Docker-in-Docker won't work there.
