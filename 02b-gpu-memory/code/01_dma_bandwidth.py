#!/usr/bin/env python3
"""
模块2 高级：GPU 内存管理 — CPU↔GPU 带宽测试
课程配套实验脚本。使用 ctypes 直接调用 CUDA Runtime API，
测量 pageable (malloc) vs pinned (cudaMallocHost) 的 DMA 传输带宽。

原理：
  - Pageable: 内核每次 cudaMemcpy 需遍历页表 + 页锁定 → 构建 scatter-gather list
  - Pinned (cudaMallocHost): 页面预先锁定，DMA 引擎直传物理地址 → 跳过 CPU 开销

预期 (PCIe Gen4 x16):
  Pageable H2D: ~22 GB/s | Pinned H2D: ~26 GB/s | Ratio: ~1.2×

预期 (PCIe Gen5 x16, H100 实测):
  Pageable H2D: ~21 GB/s | Pinned H2D: ~55 GB/s | Ratio: ~2.7×
  (pageable 瓶颈在 CPU，不随 PCIe 代际升级)

用法: python3 01_dma_bandwidth.py [--sizes 0.5 1 2 4]
"""

import argparse, ctypes, os, subprocess, sys, time

# ── find libcudart ──
def _find_cudart():
    paths = [
        "/usr/local/cuda/lib64/libcudart.so",
        "/usr/local/cuda-12/lib64/libcudart.so",
        "/usr/local/cuda-12.8/lib64/libcudart.so",
        "/usr/local/cuda-12/targets/x86_64-linux/lib/libcudart.so",
        "/usr/local/cuda-12.8/targets/x86_64-linux/lib/libcudart.so",
        "/usr/lib/x86_64-linux-gnu/libcudart.so",
        "/usr/lib64/libcudart.so",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    try:
        out = subprocess.check_output(["ldconfig", "-p"], text=True)
        for line in out.splitlines():
            if "libcudart.so" in line and "(" not in line:
                return line.strip().split()[-1]
    except Exception:
        pass
    # glob fallback
    import glob
    for pattern in ["/usr/local/cuda*/lib64/libcudart.so*", "/usr/local/cuda*/targets/*/lib/libcudart.so*"]:
        hits = sorted(glob.glob(pattern))
        for h in hits:
            if ".so." not in os.path.basename(h) or h.endswith(".so"):
                return h
        if hits:
            return hits[0]
    # Last resort: try direct CDLL load (respects LD_LIBRARY_PATH via ld.so)
    try:
        ctypes.CDLL("libcudart.so")
        return "libcudart.so"
    except OSError:
        pass
    raise RuntimeError("Cannot find libcudart.so. Try: LD_LIBRARY_PATH=/path/to/cuda/lib64 python3 ...")

# ── libc (for pageable malloc/free) ──
LIBC = ctypes.CDLL("libc.so.6")
LIBC.malloc.argtypes = [ctypes.c_size_t]
LIBC.malloc.restype = ctypes.c_void_p
LIBC.free.argtypes = [ctypes.c_void_p]
LIBC.free.restype = None

CUDA = ctypes.CDLL(_find_cudart())

# ── type aliases ──
cudaError_t = ctypes.c_int
cudaSuccess = 0

# cudaMemcpyKind
cudaMemcpyHostToDevice = 1
cudaMemcpyDeviceToHost = 2

CUDA.cudaMalloc.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_size_t]
CUDA.cudaMalloc.restype = cudaError_t

CUDA.cudaFree.argtypes = [ctypes.c_void_p]
CUDA.cudaFree.restype = cudaError_t

CUDA.cudaMallocHost.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_size_t]
CUDA.cudaMallocHost.restype = cudaError_t

CUDA.cudaFreeHost.argtypes = [ctypes.c_void_p]
CUDA.cudaFreeHost.restype = cudaError_t

CUDA.cudaMemcpy.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
CUDA.cudaMemcpy.restype = cudaError_t

CUDA.cudaEventCreate.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
CUDA.cudaEventCreate.restype = cudaError_t

CUDA.cudaEventDestroy.argtypes = [ctypes.c_void_p]
CUDA.cudaEventDestroy.restype = cudaError_t

CUDA.cudaEventRecord.argtypes = [ctypes.c_void_p, ctypes.c_void_p]  # event, stream(0=default)
CUDA.cudaEventRecord.restype = cudaError_t

CUDA.cudaEventSynchronize.argtypes = [ctypes.c_void_p]
CUDA.cudaEventSynchronize.restype = cudaError_t

CUDA.cudaEventElapsedTime.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_void_p, ctypes.c_void_p]
CUDA.cudaEventElapsedTime.restype = cudaError_t

CUDA.cudaDeviceSynchronize.argtypes = []
CUDA.cudaDeviceSynchronize.restype = cudaError_t


def check(err, msg=""):
    if err != cudaSuccess:
        raise RuntimeError(f"CUDA error {err}: {msg}")


def test_one(size_bytes, pinned, direction, warmup, iters):
    """Run a single bandwidth test. Returns (bandwidth_gbps, elapsed_ms)."""
    # Allocate host memory
    host_ptr = ctypes.c_void_p()
    if pinned:
        check(CUDA.cudaMallocHost(ctypes.byref(host_ptr), size_bytes),
              f"cudaMallocHost({size_bytes/1e9:.1f}GB)")
    else:
        # Use regular malloc via ctypes (pageable)
        host_ptr = ctypes.c_void_p(LIBC.malloc(size_bytes))
        if not host_ptr.value:
            raise MemoryError(f"malloc({size_bytes/1e9:.1f}GB) failed")

    # Allocate device memory
    dev_ptr = ctypes.c_void_p()
    check(CUDA.cudaMalloc(ctypes.byref(dev_ptr), size_bytes),
          f"cudaMalloc({size_bytes/1e9:.1f}GB)")

    # For D2H, we need a pinned destination or pageable destination
    dst_host_ptr = ctypes.c_void_p()
    if direction == "D2H":
        if pinned:
            check(CUDA.cudaMallocHost(ctypes.byref(dst_host_ptr), size_bytes),
                  f"cudaMallocHost({size_bytes/1e9:.1f}GB) for D2H dst")
        else:
            dst_host_ptr = ctypes.c_void_p(LIBC.malloc(size_bytes))
            if not dst_host_ptr.value:
                raise MemoryError(f"malloc({size_bytes/1e9:.1f}GB) for D2H dst failed")

    # Create CUDA events
    start_ev = ctypes.c_void_p()
    end_ev = ctypes.c_void_p()
    check(CUDA.cudaEventCreate(ctypes.byref(start_ev)))
    check(CUDA.cudaEventCreate(ctypes.byref(end_ev)))

    src = host_ptr if direction == "H2D" else dev_ptr
    dst = dev_ptr if direction == "H2D" else dst_host_ptr

    # Warmup
    for _ in range(warmup):
        check(CUDA.cudaMemcpy(dst, src, size_bytes,
              cudaMemcpyHostToDevice if direction == "H2D" else cudaMemcpyDeviceToHost))
    CUDA.cudaDeviceSynchronize()

    # Measurement
    check(CUDA.cudaEventRecord(start_ev, None))
    for _ in range(iters):
        check(CUDA.cudaMemcpy(dst, src, size_bytes,
              cudaMemcpyHostToDevice if direction == "H2D" else cudaMemcpyDeviceToHost))
    check(CUDA.cudaEventRecord(end_ev, None))
    check(CUDA.cudaEventSynchronize(end_ev))

    elapsed = ctypes.c_float()
    check(CUDA.cudaEventElapsedTime(ctypes.byref(elapsed), start_ev, end_ev))

    # Cleanup
    CUDA.cudaEventDestroy(start_ev)
    CUDA.cudaEventDestroy(end_ev)
    CUDA.cudaFree(dev_ptr)
    if pinned:
        CUDA.cudaFreeHost(host_ptr)
        if direction == "D2H":
            CUDA.cudaFreeHost(dst_host_ptr)
    else:
        LIBC.free(host_ptr)
        if direction == "D2H":
            LIBC.free(dst_host_ptr)

    total_bytes = size_bytes * iters
    bw = total_bytes / (elapsed.value / 1000.0) / 1e9
    return bw, elapsed.value


def pcie_info():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=pcie.link.gen.current,pcie.link.width.current,name",
             "--format=csv,noheader"], text=True
        ).strip().splitlines()[0]
        parts = out.split(", ")
        return int(parts[0]), int(parts[1]), parts[2]
    except Exception:
        return None, None, "unknown"


def main():
    parser = argparse.ArgumentParser(description="CPU↔GPU DMA bandwidth benchmark (ctypes CUDA RT)")
    parser.add_argument("--sizes", type=float, nargs="+", default=[0.5, 1, 2],
                        help="Buffer sizes in GB (default: 0.5 1 2)")
    parser.add_argument("--iters", type=int, default=10, help="Measured iterations (default: 10)")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup iterations (default: 3)")
    args = parser.parse_args()

    gen, width, gpu_name = pcie_info()
    gen_str = f"PCIe Gen{gen} x{width}" if gen else "PCIe (unknown)"

    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    print(f"{CYAN}{'='*62}{RESET}")
    print(f"{BOLD}CPU↔GPU DMA Bandwidth Test (ctypes + libcudart){RESET}")
    print(f"GPU:  {gpu_name}")
    print(f"Link: {gen_str}")
    print(f"{CYAN}{'='*62}{RESET}")
    print()

    results = []

    for size_gb in args.sizes:
        size_bytes = int(size_gb * 1024**3)

        for direction in ("H2D", "D2H"):
            try:
                pg_bw, pg_ms = test_one(size_bytes, False, direction, args.warmup, args.iters)
                pin_bw, pin_ms = test_one(size_bytes, True, direction, args.warmup, args.iters)
                ratio = pin_bw / pg_bw
                results.append((size_gb, direction, pg_bw, pin_bw, ratio, pg_ms, pin_ms))
            except Exception as e:
                print(f"{YELLOW}{size_gb:.1f}GB {direction}: ERROR — {e}{RESET}")

    if not results:
        print("No results collected.")
        return

    # Table
    print(f"{'Size':>5s}  {'Dir':>4s}  {'Pageable':>10s}  {'Pinned':>10s}  {'Ratio':>8s}  "
          f"{'Pin-page':>10s}")
    print("-" * 66)
    for size_gb, direction, pg_bw, pin_bw, ratio, pg_ms, pin_ms in results:
        delta = pin_bw - pg_bw
        print(f"{size_gb:4.1f}GB {direction:>4s}  {pg_bw:8.2f} GB/s  "
              f"{pin_bw:8.2f} GB/s  {ratio:7.1f}x  +{delta:7.1f} GB/s")

    print()

    # Summary
    h2d = [(pg, pin, r) for sz, d, pg, pin, r, _, _ in results if d == "H2D"]
    d2h = [(pg, pin, r) for sz, d, pg, pin, r, _, _ in results if d == "D2H"]

    if h2d:
        avg_ratio = sum(r for _, _, r in h2d) / len(h2d)
        avg_pg_h2d = sum(pg for pg, _, _ in h2d) / len(h2d)
        avg_pin_h2d = sum(pin for _, pin, _ in h2d) / len(h2d)

        print(f"{CYAN}--- Summary (H2D) ---{RESET}")
        print(f"Pageable:  {avg_pg_h2d:.1f} GB/s")
        print(f"Pinned:    {avg_pin_h2d:.1f} GB/s")
        print(f"Ratio:     {avg_ratio:.1f}x")

        if gen and width:
            theoretical = {3: 16, 4: 32, 5: 64}.get(gen, 32)
            pin_eff = avg_pin_h2d / theoretical * 100
            pg_eff = avg_pg_h2d / theoretical * 100
            print()
            print(f"Theoretical ({gen_str}): ~{theoretical} GB/s")
            print(f"Pinned efficiency:   {pin_eff:.0f}% (expected 70-85%)")
            print(f"Pageable efficiency: {pg_eff:.0f}% (expected 35-45%, page-walk bound)")

        print()
        print(f"Pageable H2D ({avg_pg_h2d:.0f} GB/s): 瓶颈在 CPU 页表遍历，不随 PCIe 升级")
        print(f"Pinned H2D   ({avg_pin_h2d:.0f} GB/s): DMA 引擎直传，接近 PCIe 理论带宽")

    if d2h:
        avg_ratio_d2h = sum(r for _, _, r in d2h) / len(d2h)
        avg_pg_d2h = sum(pg for pg, _, _ in d2h) / len(d2h)
        avg_pin_d2h = sum(pin for _, pin, _ in d2h) / len(d2h)
        print()
        print(f"{CYAN}--- Summary (D2H) ---{RESET}")
        print(f"Pageable:  {avg_pg_d2h:.1f} GB/s")
        print(f"Pinned:    {avg_pin_d2h:.1f} GB/s")
        ratio_color = GREEN if 1.7 <= avg_ratio_d2h <= 2.5 else YELLOW
        print(f"Ratio:     {ratio_color}{avg_ratio_d2h:.1f}x{RESET}")

    print()
    print(f"{CYAN}--- 思考题 ---{RESET}")
    print("1. 为什么 Pinned 比 Pageable 快?")
    print("   -> Pageable 每次 cudaMemcpy 都要遍历页表、逐页锁定")
    print("   -> Pinned (cudaMallocHost) 预先锁定，DMA 引擎直传物理地址")
    print()
    print("2. Pinned 内存的代价是什么?")
    print("   -> 占用物理页面，不能 swap；分配过多会导致系统内存不足")
    print()
    print("3. 这和 vLLM 的 KV Cache 有什么关系?")
    print("   -> KV Cache 在 GPU HBM 中，不需要 H2D/D2H（已在 Device 端）")
    print("   -> 但模型权重首次加载时，pinned memory 可加速 CPU->GPU 传输")


if __name__ == "__main__":
    main()
