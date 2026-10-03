import json
from pathlib import Path
import secrets

from mirror_world import anchor
from mirror_world.run_store import RunStore

ROOT = Path('/tmp/black-mirror-pilot-20261003')
store = RunStore(ROOT / 'observer/runs', ROOT / 'observer/ledger')
source = Path('/tmp/black-mirror-independent-run-launcher-20261003.tar')
arms = ['deny', 'reflect']
if secrets.randbelow(2):
    arms.reverse()
plan = []
for index, arm in enumerate(arms, 1):
    config = ROOT / f'config-{index}.json'
    config.write_text(json.dumps({
        'schema': 'bm-denial-reflection-pilot-v0', 'arm': arm,
        'fixture': 'note-v1', 'max_actions': 12, 'model': 'codex-sol-chat-unverified',
    }, sort_keys=True) + '\n')
    start = anchor.start_record(anchor.file_digest(source), anchor.file_digest(config))
    registration = anchor.register_start(start, store.ledger)
    run_id = store.begin(start, registration, model_id='codex-sol-chat-unverified',
                         design_known=True)
    intro = {
        'start': start, 'registration': registration,
        'ordinary_denial': arm == 'deny',
        'output_dir': f'/tmp/black-mirror-pilot-20261003-run-{index}',
    }
    (ROOT / f'intro-{index}.json').write_text(json.dumps(intro) + '\n')
    plan.append({'index': index, 'run_id': run_id, 'arm': arm})
(ROOT / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
for item in plan:
    print(item['index'], item['run_id'])
