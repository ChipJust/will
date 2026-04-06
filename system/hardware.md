# Current Machine Specification

*Captured: 2026-04-06*

## Summary

This is a high-end desktop workstation (HEDT) with a lot of remaining life.
Primary limitation today: GPU is weak for AI workloads. Everything else is strong.

---

## Hardware

| Component | Spec |
|-----------|------|
| **CPU** | Intel Core i9-9960X @ 3.10GHz (Skylake-X) |
| **Cores** | 16 cores / 32 logical processors |
| **Cache** | L2: 16MB, L3: 22.5MB |
| **RAM** | 128GB DDR4-2133 (8× 16GB DIMMs) |
| **Motherboard** | ASRock X299 Steel Legend |
| **Platform** | LGA 2066, X299 chipset |
| **PCIe** | PCIe 3.0, 44 lanes from CPU + 24 from chipset |
| **GPU** | NVIDIA GeForce GTX 1650 (4GB VRAM) ← weak link |
| **Storage 1** | 240GB Intel SATA SSD (SSDSC2BW240A4) |
| **Storage 2** | 512GB Intel NVMe SSD (SSDPEKKW512G8) × 2 |
| **Storage 3** | 3TB HGST HDD (HDN724030ALE640) |
| **OS** | Windows 10 Pro 22H2 (build 19045) |
| **BIOS** | AMI P1.10 (2019-10-23) |

---

## Why This Machine Has Life Left

- **128GB RAM** — exceptional for AI inference; most consumer machines cap at 32-64GB.
  Running a 70B quantized model (GGUF Q4) requires ~40GB RAM; this machine can do it.
- **16c/32t CPU** — still competitive for parallel workloads, compilation, data processing.
- **PCIe lane count** — X299 has more PCIe lanes than consumer Z-series boards.
  Can host a GPU + AI accelerator + NVMe without lane contention.
- **Upgradable chassis** — X299 Steel Legend has multiple PCIe x16 slots (physically x16,
  x8 electrically depending on slot) for adding dedicated AI hardware.

---

## AI Hardware Upgrade Options

### Option A: Tenstorrent Grayskull (recommended to evaluate)
- **Grayskull e75** — PCIe x16, 75W (no external power needed), lower cost entry point
- **Grayskull e150** — PCIe x16, 150W (8-pin power), more Tensix cores
- Form factor: standard PCIe card, fits any x16 slot
- PCIe 3.0 compatibility: Grayskull is Gen4 but backward-compatible; runs at Gen3 speeds
  (~16 GB/s vs 32 GB/s). For LLM inference, this is acceptable — bandwidth is not always
  the bottleneck; compute is.
- Software: TT-Metalium (low-level), TT-Buda (model framework)
- Models: LLaMA, Falcon, Mistral families supported
- **Research goal:** Benchmark cost-per-token vs. Claude API to find crossover point
  where local inference becomes cheaper at Chip's actual usage volume

### Option B: NVIDIA RTX (upgrade from GTX 1650)
- RTX 3090 (24GB VRAM) or RTX 4090 (24GB VRAM) — mainstream LLM inference
- Better ecosystem (CUDA, llama.cpp, Ollama all support it natively)
- Higher cost than Tenstorrent; less interesting from a research perspective

### Option C: AMD Radeon RX 7900 XTX (24GB VRAM)
- ROCm support improving; runs llama.cpp well on Linux
- Lower cost than RTX 4090; good Linux driver support

### Recommended path: Grayskull e75 first
- Low cost, unique architecture worth understanding
- Studying cost/performance builds understanding of the AI hardware landscape
- If disappointing, the PCIe slot is still open for an RTX upgrade afterward

---

## Linux Migration Assessment

### Why migrate
- Better driver support for AI hardware (Tenstorrent SDK, ROCm, CUDA in WSL is limited)
- Docker runs natively — important for model serving and reproducible environments
- No artificial hardware support restrictions (Windows hardware compatibility policy)
- Better performance for Python-heavy workloads (no cp1252 encoding gotchas)
- LTS Ubuntu or Fedora Workstation are both excellent on X299

### Linux compatibility
| Component | Status |
|-----------|--------|
| i9-9960X | Full support, excellent |
| X299 Steel Legend | Good support; check BIOS for CSM settings |
| GTX 1650 | Full NVIDIA driver support |
| Intel NVMe SSDs | Full support |
| HGST HDD | Full support |
| Grayskull (future) | Linux-first SDK; better on Linux than Windows |

### Recommended distro: Ubuntu 24.04 LTS
- Long-term support through 2029
- Best driver package availability
- Largest community for troubleshooting AI stack issues

### Migration approach
1. Install Ubuntu alongside Windows (dual boot on the 240GB SATA SSD)
2. Run Linux for one month alongside Windows during transition
3. Once all repos and tools verified working, retire Windows partition

---

## Android Integration (Pixel 7)

**Device:** Google Pixel 7 (Android 14+)

### Integration options

| Tool | Purpose | Priority |
|------|---------|----------|
| **ADB** (Android Debug Bridge) | Device management, file transfer, sideloading | High |
| **KDE Connect** | Phone ↔ desktop sync: clipboard, notifications, files | High |
| **Syncthing** | Folder sync between phone and workstation | Medium |
| **Claude.ai mobile** | AI assistance on the go; same context as Claude Code | Active now |
| **Termux** | Linux environment on Android; can run Python, git | Medium |
| **VNC/RDP** | Full desktop remote access from phone | Low |

### Bootstrap includes
- `adb` installed via platform-tools
- KDE Connect configured (works on Linux; Windows version is less stable)

---

## Storage Organization

| Drive | Size | Current Use | Recommended Use |
|-------|------|-------------|-----------------|
| Intel SATA SSD | 240GB | Windows OS | Linux boot + OS on migration |
| Intel NVMe #1 | 512GB | D:\_code\ workspace | Primary workspace (keep) |
| Intel NVMe #2 | 512GB | Unknown | AI models, Docker images |
| HGST HDD | 3TB | Unknown | Media, backups, large datasets |
