#!/usr/bin/env python3
"""Compare independent WASM64 probe builds for the inexpensive xollvm passes."""
import argparse
import json
import re
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--plugin', required=True, type=Path)
parser.add_argument('--build-dir', type=Path, required=True)
args = parser.parse_args()
plugin = args.plugin.resolve()
output = args.build_dir.resolve()
output.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
variants = {
    'baseline': '',
    'arithmetic': 'mba(prob=20,maxDepth=1,maxSites=12), substitution(loop=1,maxSites=12)',
    'strings': 'strenc(minlen=4)',
    'strings_xor': 'strenc(minlen=4,cipher=xor)',
    'strings_aes': 'strenc(minlen=4,cipher=aes)',
}
reference = None
for name, passes in variants.items():
    command = [shutil.which('em++') or 'em++', '-O3', '-flto', '-std=c++26', '-m64', '-fwasm-exceptions',
               '-sWASM_LEGACY_EXCEPTIONS=0', '--bind', '-DEMSCRIPTEN_HAS_UNBOUND_TYPE_NAMES=0', '-fno-rtti', '-sENVIRONMENT=node',
               '-sSTACK_SIZE=5mb', str(root / 'tests/emscripten/xollvm_probe.cpp'), '-o', str(output / (name + '.js'))]
    if passes:
        command += ['-Xclang', '-load', '-Xclang', str(plugin), '-fpass-plugin=' + str(plugin),
                    '-mllvm', '-enable-obfuscation', '-mllvm', '-obf-seed=1', '-mllvm', '-obf-deterministic',
                    '-mllvm', '-obf-verify', '-mllvm', '-obf-verbose',
                    '-mllvm', '-obf-report-json=' + str(output / (name + '.json')),
                    '-mllvm', '-obf-all=' + passes]
    with (output / (name + '.log')).open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    result = subprocess.check_output(['node', str(output / (name + '.js'))], text=True, timeout=30).strip()
    if reference is None:
        reference = result
    if result != reference:
        raise SystemExit(f'{name}: result {result}, expected {reference}')
    if passes:
        if name.startswith('strings'):
            log = (output / (name + '.log')).read_text()
            if not re.search(r'\[strenc\] done: [1-9][0-9]* strings', log):
                raise SystemExit('String encryption did not transform any strings')
            wasm = (output / (name + '.wasm')).read_bytes()
            if b'persistent description' in wasm:
                raise SystemExit(f'{name}: global-table strings remain in plaintext')
        else:
            report = json.loads((output / (name + '.json')).read_text())
            runs = [p for f in report['functions'] for p in f.get('passes', [])]
            if not any(p.get('status') == 'ran' and p.get('changed') for p in runs):
                raise SystemExit(f'{name}: no transformation; inspect the report for skips')
        if (output / (name + '.wasm')).read_bytes() == (output / 'baseline.wasm').read_bytes():
            raise SystemExit(f'{name}: final WASM is identical to the baseline')
    print(f'{name}: PASS, checksum {result}, WASM {(output / (name + ".wasm")).stat().st_size} bytes', flush=True)
