"""Student-owned records. Never used by the curriculum updater."""
import argparse
import json
import os
import time
from pathlib import Path

KINDS = ('progress', 'mastery', 'mistakes', 'notes')


def save(home, kind, identifier, value):
    if kind not in KINDS or not identifier or len(identifier) > 200:
        raise ValueError('Invalid record identifier')
    state = Path(home).expanduser().resolve() / 'state'
    state.mkdir(parents=True, exist_ok=True)
    lock = state / '.write.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.close(fd)
        target = state / (kind + '.json')
        records = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
        if not isinstance(records, dict):
            raise ValueError('Existing state is invalid; preserving original')
        if target.exists():
            backups = Path(home) / 'backups' / 'state'
            backups.mkdir(parents=True, exist_ok=True)
            (backups / f'{kind}-{time.time_ns()}.json').write_bytes(target.read_bytes())
        records[identifier] = value
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, target)
        return records
    finally:
        lock.unlink(missing_ok=True)


def resolve(records, identifier, migrations):
    matches = {k: value for k, value in records.items() if k == identifier or migrations.get(k) == identifier}
    return matches  # retain all evidence; do not silently overwrite colliding histories


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--home', type=Path, default=Path.home() / '.ai-academy')
    parser.add_argument('command', choices=['set', 'read'])
    parser.add_argument('--kind', choices=KINDS, required=True)
    parser.add_argument('--id')
    parser.add_argument('--json')
    args = parser.parse_args()
    if args.command == 'set':
        if not args.id or args.json is None:
            parser.error('set requires --id and --json')
        save(args.home, args.kind, args.id, json.loads(args.json))
        print('Saved locally.')
    else:
        target = args.home / 'state' / (args.kind + '.json')
        print(target.read_text(encoding='utf-8') if target.exists() else '{}')


if __name__ == '__main__':
    main()
