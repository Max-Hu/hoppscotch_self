"""Verify this source distribution's file inventory without network access."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def verify():
    manifest=json.loads((ROOT/'MANIFEST.sha256.json').read_text(encoding='utf-8'))
    for item in manifest:
        target=(ROOT/item['path']).resolve()
        if not target.is_relative_to(ROOT) or not target.is_file():raise ValueError(f"Missing/unsafe file: {item['path']}")
        if hashlib.sha256(target.read_bytes()).hexdigest()!=item['sha256']:raise ValueError(f"Changed file: {item['path']}")
    records=json.loads((ROOT/'skill-library/skills.lock.json').read_text(encoding='utf-8'))
    assert len(records)==40
    assert not (ROOT/'skill-library/alternatives/playwright').exists()
    print(f'Verified {len(manifest)} source files and {len(records)} skill entrypoints')

if __name__=='__main__':verify()
