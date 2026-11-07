#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 The LineageOS Project
"""Compile Waipio/Cape DTs and apply every matching Xiaomi board overlay."""
from pathlib import Path
import argparse
import concurrent.futures
import subprocess
import json
import struct
import sys

dt = Path(__file__).resolve().parents[1]
platform = dt.parents[2]
root = platform.parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--clang', default=str(platform/'prebuilts/clang/host/linux-x86/clang-r510928/bin/clang'))
parser.add_argument('--dtc', default=str(root/'out/host/linux-x86/bin/dtc'))
parser.add_argument('--fdtoverlay', default=str(root/'out/host/linux-x86/bin/fdtoverlay'))
args = parser.parse_args()
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=True)
k = dt.parent/'sm8450-kernel'
m = dt.parent/'sm8450-modules/qcom/opensource'
includes = [
    k / 'include', k / 'scripts/dtc/include-prefixes', dt / 'qcom',
    m / 'audio-kernel/include', m / 'camera-kernel', m / 'synx-kernel',
]


def build(name):
    source = dt / 'qcom' / f'{name}.dts'
    preprocessed = out / f'{name}.pp'
    extension = '.dtbo' if 'overlay' in name else '.dtb'
    output = out / (name + extension)
    command = [
        args.clang, '-E', '-nostdinc', '-undef', '-D__DTS__',
        '-x', 'assembler-with-cpp',
        *[value for path in includes for value in ['-I', str(path)]],
        str(source), '-o', str(preprocessed),
    ]
    process = subprocess.run(command, capture_output=True, text=True)
    diagnostics = process.stderr
    if not process.returncode:
        process = subprocess.run(
            [args.dtc, '-@', '-I', 'dts', '-O', 'dtb', '-o',
             str(output), str(preprocessed)],
            capture_output=True, text=True,
        )
        diagnostics += process.stderr
    (out / f'{name}.log').write_text(diagnostics)
    return name, process.returncode, diagnostics[-2500:] if process.returncode else ''


def check_bindings(path):
    data = path.read_bytes()
    offset, strings = struct.unpack_from('>II', data, 8)
    stack = []
    nodes = {}
    while True:
        token = struct.unpack_from('>I', data, offset)[0]
        offset += 4
        if token == 1:
            end = data.index(b'\0', offset)
            stack.append(data[offset:end].decode())
            offset = (end + 4) & ~3
            nodes['/'.join(stack)] = {}
        elif token == 2:
            stack.pop()
        elif token == 3:
            size, name_offset = struct.unpack_from('>II', data, offset)
            offset += 8
            end = data.index(b'\0', strings + name_offset)
            name = data[strings + name_offset:end].decode()
            nodes['/'.join(stack)][name] = data[offset:offset + size]
            offset = (offset + size + 3) & ~3
        elif token == 4:
            continue
        elif token == 9:
            break
        else:
            raise ValueError(f'{path}: invalid FDT token {token}')

    for name, properties in nodes.items():
        compatible = properties.get('compatible', b'').split(b'\0')
        parent = nodes.get(name.rpartition('/')[0], {})
        if b'qcom,sde-rsc-rpmh' in compatible:
            # rpmh.c interprets the immediate parent's data as rsc_drv.
            if 'qcom,drv-id' not in parent or 'qcom,tcs-offset' not in parent:
                raise ValueError(f'{path}: {name} must be a child of an RSC DRV')
        if b'qcom,usb-bam-msm' in compatible:
            address_cells = int.from_bytes(parent.get('#address-cells', b'\0\0\0\2'), 'big')
            size_cells = int.from_bytes(parent.get('#size-cells', b'\0\0\0\1'), 'big')
            stride = 4 * (address_cells + size_cells)
            registers = properties.get('reg', b'')
            if not stride or not registers or len(registers) % stride:
                raise ValueError(f'{path}: {name} has an invalid MMIO register encoding')


waipio_boards = ['zeus', 'cupid']
cape_boards = ['diting', 'mayfly', 'mondrian', 'thor', 'unicorn', 'zizhan']
names = (
    ['waipio', 'waipio-v2', 'cape']
    + [board + '-sm8450-pm8008-overlay' for board in waipio_boards]
    + [board + '-sm8475-pm8008-overlay' for board in cape_boards]
)
failed = False
for name, status, error in concurrent.futures.ThreadPoolExecutor().map(build, names):
    print(name, 'FAIL' if status else 'PASS', error)
    failed |= bool(status)
if failed:
    sys.exit(1)
results = []
for base in ['waipio', 'waipio-v2', 'cape']:
    boards = waipio_boards if base != 'cape' else cape_boards
    for board in boards:
        soc = 'sm8475' if base == 'cape' else 'sm8450'
        overlay = out/f'{board}-{soc}-pm8008-overlay.dtbo'
        combined = out/f'{base}-{board}.dtb'
        proc = subprocess.run([args.fdtoverlay, '-i', str(out/(base+'.dtb')), '-o', str(combined), str(overlay)], capture_output=True, text=True)
        print(base, board, 'FAIL' if proc.returncode else 'PASS', proc.stderr)
        failed |= bool(proc.returncode)
        binding_error = ''
        if not proc.returncode:
            try:
                check_bindings(combined)
            except ValueError as error:
                binding_error = str(error)
                print(binding_error)
                failed = True
        results.append({'base': base, 'board': board, 'passed': not proc.returncode and not binding_error})
(out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
sys.exit(1 if failed else 0)
