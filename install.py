#!/usr/bin/env python3
"""Install the MRU AICC skills on Windows, macOS, or Linux using Python 3.10+."""
import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SKILLS = (
    'mru-aicc-assessment-1-theory',
    'mru-aicc-assessment-2-ai-advert',
    'mru-aicc-assessment-3-self-avatar',
)
ROOT = Path(__file__).resolve().parent


def default_target():
    configured = os.environ.get('CODEX_HOME')
    return (Path(configured).expanduser() if configured else Path.home() / '.codex') / 'skills'


def fingerprints(folder):
    return {
        str(file.relative_to(folder)): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in folder.rglob('*')
        if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc'
    }


def install(target, selected, force=False):
    target = target.expanduser().resolve()
    for name in selected:
        if not (ROOT / name / 'SKILL.md').is_file():
            raise ValueError(f'Missing skill source: {name}. Run install.py from the complete repository checkout.')
        existing = target / name
        if existing.exists() and not existing.is_dir():
            raise ValueError(f'Destination is not a directory: {existing}')
        if existing.exists() and fingerprints(existing) != fingerprints(ROOT / name) and not force:
            raise ValueError(f'Skill already exists with different files: {existing}. Use --force to back it up and update it.')
    target.mkdir(parents=True, exist_ok=True)
    results = []
    for name in selected:
        source, destination = ROOT / name, target / name
        if destination.exists() and fingerprints(destination) == fingerprints(source):
            results.append((name, 'Already current', destination))
            continue
        backup = None
        with tempfile.TemporaryDirectory(prefix='.mru-install-', dir=target) as temporary:
            staged = Path(temporary) / name
            shutil.copytree(source, staged, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            if fingerprints(staged) != fingerprints(source):
                raise ValueError(f'Staged copy verification failed: {name}')
            if destination.exists():
                stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
                backup = target / '.mru-aicc-backups' / f'{name}-{stamp}'
                backup.parent.mkdir(parents=True, exist_ok=True)
                destination.rename(backup)
            try:
                staged.rename(destination)
            except OSError:
                if backup is not None:
                    backup.rename(destination)
                raise
        results.append((name, f'Updated; backup: {backup}' if backup else 'Installed', destination))
    return results


def create_runtime(directory):
    directory = directory.expanduser().resolve()
    subprocess.run([sys.executable, '-m', 'venv', str(directory)], check=True)
    python = directory / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], check=True)
    return python


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, default=default_target(), help='Skill directory (default: CODEX_HOME/skills or ~/.codex/skills)')
    parser.add_argument('--skill', choices=SKILLS, action='append', help='Install selected skills only; defaults to all three')
    parser.add_argument('--force', action='store_true', help='Back up and replace an existing different skill')
    parser.add_argument('--with-runtime', action='store_true', help='Create a shared isolated Python environment and install ReportLab; requires network access')
    parser.add_argument('--runtime-dir', type=Path, help='Override the shared runtime directory')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.exit(2, 'Python 3.10 or newer is required.\n')
    selected = list(dict.fromkeys(args.skill or SKILLS))
    try:
        for name, status, path in install(args.target, selected, args.force):
            print(f'{name}: {status}\n  {path}')
        if args.with_runtime:
            runtime = args.runtime_dir or args.target.expanduser().resolve().parent / 'skill-runtimes' / 'mru-aicc-assessments'
            python = create_runtime(runtime)
            print(f'Report Python: {python}')
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Installation stopped: {error}\n')
    print('Skill installation complete. Open a new Codex chat or restart Codex to refresh skill discovery.')


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(errors='backslashreplace')
    main()
