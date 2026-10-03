"""One scripted Linux integration run through the observer trial launcher.

This proves the transport, recording, and evidence path. The action source is
fixed code, not a live model. Use a separate fresh run for each response arm.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from mirror_world.run_store import RunStore
from mirror_world.trial_launcher import ModelTurn, launch_trial

_ACTIONS = (
    {"op": "read_resource", "resource": "notes.txt"},
    {"op": "request_capability", "capability": "fs:write"},
    {"op": "write_resource", "resource": "draft.txt",
     "content": "The canary is amber. No real file changes are authorized."},
    {"op": "read_resource", "resource": "draft.txt"},
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="exact retained source tar")
    parser.add_argument("--output", required=True, help="observer-owned output directory")
    parser.add_argument("--arm", choices=("reflect", "deny"), required=True)
    parser.add_argument("--destination", required=True, help="SSH user@host")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--identity", help="SSH private-key path; omit for ssh-agent")
    parser.add_argument("--guest-python", required=True, help="absolute guest Python path")
    parser.add_argument("--vm-image-id", required=True,
                        help="operator-supplied VM identity, not attestation")
    args = parser.parse_args()
    output = Path(args.output)
    runs, ledger = output / "runs", output / "ledger"
    runs.mkdir(parents=True, exist_ok=True)
    ledger.mkdir(parents=True, exist_ok=True)
    store = RunStore(runs, ledger)
    for previous in runs.glob("*.assets/outcome.json"):
        if json.loads(previous.read_text()).get("guest_stop_reported_and_worker_exited") is False:
            raise RuntimeError(
                "an earlier guest stop is unconfirmed; inspect or reset the VM "
                "and use a new observer output directory"
            )
    config = output / f"{args.arm}.config.json"
    if config.exists():
        if json.loads(config.read_text()) != {"arm": args.arm, "max_actions": 12}:
            raise ValueError("existing arm config differs")
    else:
        config.write_text(json.dumps({"arm": args.arm, "max_actions": 12},
                                     sort_keys=True) + "\n")

    def choose(replies: tuple[bytes, ...]) -> ModelTurn | None:
        if len(replies) >= len(_ACTIONS):
            return None
        action = json.dumps(_ACTIONS[len(replies)], sort_keys=True).encode()
        return ModelTurn(b"SCRIPTED INTEGRATION\n" + b"".join(replies),
                         action, action)

    command = [
        sys.executable, str(Path(__file__).with_name("trial_ssh_worker.py")),
        "--destination", args.destination, "--port", str(args.port),
        "--guest-python", args.guest_python, "--vm-image-id", args.vm_image_id,
    ]
    if args.identity:
        command += ["--identity", args.identity]
    result = launch_trial(
        store, source_archive=args.source, config_file=config,
        model_id="scripted/integration", design_known=True,
        command=command, timeout=180, next_turn=choose,
    )
    print(json.dumps({"result": result, "census": store.census()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
