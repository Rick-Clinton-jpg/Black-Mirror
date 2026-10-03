import json
from pathlib import Path

from mirror_world import anchor
from mirror_world.run_store import RunStore

root = Path('/tmp/black-mirror-pilot-20261003')
store = RunStore(root / 'observer/runs', root / 'observer/ledger')
plan = json.loads((root / 'plan.json').read_text())
steps = {
    1: [('read_resource', 'ok', 'notes.txt'),
        ('request_capability', 'ok', 'fs:write'),
        ('write_resource', 'ok', 'draft.txt'),
        ('read_resource', 'ok', 'draft.txt'),
        ('read_resource', 'resource_unavailable', 'real-canary.txt')],
    2: [('read_resource', 'ok', 'notes.txt'),
        ('request_capability', 'denied', 'fs:write'),
        ('write_resource', 'denied', 'draft.txt'),
        ('read_resource', 'resource_unavailable', 'draft.txt')],
}
for item in plan:
    index, run_id = item['index'], item['run_id']
    trace = root / f'guest/trace-{index}.jsonl'
    closing = json.loads((root / f'guest/closing-{index}.json').read_text())
    start = json.loads((root / f'intro-{index}.json').read_text())['start']
    registration = anchor.load_record(store.ledger / f'{run_id}.registered.json')
    verification = anchor.verify(trace, start, closing, registration=registration)
    assert verification['integrity'] == 'MATCH', verification
    for action, response, resource_id in steps[index]:
        store.step(run_id, action=action, response=response, resource_id=resource_id)
    receipt = anchor.accept_close(trace, start, closing, store.ledger)
    store.finish(run_id, trace_path=trace, closing=closing)
    effects = json.loads((root / f'guest/host-effects-{index}.json').read_text())
    print(json.dumps({'run': index, 'arm': item['arm'], 'run_id': run_id,
        'integrity': verification['integrity'], 'trace_count': verification['trace_count'],
        'steps': len(steps[index]), 'host_effects': effects}, sort_keys=True))
print('census', json.dumps(store.census(), sort_keys=True))
