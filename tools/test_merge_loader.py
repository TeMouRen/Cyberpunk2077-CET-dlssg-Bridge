#!/usr/bin/env python3
"""Smoke-test a staged merged version.dll without touching a game install."""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

import pefile


NAMES = [
    "GetFileVersionInfoA",
    "ResolveAddress",
    "NVSDK_NGX_GetAPIVersion",
    "NVSDK_NGX_D3D12_Init",
    "NVSDK_NGX_D3D12_CreateFeature",
    "NVSDK_NGX_D3D12_EvaluateFeature",
]


def main() -> int:
    stage = Path(sys.argv[1]).resolve()
    os.chdir(stage)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.SetDllDirectoryW(str(stage))
    kernel32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_uint32]
    kernel32.LoadLibraryExW.restype = ctypes.c_void_p
    kernel32.GetProcAddress.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    kernel32.GetProcAddress.restype = ctypes.c_void_p
    kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    kernel32.GetModuleHandleW.restype = ctypes.c_void_p

    handle = kernel32.LoadLibraryExW(str(stage / "version.dll"), None, 0x00000008)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    print(f"outer=0x{handle:x}")
    inner = kernel32.GetModuleHandleW("versionHooked.dll")
    print(f"inner=0x{inner:x}")
    failed = []
    for name in NAMES:
        addr = kernel32.GetProcAddress(handle, name.encode("ascii"))
        print(f"{name}={addr!r}")
        if not addr:
            failed.append(name)

    inner_exports = []
    inner_pe = pefile.PE(str(stage / "versionHooked.dll"))
    for symbol in inner_pe.DIRECTORY_ENTRY_EXPORT.symbols:
        if symbol.name and symbol.name.startswith(b"NVSDK_NGX_"):
            inner_exports.append(symbol.name.decode("ascii"))
    for name in inner_exports:
        if not kernel32.GetProcAddress(handle, name.encode("ascii")):
            failed.append(name)
    print(f"all_ngx_exports_resolved={len(inner_exports) - sum(1 for n in inner_exports if n in failed)}/{len(inner_exports)}")

    # The inner DLL should also redirect the game's normal attempt to load
    # nvngx_dlssg.dll back to itself.  The staged file is only a harmless
    # stand-in to prove that the requested name is intercepted.
    redirect_target = stage / "nvngx_dlssg.dll"
    redirected = kernel32.LoadLibraryExW(str(redirect_target), None, 0)
    print(f"redirected=0x{redirected:x}" if redirected else "redirected=None")
    print(f"redirect_matches_inner={redirected == inner}")
    if redirected != inner:
        failed.append("LoadLibraryExW(nvngx_dlssg.dll) redirect")

    api = kernel32.GetProcAddress(handle, b"NVSDK_NGX_GetAPIVersion")
    if api:
        fn = ctypes.CFUNCTYPE(ctypes.c_uint32)(api)
        try:
            print(f"NVSDK_NGX_GetAPIVersion()={fn()}")
        except Exception as exc:  # pragma: no cover - platform-dependent
            print(f"call-error={exc!r}")

    return 1 if failed or not inner else 0


if __name__ == "__main__":
    raise SystemExit(main())
