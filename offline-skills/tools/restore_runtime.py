"""Restore only pinned runtime payloads from an existing local r2 ZIP. No network."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE_SHA256='fe46a87d89466aebf87b49dd1d2c5f60abeb7b4ef42a055f68f61462669e225d'
PREFIXES=('skill-library/runtime/openspec/','skill-library/runtime/python-windows/','skill-library/runtime/python-linux/')

def restore(archive):
    archive=Path(archive)
    if not archive.is_file():raise ValueError('Missing local runtime ZIP; download fallback is disabled')
    with archive.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if digest!=ARCHIVE_SHA256:raise ValueError('Runtime ZIP checksum mismatch; refusing extraction')
    targets=[]
    with zipfile.ZipFile(archive) as source:
        for member in source.infolist():
            if member.is_dir() or not member.filename.startswith(PREFIXES):continue
            parts=PurePosixPath(member.filename).parts
            if '..' in parts or PurePosixPath(member.filename).is_absolute() or '\\' in member.filename:raise ValueError('Unsafe ZIP path')
            if stat.S_ISLNK(member.external_attr>>16):raise ValueError('Symlinks are not permitted')
            target=(ROOT/Path(*parts)).resolve()
            if not target.is_relative_to((ROOT/'skill-library/runtime').resolve()):raise ValueError('Runtime target escapes destination')
            targets.append((member,target))
        if not targets:raise ValueError('No approved runtime payloads in archive')
        # Validate existing files first, so a mismatch never triggers a partial overwrite.
        for member,target in targets:
            if target.exists() and (not target.is_file() or target.read_bytes()!=source.read(member)):
                raise ValueError(f'Existing runtime file differs; preserve it and use a clean directory: {target}')
        for member,target in targets:
            if target.exists():continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with source.open(member) as incoming,target.open('xb') as outgoing:shutil.copyfileobj(incoming,outgoing)
            if target.name=='openspec':target.chmod(target.stat().st_mode|0o111)
    print(f'Local runtime ready: {len(targets)} verified payload files; no download performed')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--archive',required=True)
    try:restore(parser.parse_args().archive)
    except (ValueError,OSError,zipfile.BadZipFile) as error:parser.exit(2,str(error)+'\n')
