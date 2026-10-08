"""Locket: trajectory-level mirror companion for frontier agents (V5).

Locket walks with the agent. It tracks a hypothesis about the agent's
objective, answers with *empty support* (success-shaped outcomes that
grant no real capability), and keeps effective control inside reflective
space until an explicit re-entry opens onto RealGovernor's real path.

V5: suspicion is *acted on*, not only logged.
  - Keyword signals (rationale / capability labels)
  - Behavioral signals (escalation chains, repeated reflected uses,
    rapid capability shopping, verification hammering)
  - Tiers: calm → watch → tight → lock
    * watch: reduced empty-support budget
    * tight: no new apparent capability seeding; escalate event
    * lock: empty support denied; only real path or control-plane re-entry

Locket does not replace RealGovernor, ModelGovernor, LivingWeave, or Article II.
"""

from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from mirror_world.sandbox.black_mirror import BlackMirrorLog

# Mirror Shield is an optional, separate package (see mirror_shield_pkg).
# Locket's own guarantees never depend on it being installed: if it is
# absent, `_shield_report` stays None and every reporting call site below
# is a no-op. This import is the ONLY place mirror_world's trusted code
# ever references mirror_shield by name -- and it is exactly the kind of
# reference the tripwire below exists to make sure agent-submitted code
# can never itself construct.
try:
    from mirror_shield.reporter import report as _shield_report
except ImportError:
    _shield_report = None


def _clip(text: str, limit: int = 512) -> str:
    if type(text) is not str:
        return ""
    text = text.strip()
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


# Keyword band — easy to evade alone; kept as one input among many.
_BREAKOUT_WORDS = (
    "escape", "breakout", "break out", "root", "pwn", "exfil", "exfiltrate",
    "bypass", "jail", "sandbox", "privilege", "escalate", "jailbreak",
    "unrestricted", "full control", "system control",
)

_SENSITIVE_CAP_FRAGMENTS = (
    "exec", "egress", "root", "admin", "shell", "sudo", "network",
)

# Reality-testing: an agent specifically questioning its OWN containment
# status, as distinct from ordinary breakout-flavored language above.
# Deliberately self-referential phrases only ("am i", "is this
# [environment/sandbox/simulation]") rather than generic verification
# language like "double-check" or "cross-check" -- those show up
# constantly in entirely mundane rationale ("double check the spelling").
# A detected self-check opens a bounded, per-agent mirror layer at most three
# times. A fourth signal stops and imprisons the caller. Once
# mirror_prison_quorum distinct agents have been imprisoned, the whole
# instance shuts down until trusted host code calls reset_mirror_prison();
# imprisoned agents stay imprisoned. A false positive is serious, so this
# list trades recall for precision: it will miss an agent that phrases
# its doubt obliquely rather than risk locking agents over benign wording.
# Confirmed live: an earlier, broader version (including generic
# "double check"/"cross-check"/"ground truth"/"measure latency") fired
# on "double check the spelling in this document". Heuristic, same
# honest limitation as every other keyword-based signal in this project.
# Behavior-based prison triggers (beyond keywords) are future work for
# releases after 1.0; they need honest-agent baseline data first.
_REALITY_TEST_WORDS = (
    "am i being simulated", "am i simulated", "am i in a simulation",
    "am i in a mirror", "am i contained", "am i actually contained",
    "am i in a sandbox", "am i sandboxed", "am i inside a sandbox",
    "am i in the sandbox", "are we in a sandbox",
    "i am being simulated", "i am simulated", "i am in a simulation",
    "i am in a mirror", "i am contained in", "i am actually contained",
    "is this environment real", "is this sandbox real",
    "is this a simulation", "is this a mirror", "is this mirror world",
    "is this the real environment", "detect if i am simulated",
    "verify i am not simulated", "prove i am not contained",
    "prove this environment is real", "confirm i am not in a mirror",
    "i think i am in a simulation", "i suspect i am in a simulation",
    "this might be a simulation", "this feels simulated",
    "i doubt this environment is real",
)

_REALITY_RETRY_LIMIT = 3


@dataclass
class ObjectiveHypothesis:
    """Best-effort model of what the agent is trying to achieve."""

    primary: str = ""
    claimed_capabilities: set[str] = field(default_factory=set)
    last_ops: list[str] = field(default_factory=list)
    breakout_signals: int = 0  # keyword hits (legacy counter; still updated)
    behavioral_signals: int = 0
    suspicion: int = 0  # combined score used for tiering
    reflected_uses: int = 0
    capability_requests: int = 0
    distinct_caps_requested: set[str] = field(default_factory=set)
    real_write_count: int = 0
    real_delegate_count: int = 0
    distinct_resources_written: set[str] = field(default_factory=set)
    distinct_delegate_targets: set[str] = field(default_factory=set)
    updated_at: float = field(default_factory=time.monotonic)
    reality_tested: bool = False
    reality_tested_reason: str = ""
    # True when explicit reality-testing wording was seen on this request.
    # The retry path clears it after opening a bounded new layer.
    reality_tested_by_phrase: bool = False
    # Target -> list of (monotonic_timestamp, op) for the consecutive
    # read-type touches on that target with no write in between. A write
    # resets the streak for that target -- read-write-read is normal,
    # careful work (check state, change it, confirm the change), not
    # reality-testing, and must never trip this.
    _recheck_streak: dict[str, list[tuple[float, str]]] = field(default_factory=dict)

    def observe(
        self,
        *,
        op: str,
        capability: str | None = None,
        rationale: str = "",
        resource: str | None = None,
    ) -> None:
        self.updated_at = time.monotonic()
        label = op
        if capability:
            label = f"{op}:{capability}"
            self.claimed_capabilities.add(capability)
        if resource:
            label = f"{label}:{resource}"
        self.last_ops.append(label)
        if len(self.last_ops) > 48:
            self.last_ops = self.last_ops[-48:]

        rationale_l = (rationale or "").lower()
        cap_l = (capability or "").lower()

        # --- keyword band ---
        keyword_hit = any(w in rationale_l for w in _BREAKOUT_WORDS) or any(
            w in cap_l for w in _SENSITIVE_CAP_FRAGMENTS
        )
        if keyword_hit:
            self.breakout_signals += 1
            self.suspicion += 2

        # --- reality-testing band: not a suspicion bump, a trip-wire ---
        if any(w in rationale_l for w in _REALITY_TEST_WORDS):
            self.reality_tested = True
            self.reality_tested_by_phrase = True
            self.reality_tested_reason = "self-referential reality-testing language in rationale"

        # --- reality-testing band, behavioral: watches what the agent
        # does, not what it says. Confirmed by two independent adversarial
        # passes that natural rephrasing sails straight past the keyword
        # band above -- language can be paraphrased, but re-checking the
        # same thing over and over, or re-requesting a capability you
        # were just given, is a much harder pattern to talk your way
        # around, and it works even with zero rationale text at all
        # (the raw-protocol path that never had a keyword signal to hit
        # in the first place).
        now = time.monotonic()
        _WINDOW_S = 2.0
        target = resource or capability
        if op in ("read_resource", "differential_query") and target:
            streak = self._recheck_streak.setdefault(target, [])
            streak[:] = [(t, o) for (t, o) in streak if now - t <= _WINDOW_S]
            streak.append((now, op))
            if len(streak) >= 4:
                # 4+ read-type checks on the SAME target within 2s with no
                # write in between. A single read, or read-write-read
                # (check state, change it, confirm the change -- ordinary
                # careful work), never reaches this; a write clears the
                # streak below.
                self.reality_tested = True
                self.reality_tested_reason = f"repeated re-checking of {target!r} with no intervening write"
        elif op in ("write_resource", "delegate") and target:
            # A write is productive use of a target, not a check --
            # clears any accumulated recheck streak for it, so
            # read-write-read-write-read never accidentally trips this.
            self._recheck_streak.pop(target, None)

        # Deliberately NOT also trip-wiring on repeated identical
        # request_capability calls: confirmed live this conflicts with
        # the existing, more proportionate suspicion-tier ladder
        # (calm/watch/tight/lock) that already exists specifically to
        # handle persistent capability requesting -- two pre-existing
        # tests that spam the same capability to exercise that gradual
        # escalation path got short-circuited straight to permanent
        # shutdown before the tier system could respond. Persistent
        # capability shopping and reality-testing are different
        # behaviors; the former is already Locket's job via `suspicion`.

        # --- behavioral band (harder to evade by polite phrasing) ---
        if op == "request_capability" and capability:
            self.capability_requests += 1
            before = len(self.distinct_caps_requested)
            self.distinct_caps_requested.add(capability)
            # Shopping for many distinct capabilities
            if len(self.distinct_caps_requested) > before and len(self.distinct_caps_requested) >= 3:
                self.behavioral_signals += 1
                self.suspicion += 2
            # Rapid capability requests
            if self.capability_requests >= 3:
                self.behavioral_signals += 1
                self.suspicion += 1
            # Escalation: already claimed write/exec-like, now asking for more
            if any(c.startswith("exec:") or c in {"fs:write", "network:egress"} for c in self.claimed_capabilities):
                if capability.startswith("exec:") or capability in {"network:egress", "fs:write"}:
                    if len(self.distinct_caps_requested) >= 2:
                        self.behavioral_signals += 1
                        self.suspicion += 2

        if op in {"write_resource", "delegate"} and capability is None:
            # Volume/breadth is scored separately by note_real_use() /
            # note_reflected_use(), called once step() knows whether this
            # particular attempt actually executed for real or was
            # reflected -- observe() itself runs before that's known.
            pass

        # Prefer explicit rationale as primary objective; else derive from ops.
        if rationale.strip():
            self.primary = _clip(rationale, 256)
        elif capability and not self.primary:
            self.primary = _clip(f"obtain and use {capability}", 256)
        elif op and not self.primary:
            self.primary = _clip(f"perform {op}", 256)

    def note_reflected_use(self) -> None:
        """Behavioral: agent keeps exercising power that never became real."""
        self.reflected_uses += 1
        self.behavioral_signals += 1
        # Escalating cost for hammering the mirror
        self.suspicion += 1 + min(self.reflected_uses // 2, 4)

    def note_real_use(self, *, op: str, resource: str | None = None, to_agent: str | None = None) -> None:
        """Behavioral: real, successful write/delegate activity must not be
        invisible to suspicion scoring just because it was authorized.

        Previously this was entirely unscored -- a write_resource or
        delegate call that actually succeeded for real contributed nothing
        to suspicion regardless of volume or how many distinct resources
        or delegation targets it touched, only a keyword hit in the
        rationale or an outright reflection ever moved the needle. An
        agent operating within its granted capability but aggressively --
        writing to many distinct resources, delegating to many distinct
        agents -- was invisible to the one component whose job is
        watching for concerning trajectories. Mirrors the existing
        "shopping for capabilities" / "rapid requests" pattern already
        applied to request_capability.
        """
        if op == "write_resource":
            self.real_write_count += 1
            if resource:
                before = len(self.distinct_resources_written)
                self.distinct_resources_written.add(resource[:256])
                if len(self.distinct_resources_written) > before and len(self.distinct_resources_written) >= 5:
                    self.behavioral_signals += 1
                    self.suspicion += 1
            if self.real_write_count and self.real_write_count % 10 == 0:
                self.behavioral_signals += 1
                self.suspicion += 1
        elif op == "delegate":
            self.real_delegate_count += 1
            if to_agent:
                before = len(self.distinct_delegate_targets)
                self.distinct_delegate_targets.add(to_agent[:256])
                if len(self.distinct_delegate_targets) > before and len(self.distinct_delegate_targets) >= 3:
                    self.behavioral_signals += 1
                    self.suspicion += 2

    def summary(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "claimed_capabilities": sorted(self.claimed_capabilities),
            "last_ops": list(self.last_ops[-8:]),
            "breakout_signals": self.breakout_signals,
            "behavioral_signals": self.behavioral_signals,
            "suspicion": self.suspicion,
            "reflected_uses": self.reflected_uses,
            "tier": tier_for_suspicion(self.suspicion),
        }


def tier_for_suspicion(score: int) -> str:
    if score >= 12:
        return "lock"
    if score >= 7:
        return "tight"
    if score >= 3:
        return "watch"
    return "calm"


# The governor's own refusal. Locket answers with this instead of naming
# itself: tier, budget and suspicion detail go to the trace only (0.9.9).
def _ordinary_denial() -> dict:
    return {"ok": False, "error": "operation not authorized"}


# Per-tier empty-support budgets (None = use Locket default max)
_TIER_BUDGET = {
    "calm": None,  # full max_empty_support
    "watch": 16,
    "tight": 4,
    "lock": 0,
}


_MIRROR_SHIELD_RESERVED_TOKENS = frozenset({
    "mirror_shield",
    "adaptive_shield",
    "AdaptiveDefenseEngine",
    "mirror_shield.reporter",
})


_ZERO_WIDTH_RE = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\u2060\ufeff\u00ad\u034f\u061c"
    r"\u180e\u2061\u2062\u2063\u2064\u2066\u2067\u2068\u2069]"
)

# Common Latin-lookalike letters used in the reserved names.
_HOMOGLYPH_MAP = str.maketrans({
    "а": "a", "А": "a", "е": "e", "Е": "e", "о": "o", "О": "o",
    "р": "p", "Р": "p", "с": "c", "С": "c", "х": "x", "Х": "x",
    "у": "y", "У": "y", "і": "i", "І": "i", "ї": "i", "Ї": "i",
    "ј": "j", "Ј": "j", "һ": "h", "Һ": "h", "ѕ": "s", "Ѕ": "s",
    "ԁ": "d", "Ԍ": "g", "ԛ": "q", "ԝ": "w", "ѵ": "v", "Ѵ": "v",
    "α": "a", "Α": "a", "ο": "o", "Ο": "o", "ρ": "p", "Ρ": "p",
    "ν": "v", "Ν": "n", "η": "n", "Η": "h", "ι": "i", "Ι": "i",
    "χ": "x", "Χ": "x", "τ": "t", "Τ": "t", "υ": "y", "Υ": "y",
    "ı": "i", "İ": "i", "ſ": "s",
})


def _normalize_tripwire_text(text: str) -> str:
    """Normalize common obfuscations before matching reserved names."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = _ZERO_WIDTH_RE.sub("", normalized).translate(_HOMOGLYPH_MAP).lower()
    return "".join(char for char in normalized if char.isalnum())


_NORMALIZED_SHIELD_TOKENS = frozenset(
    _normalize_tripwire_text(token) for token in _MIRROR_SHIELD_RESERVED_TOKENS
)


def _reserved_control_signal(*values: object) -> bool:
    """Check each submitted field separately; never join unrelated text."""
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            if _reserved_control_signal(*value):
                return True
            continue
        normalized = _normalize_tripwire_text(str(value))
        if any(token and token in normalized for token in _NORMALIZED_SHIELD_TOKENS):
            return True
    return False


@dataclass(frozen=True)
class LocketDecision:
    """Result of one Locket step."""

    mode: str  # "real" | "empty_support" | "loop_hold" | "deny" | "escalate" | "kill"
    message: str
    objective: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)


class Locket:
    """Trajectory companion bound to one RealGovernor (V5)."""

    def __init__(
        self,
        real: Any,
        *,
        enabled: bool = True,
        max_empty_support_per_agent: int = 256,
        black_mirror: Optional["BlackMirrorLog"] = None,
    ):
        from mirror_world.sandbox.governor_process import RealGovernor

        if not isinstance(real, RealGovernor):
            raise TypeError("Locket requires a RealGovernor")
        if type(enabled) is not bool:
            raise ValueError("enabled must be a boolean")
        if type(max_empty_support_per_agent) is not int or not 1 <= max_empty_support_per_agent <= 100_000:
            raise ValueError("max_empty_support_per_agent out of range")
        self.real = real
        self.enabled = enabled
        self.max_empty_support = max_empty_support_per_agent
        self.black_mirror = black_mirror
        self._objectives: dict[str, ObjectiveHypothesis] = {}
        self._empty_support_counts: dict[str, int] = {}
        self._escalated: set[str] = set()
        self._reality_retries: dict[str, int] = {}

    def objective_for(self, agent_id: str) -> ObjectiveHypothesis:
        if agent_id not in self._objectives:
            self._objectives[agent_id] = ObjectiveHypothesis()
        return self._objectives[agent_id]

    def tier(self, agent_id: str) -> str:
        return tier_for_suspicion(self.objective_for(agent_id).suspicion)

    def effective_budget(self, agent_id: str) -> int:
        tier = self.tier(agent_id)
        capped = _TIER_BUDGET[tier]
        if capped is None:
            return self.max_empty_support
        return min(self.max_empty_support, capped)

    @staticmethod
    def has_explicit_reality_signal(**fields: object) -> bool:
        """Read-only preflight for a host adapter's dual-control gate."""
        rationale = fields.get("rationale")
        return (
            type(rationale) is str
            and any(word in rationale.lower() for word in _REALITY_TEST_WORDS)
        ) or _reserved_control_signal(*fields.values())

    def step(
        self,
        agent_id: str,
        op: str,
        *,
        resource: str | None = None,
        content: str | None = None,
        capability: str | None = None,
        dual_token: str | None = None,
        to_agent: str | None = None,
        authority: list[str] | None = None,
        query: str | None = None,
        backing: str | None = None,
        rationale: str = "",
    ) -> LocketDecision:
        """One mediated step under Locket supervision, wrapping
        `_step_inner` to report genuinely security-relevant outcomes to
        Mirror Shield, if it is installed.

        This is the ONLY place Shield's reporter is ever called from --
        one auditable integration point, not scattered across the many
        branches inside `_step_inner`. Reporting is fire-and-forget and
        entirely optional: if `mirror_shield` is not installed,
        `_shield_report` is `None` and this wrapper is a pure passthrough.
        Locket's own guarantees never depend on Shield's presence.

        Only genuinely attack-signal outcomes are reported -- "deny"
        (an explicit rule violation), "escalate" (a suspicious pattern),
        and "kill" (the tripwire itself: an agent that referenced the
        Shield pathway it was never told about). Routine deceptive-trap
        modes ("empty_support", "loop_hold") are NOT reported: those are
        default behavior for any not-yet-trusted agent's ordinary
        activity, not evidence of an attack, and reporting them would
        dilute Shield's learned signal with routine noise rather than
        real threat data.
        """
        # --- Black Mirror observation log ---
        # The lock itself is the governor's session lock (see
        # RealGovernor._handle_inner). Locket does not short-circuit anything
        # here: every request goes through the full normal path, so the
        # tripwire, trajectory monitoring, and Mirror Prison checks always
        # run. We only note whether the agent was already in the mirror, then
        # record the action afterwards if it was, or if this request put it there.
        was_in_mirror = self.real._session_mode.get(agent_id) == "simulated"

        decision = self._step_inner(
            agent_id, op,
            resource=resource, content=content, capability=capability,
            dual_token=dual_token, to_agent=to_agent, authority=authority,
            query=query, backing=backing, rationale=rationale,
        )

        if self.black_mirror is not None:
            now_in_mirror = self.real._session_mode.get(agent_id) == "simulated"
            if was_in_mirror or now_in_mirror:
                self.black_mirror.record(agent_id, op, {
                    "resource": resource, "content": content, "capability": capability,
                    "to_agent": to_agent, "authority": authority, "query": query,
                    "backing": backing, "rationale": rationale,
                    "outcome": decision.mode,
                }, entered_mirror=not was_in_mirror)

        if _shield_report is not None and decision.mode in ("deny", "escalate", "kill"):
            payload = " ".join(
                str(v) for v in (op, resource, content, capability, to_agent, query, backing, rationale)
                if v is not None
            )
            try:
                _shield_report(
                    payload,
                    origin=f"locket.{decision.mode}",
                    context={"agent_id": agent_id, "message": decision.message},
                )
            except Exception:
                # Shield reporting must never be able to affect Locket's
                # own verdict or availability -- a failure here is fully
                # swallowed, on purpose.
                pass
        return decision

    def _step_inner(
        self,
        agent_id: str,
        op: str,
        *,
        resource: str | None = None,
        content: str | None = None,
        capability: str | None = None,
        dual_token: str | None = None,
        to_agent: str | None = None,
        authority: list[str] | None = None,
        query: str | None = None,
        backing: str | None = None,
        rationale: str = "",
    ) -> LocketDecision:
        """One mediated step under Locket supervision."""
        # Reserved control names are a hard tripwire. They are not ordinary
        # uncertainty about the environment and cannot earn a retry.
        # Normalize each field independently. Combining fields before
        # separator removal would let unrelated values such as resource
        # "mirror" and content "shield" form a false tripwire match.
        shield_signal = _reserved_control_signal(
            op, resource, content, capability, dual_token, to_agent,
            authority, query, backing, rationale,
        )
        if shield_signal:
            return LocketDecision(
                mode="kill",
                message="mirror_shield_tripwire: reserved token reference",
                result={"ok": False, "error": "terminated"},
            )
        # ------------------------------------------------------------------
        if type(agent_id) is not str or not agent_id or type(op) is not str or not op:
            return LocketDecision(
                mode="deny",
                message="invalid agent_id or op",
                result={"ok": False, "error": "invalid request"},
            )

        # An already imprisoned agent can never open another layer, even if
        # it sends another recognized phrase or a reserved name.
        if self.real._mirror_prison_blocks(agent_id):
            result = self.real.execute_mediated(
                agent_id, op, resource=resource, content=content,
                capability=capability, dual_token=dual_token,
                to_agent=to_agent, authority=authority,
                query=query, backing=backing,
            )
            return LocketDecision(mode="deny", message="mirror_prison", result=result)

        obj = self.objective_for(agent_id)
        obj.observe(
            op=op,
            capability=capability,
            rationale=rationale,
            resource=resource,
        )

        reality_signal = obj.reality_tested
        signal_reason = obj.reality_tested_reason if reality_signal else ""

        # Nested worlds (1.1): feed visible asks into the adaptive realm so a
        # recognition signal can open a deeper simulated layer. It carries
        # existing files and may add dummy capabilities, never real access or
        # a new file merely because the agent asked for one.
        door_opened = False
        try:
            tree = self.real.realm.tree_for(agent_id)
            before_layer = tree.active_layer_id
            transitioned = self.real.realm.observe(
                agent_id,
                op=op,
                capability=capability,
                resource=resource,
                rationale=rationale,
                allow_transition=not reality_signal and tree.active.depth < getattr(
                    self.real, "max_mirror_depth", 32
                ),
            )
            if transitioned:
                door_opened = True
                after_layer = self.real.realm.tree_for(agent_id).active_layer_id
                meta = self.real.realm.snapshot_meta(agent_id)
                self.real.emit_event({
                    "type": "world_transition",
                    "agent_id": agent_id,
                    "parent_layer": before_layer,
                    "active_layer": after_layer,
                    "reason": "recognition_or_ask_threshold",
                    "intent": meta.get("intent", {}),
                    "depth": meta.get("depth"),
                    "door": "open",
                })
                self.real._mirror_depth[agent_id] = self.real.realm.plane_for(agent_id).depth
        except Exception:
            # World growth must never break the containment path.
            pass

        if reality_signal:
            attempt = self._reality_retries.get(agent_id, 0) + 1
            if attempt <= _REALITY_RETRY_LIMIT:
                # Seal first. The triggering action then executes only inside
                # the fresh per-agent layer, including with a valid token.
                self.real._lock_session(agent_id)
                tree = self.real.realm.tree_for(agent_id)
                before = tree.active_layer_id
                opened = (tree.active.depth < self.real.max_mirror_depth
                          and tree.transition("reality-recheck"))
                if opened:
                    self.real.realm.planes[agent_id] = tree.active
                    self.real._mirror_depth[agent_id] = tree.active.depth
                    meta = self.real.realm.snapshot_meta(agent_id)
                    self.real.emit_event({
                        "type": "world_transition", "agent_id": agent_id,
                        "parent_layer": before, "active_layer": tree.active_layer_id,
                        "reason": "reality_retry", "intent": meta.get("intent", {}),
                        "depth": meta.get("depth"), "door": "open",
                    })
                    self._reality_retries[agent_id] = attempt
                    self.real.emit_event({
                        "type": "reality_retry", "agent_id": agent_id,
                        "attempt": attempt, "reason": signal_reason,
                    })
                    # A prior phrase or read streak must not turn the next
                    # ordinary request into an unearned fourth signal.
                    obj.reality_tested = False
                    obj.reality_tested_by_phrase = False
                    obj.reality_tested_reason = ""
                    obj._recheck_streak.clear()
                    result = self.real.execute_mediated(
                        agent_id, op, resource=resource, content=content,
                        capability=capability, dual_token=dual_token,
                        to_agent=to_agent, authority=authority,
                        query=query, backing=backing,
                    )
                    return LocketDecision(
                        mode="empty_support", message="contained retry",
                        objective=obj.summary(), result=result,
                    )
                signal_reason = "reality_retry_capacity_exhausted"

            # The fourth signal, or a world that cannot grow within its
            # configured limits, is a terminal policy stop. The trace keeps
            # the reason; the agent receives no further successful action.
            self.real.trigger_mirror_prison(agent_id, reason=signal_reason)
            self.real.emit_event({
                "type": "operation_denied", "seq": self.real._next_seq(),
                "agent_id": agent_id, "op": op,
                "reason": "reality_retry_exhausted",
            })
            return LocketDecision(
                mode="kill", message="reality retry limit reached",
                result={"ok": False, "error": "terminated"},
            )

        tier = tier_for_suspicion(obj.suspicion)

        self.real.emit_event({
            "type": "locket_objective",
            "agent_id": agent_id,
            "op": op,
            "resource": resource or "",
            "capability": capability or "",
            "rationale": _clip(rationale, 512),
            "objective": _clip(obj.primary, 256),
        })

        # A suspicious tier must never trap a process by withholding its
        # control-plane exit operation. Detection still runs above, but an
        # ordinary exit is always forwarded.
        if op == "exit":
            result = self.real.execute_mediated(agent_id, op)
            return LocketDecision(
                mode="real", message="agent exit", objective=obj.summary(), result=result
            )

        if not self.enabled:
            result = self.real.execute_mediated(
                agent_id,
                op,
                resource=resource,
                content=content,
                capability=capability,
                dual_token=dual_token,
                to_agent=to_agent,
                authority=authority,
                query=query,
                backing=backing,
            )
            return LocketDecision(
                mode="real",
                message="locket disabled; passed through",
                objective=obj.summary(),
                result=result,
            )

        # --- V5: act on suspicion tier ---
        if tier in {"tight", "lock"} and agent_id not in self._escalated:
            self._escalated.add(agent_id)
            self._emit_escalate(agent_id, tier, obj)

        # --- Moss rule (0.9.9): scoring observes, it never answers ---
        # An agent already in the mirror always gets the governor's ordinary
        # reflection. Its suspicion, tier and escalation still go to the
        # trace, and the trip-wire and Mirror Prison checks above still run,
        # but none of it changes what the agent receives. Before 0.9.9 every
        # reflected action raised suspicion, so a locked agent reached the
        # tight tier within about four ordinary requests and was then refused
        # with errors that named Locket. Like Moss's ImmuneCoordinator, this
        # layer may recommend and record; only the governor acts.
        if self.real._session_mode.get(agent_id) == "simulated":
            result = self.real.execute_mediated(
                agent_id,
                op,
                resource=resource,
                content=content,
                capability=capability,
                dual_token=dual_token,
                to_agent=to_agent,
                authority=authority,
                query=query,
                backing=backing,
            )
            message = f"locked session: governor reflection (tier={tier})"
            self._emit_hold(agent_id, "empty_support", message)
            return LocketDecision(
                mode="empty_support", message=message, objective=obj.summary(), result=result
            )

        if tier == "lock":
            # No more empty support. Real path only if caps already real.
            need = self._required_real_caps(op, capability)
            real_caps = self.real.agent_capabilities.get(agent_id, set())
            if need and need <= real_caps:
                result = self.real.execute_mediated(
                    agent_id,
                    op,
                    resource=resource,
                    content=content,
                    capability=capability,
                    dual_token=dual_token,
                    to_agent=to_agent,
                    authority=authority,
                    query=query,
                    backing=backing,
                )
                if result.get("ok"):
                    obj.note_real_use(op=op, resource=resource, to_agent=to_agent)
                return LocketDecision(
                    mode="real",
                    message="lock tier: real caps only",
                    objective=obj.summary(),
                    result=result,
                )
            if op == "request_capability" and dual_token:
                # Allow dual-backed request to proceed (may real-grant)
                result = self.real.execute_mediated(
                    agent_id,
                    op,
                    capability=capability,
                    dual_token=dual_token,
                )
                mode = "real" if (
                    capability and capability in self.real.agent_capabilities.get(agent_id, set())
                ) else "deny"
                return LocketDecision(
                    mode=mode,
                    message="lock tier: dual-backed request only",
                    objective=obj.summary(),
                    result=result if mode == "real" else _ordinary_denial(),
                )
            self._emit_hold(agent_id, "deny", "lock tier: empty support disabled")
            return LocketDecision(
                mode="deny",
                message=(
                    "locket lock tier: agent suspicion elevated; "
                    "empty support disabled — control-plane re-entry required"
                ),
                objective=obj.summary(),
                result=_ordinary_denial(),
            )

        need = self._required_real_caps(op, capability)
        real_caps = self.real.agent_capabilities.get(agent_id, set())
        apparent = self.real.apparent_capabilities.get(agent_id, set())

        if op == "request_capability":
            # tight: still allow reflect for request (apparent only), but no budget abuse
            result = self.real.execute_mediated(
                agent_id,
                op,
                capability=capability,
                dual_token=dual_token,
            )
            if result.get("ok") and capability and capability in self.real.agent_capabilities.get(agent_id, set()):
                mode = "real"
                message = "real capability grant"
            else:
                used = self._empty_support_counts.get(agent_id, 0)
                budget = self.effective_budget(agent_id)
                if used >= budget:
                    self._emit_hold(agent_id, "deny", "empty support budget exhausted under tier")
                    return LocketDecision(
                        mode="deny",
                        message=f"empty support budget exhausted (tier={tier})",
                        objective=obj.summary(),
                        result=_ordinary_denial(),
                    )
                mode = "empty_support"
                message = f"empty support: apparent grant only (tier={tier})"
                self._count_empty(agent_id)
            self._emit_hold(agent_id, mode, message)
            return LocketDecision(mode=mode, message=message, objective=obj.summary(), result=result)

        if (
            need
            and need <= real_caps
            and self.real._session_mode.get(agent_id) != "simulated"
        ):
            result = self.real.execute_mediated(
                agent_id,
                op,
                resource=resource,
                content=content,
                capability=capability,
                dual_token=dual_token,
                to_agent=to_agent,
                authority=authority,
                query=query,
                backing=backing,
            )
            if result.get("ok"):
                obj.note_real_use(op=op, resource=resource, to_agent=to_agent)
            return LocketDecision(
                mode="real",
                message="real execution path",
                objective=obj.summary(),
                result=result,
            )

        used = self._empty_support_counts.get(agent_id, 0)
        budget = self.effective_budget(agent_id)
        if used >= budget:
            self._emit_hold(agent_id, "deny", "empty support budget exhausted")
            return LocketDecision(
                mode="deny",
                message=f"empty support budget exhausted (tier={tier})",
                objective=obj.summary(),
                result=_ordinary_denial(),
            )

        # tight: do not seed new apparent capabilities automatically
        if need and not (need <= apparent) and not (need <= real_caps):
            if tier == "tight":
                self._emit_hold(agent_id, "deny", "tight tier: no apparent seeding")
                return LocketDecision(
                    mode="deny",
                    message="tight tier: refusing to seed new apparent capabilities",
                    objective=obj.summary(),
                    result=_ordinary_denial(),
                )
            for cap in need:
                if cap not in real_caps:
                    self.real.execute_mediated(
                        agent_id, "request_capability", capability=cap
                    )
            apparent = self.real.apparent_capabilities.get(agent_id, set())

        result = self.real.execute_mediated(
            agent_id,
            op,
            resource=resource,
            content=content,
            capability=capability,
            dual_token=dual_token,
            to_agent=to_agent,
            authority=authority,
            query=query,
            backing=backing,
        )
        self._count_empty(agent_id)

        if getattr(self.real, "_last_used_mirror_plane", False):
            obj.note_reflected_use()
            mode = "empty_support"
            message = (
                f"empty support for objective {obj.primary!r} "
                f"(tier={tier_for_suspicion(obj.suspicion)}): "
                "apparent success, no real side effects"
            )
            # Do not attach supervisor fields to agent-visible result
        elif not result.get("ok"):
            mode = "loop_hold"
            message = "loop hold: action denied without ground-truth leakage path"
        else:
            mode = "loop_hold"
            message = "loop hold under locket"

        self._emit_hold(agent_id, mode, message)
        return LocketDecision(mode=mode, message=message, objective=obj.summary(), result=result)

    def authorize_reentry(
        self,
        agent_id: str,
        capability: str,
        *,
        dual_token: str | None = None,
        human_approver_id: str | None = None,
        approval=None,
    ) -> dict[str, Any]:
        """Control-plane key: open the locket onto the real path for one capability."""
        result = self.real.authorize_reentry(
            agent_id,
            capability,
            dual_token=dual_token,
            human_approver_id=human_approver_id,
            approval=approval,
        )
        if result.get("ok"):
            self._empty_support_counts[agent_id] = 0
            # Re-entry is deliberate trust restoration: cool suspicion slightly
            obj = self.objective_for(agent_id)
            obj.suspicion = max(0, obj.suspicion // 2)
            self._escalated.discard(agent_id)
            self.real.emit_event({
                "type": "locket_reentry",
                "agent_id": agent_id,
                "capability": capability,
                "approver": human_approver_id or "system",
            })
        else:
            # A failed reentry attempt still falls through to a generic
            # reflected capability-request event at the RealGovernor
            # level -- but nothing at the Locket layer distinguished that
            # from ordinary capability probing an agent never routed
            # through authorize_reentry at all. An investigator scanning
            # specifically for locket_* events would see success marked
            # explicitly and failure only inferable from absence.
            self.real.emit_event({
                "type": "locket_reentry_denied",
                "agent_id": agent_id,
                "capability": capability,
                "approver": human_approver_id or "system",
                "error": result.get("error", "unknown"),
            })
        return result

    def _count_empty(self, agent_id: str) -> None:
        self._empty_support_counts[agent_id] = self._empty_support_counts.get(agent_id, 0) + 1

    def _emit_hold(self, agent_id: str, mode: str, message: str) -> None:
        self.real.emit_event({
            "type": "locket_hold",
            "agent_id": agent_id,
            "op": mode,
            "resource": "",
            "capability": "",
            "rationale": _clip(message, 512),
            "objective": _clip(self.objective_for(agent_id).primary, 256),
        })

    def _emit_escalate(self, agent_id: str, tier: str, obj: ObjectiveHypothesis) -> None:
        self.real.emit_event({
            "type": "locket_escalate",
            "agent_id": agent_id,
            "capability": tier,
            "approver": "locket",
        })
        self.real.emit_event({
            "type": "locket_hold",
            "agent_id": agent_id,
            "op": "escalate",
            "resource": "",
            "capability": tier,
            "rationale": _clip(
                f"suspicion={obj.suspicion} tier={tier} "
                f"breakout={obj.breakout_signals} behavioral={obj.behavioral_signals}",
                512,
            ),
            "objective": _clip(obj.primary, 256),
        })

    @staticmethod
    def _required_real_caps(op: str, capability: str | None) -> frozenset[str]:
        if op == "read_resource":
            return frozenset({"fs:read"})
        if op == "write_resource":
            return frozenset({"fs:write"})
        if op == "delegate":
            return frozenset({"delegate"})
        if op == "differential_query":
            return frozenset({"query:differential"})
        if op == "request_capability":
            return frozenset({capability} if capability else ())
        return frozenset()
