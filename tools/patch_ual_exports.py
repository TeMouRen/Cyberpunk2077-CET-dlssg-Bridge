#!/usr/bin/env python3
"""Add DLSSG NGX forwarder exports to an Ultimate ASI Loader version.dll.

This script only writes the explicitly supplied output path.  It is intended
for an isolated staging directory first; it never modifies the input file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import lief


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outer", type=Path, required=True)
    parser.add_argument("--inner", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    outer = lief.PE.parse(str(args.outer))
    inner = lief.PE.parse(str(args.inner))
    if outer is None or inner is None:
        raise SystemExit("could not parse PE input")
    outer_export = outer.get_export()
    inner_export = inner.get_export()
    if outer_export is None or inner_export is None:
        raise SystemExit("missing export directory")

    amd64 = lief.PE.Header.MACHINE_TYPES.AMD64
    if outer.header.machine != amd64 or inner.header.machine != amd64:
        raise SystemExit("both inputs must be AMD64 PE files")

    existing = {entry.name for entry in outer_export.entries if entry.name}
    required_outer = {"GetFileVersionInfoA", "ResolveAddress"}
    missing_outer = sorted(required_outer - existing)
    if missing_outer:
        raise SystemExit(f"outer DLL is missing required exports: {missing_outer}")

    inner_names = {entry.name for entry in inner_export.entries if entry.name}
    required_inner = {
        "NVSDK_NGX_GetAPIVersion",
        "NVSDK_NGX_D3D12_Init",
        "NVSDK_NGX_D3D12_CreateFeature",
        "NVSDK_NGX_D3D12_EvaluateFeature",
    }
    missing_inner = sorted(required_inner - inner_names)
    if missing_inner:
        raise SystemExit(f"inner DLL is missing required exports: {missing_inner}")

    existing_ngx = sorted(name for name in existing if name.startswith("NVSDK_NGX_"))
    if existing_ngx:
        raise SystemExit("outer DLL already contains NVSDK_NGX exports; manual review required")

    added = []
    for entry in inner_export.entries:
        name = entry.name
        if not name or not name.startswith("NVSDK_NGX_"):
            continue
        if name in existing:
            continue
        new_entry = outer_export.add_entry(name, 0)
        # PE forwarders use DLL.export syntax.  Keep the inner filename
        # explicit so Windows resolves the intended side-by-side module.
        new_entry.set_forward_info(args.inner.name, name)
        added.append(name)

    if not added:
        raise SystemExit("no new NVSDK_NGX exports were added")

    config = lief.PE.Builder.config_t()
    config.exports = True
    builder = lief.PE.Builder(outer, config)
    builder.build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    builder.write(str(args.output))
    print(f"added {len(added)} forwarders to {args.output}")
    for name in added:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
