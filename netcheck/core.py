"""Pure functions: no filesystem, network, model, or hardware access.

Nodes are (component, pin) tuples, never ambiguous concatenated identifiers.
The graph describes supplied records, not measured physical connectivity.
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
from collections import deque
from dataclasses import dataclass

MAX_BYTES = 256_000
MAX_PINS = 300
MAX_WIRES = 600
MAX_LABEL = 80
PIN_COLUMNS = ('component', 'pin', 'net')
WIRE_COLUMNS = ('wire_id', 'from_component', 'from_pin', 'to_component', 'to_pin')
Node = tuple[str, str]


class NetCheckError(ValueError):
    """Invalid input or stale state; callers should display the error."""


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def _label(value: object) -> str:
    if not isinstance(value, str):
        raise NetCheckError('Labels must be strings.')
    value = value.strip()
    if not value or len(value) > MAX_LABEL or any(ord(c) < 32 for c in value):
        raise NetCheckError('Labels must contain 1–80 characters without controls.')
    try:
        value.encode('utf-8')
    except UnicodeError as exc:
        raise NetCheckError('Labels must be valid Unicode text.') from exc
    return value


def _rows(text: str, columns: tuple[str, ...], limit: int) -> list[dict]:
    if not isinstance(text, str):
        raise NetCheckError('CSV input must be text.')
    try:
        if len(text.encode('utf-8')) > MAX_BYTES:
            raise NetCheckError('CSV exceeds 256000 bytes.')
    except UnicodeError as exc:
        raise NetCheckError('CSV must be valid Unicode text.') from exc
    try:
        reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff'), newline=''), strict=True)
        if reader.fieldnames != list(columns):
            raise NetCheckError('CSV header must be exactly: ' + ','.join(columns))
        result = []
        for row in reader:
            if len(result) >= limit:
                raise NetCheckError(f'CSV exceeds {limit} records.')
            if None in row or any(v is None for v in row.values()):
                raise NetCheckError(f'CSV line {reader.line_num} has the wrong column count.')
            result.append({k: _label(v) for k, v in row.items()})
        return result
    except csv.Error as exc:
        raise NetCheckError('Malformed CSV.') from exc


@dataclass(frozen=True)
class Snapshot:
    pins: tuple[tuple[str, str, str], ...]
    wires: tuple[tuple[str, str, str, str, str], ...]
    observations_complete: bool
    source_hashes: tuple[str, str]
    revisions: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.observations_complete) is not bool:
            raise NetCheckError('Observation completeness must be explicitly true or false.')
        if not isinstance(self.pins, tuple) or not 1 <= len(self.pins) <= MAX_PINS:
            raise NetCheckError('Expected map must contain 1–300 pins.')
        if not isinstance(self.wires, tuple) or len(self.wires) > MAX_WIRES:
            raise NetCheckError('Observed map must contain at most 600 wires.')
        nodes = set()
        for row in self.pins:
            if not isinstance(row, tuple) or len(row) != 3 or any(_label(x) != x for x in row):
                raise NetCheckError('Invalid expected-pin record.')
            if row[:2] in nodes:
                raise NetCheckError('Each expected pin must occur once.')
            nodes.add(row[:2])
        ids, edges = set(), set()
        for row in self.wires:
            if not isinstance(row, tuple) or len(row) != 5 or any(_label(x) != x for x in row):
                raise NetCheckError('Invalid wire record.')
            wire_id, fc, fp, tc, tp = row
            start, end = (fc, fp), (tc, tp)
            if wire_id in ids:
                raise NetCheckError('Wire IDs must be unique.')
            if start not in nodes or end not in nodes:
                raise NetCheckError('Wire endpoint is absent from expected map.')
            if start == end:
                raise NetCheckError('Self-loop wire is not a connection between two pins.')
            edge = frozenset((start, end))
            if edge in edges:
                raise NetCheckError('Duplicate undirected wire endpoints.')
            ids.add(wire_id)
            edges.add(edge)
        if (not isinstance(self.source_hashes, tuple) or len(self.source_hashes) != 2
                or any(not _is_hash(x) for x in self.source_hashes)):
            raise NetCheckError('Two source SHA-256 values are required.')
        if not isinstance(self.revisions, tuple) or any(not _is_hash(x) for x in self.revisions):
            raise NetCheckError('Invalid revision hashes.')

    @property
    def state_hash(self) -> str:
        return _digest({'pins': self.pins, 'wires': self.wires,
                        'complete': self.observations_complete,
                        'source_hashes': self.source_hashes, 'revisions': self.revisions})


def _is_hash(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def load_connection_tables(expected_csv: str, observed_csv: str, *,
                           observations_complete: bool) -> Snapshot:
    pins = _rows(expected_csv, PIN_COLUMNS, MAX_PINS)
    wires = _rows(observed_csv, WIRE_COLUMNS, MAX_WIRES)
    return Snapshot(
        tuple(tuple(r[k] for k in PIN_COLUMNS) for r in pins),
        tuple(tuple(r[k] for k in WIRE_COLUMNS) for r in wires),
        observations_complete,
        (hashlib.sha256(expected_csv.encode()).hexdigest(),
         hashlib.sha256(observed_csv.encode()).hexdigest()),
    )


def _graph(snapshot: Snapshot):
    graph = {(c, p): [] for c, p, _ in snapshot.pins}
    for wire, fc, fp, tc, tp in snapshot.wires:
        graph[(fc, fp)].append(((tc, tp), wire))
        graph[(tc, tp)].append(((fc, fp), wire))
    for neighbors in graph.values():
        neighbors.sort()
    return graph


def _path(graph: dict, start: Node, end: Node) -> dict:
    queue, prior = deque([start]), {start: None}
    while queue:
        node = queue.popleft()
        if node == end:
            break
        for neighbor, wire in graph[node]:
            if neighbor not in prior:
                prior[neighbor] = (node, wire)
                queue.append(neighbor)
    nodes, wires, node = [end], [], end
    while prior[node] is not None:
        node, wire = prior[node]
        nodes.append(node)
        wires.append(wire)
    return {'pins': list(reversed(nodes)), 'wire_ids': list(reversed(wires))}


def compare_connectivity(snapshot: Snapshot) -> dict:
    graph, groups, membership = _graph(snapshot), [], {}
    expected = {(c, p): net for c, p, net in snapshot.pins}
    for start in sorted(graph):
        if start in membership:
            continue
        group, queue = [], deque([start])
        membership[start] = len(groups)
        while queue:
            node = queue.popleft()
            group.append(node)
            for neighbor, _ in graph[node]:
                if neighbor not in membership:
                    membership[neighbor] = len(groups)
                    queue.append(neighbor)
        groups.append(sorted(group))
    cross_net = []
    for group in groups:
        net_reps = {}
        for pin in group:
            net_reps.setdefault(expected[pin], pin)
        names = sorted(net_reps)
        if len(names) > 1:
            cross_net.append({'expected_nets': names, 'pins': group,
                              'witness_paths': [_path(graph, net_reps[names[0]], net_reps[n])
                                                for n in names[1:]]})
    disconnected = []
    for net in sorted(set(expected.values())):
        parts = {}
        for node in sorted(expected):
            if expected[node] == net:
                parts.setdefault(membership[node], []).append(node)
        if len(parts) > 1:
            disconnected.append({'expected_net': net, 'groups': list(parts.values()),
                                 'status': 'recorded_disconnect' if snapshot.observations_complete
                                 else 'unverified_connection'})
    return {'state_hash': snapshot.state_hash,
            'observations_complete': snapshot.observations_complete,
            'scope': 'Supplied connection records only; not a physical or electrical safety test.',
            'cross_net_connections': cross_net, 'disconnected_expected_nets': disconnected,
            'observed_components': groups,
            'consistent_with_expected_map': not cross_net and not disconnected}


def inspect_pin(snapshot: Snapshot, component: str, pin: str) -> dict:
    node = (_label(component), _label(pin))
    expected = {(c, p): n for c, p, n in snapshot.pins}
    if node not in expected:
        raise NetCheckError('Unknown pin; ask for an existing component and pin ID.')
    return {'pin': node, 'expected_net': expected[node],
            'recorded_neighbors': [{'pin': n, 'wire_id': w} for n, w in _graph(snapshot)[node]],
            'expected_net_members': sorted(n for n, net in expected.items() if net == expected[node]),
            'state_hash': snapshot.state_hash}


@dataclass(frozen=True)
class Proposal:
    base_hash: str
    action: str
    wire: tuple[str, ...]

    @property
    def proposal_hash(self) -> str:
        return _digest((self.base_hash, self.action, self.wire))


def stage_observation(snapshot: Snapshot, *, action: str, wire_id: str,
                      from_component: str = '', from_pin: str = '',
                      to_component: str = '', to_pin: str = '') -> Proposal:
    wire_id = _label(wire_id)
    if action == 'add':
        wire = tuple(_label(v) for v in (wire_id, from_component, from_pin, to_component, to_pin))
        candidate = snapshot.wires + (wire,)
    elif action == 'remove':
        if any((from_component, from_pin, to_component, to_pin)):
            raise NetCheckError('Remove accepts only a wire ID.')
        matches = [w for w in snapshot.wires if w[0] == wire_id]
        if not matches:
            raise NetCheckError('Unknown wire ID.')
        wire = matches[0]
        candidate = tuple(w for w in snapshot.wires if w[0] != wire_id)
    else:
        raise NetCheckError('Action must be add or remove.')
    Snapshot(snapshot.pins, candidate, snapshot.observations_complete, snapshot.source_hashes)
    return Proposal(snapshot.state_hash, action, wire)


def confirm_observation(snapshot: Snapshot, proposal: Proposal, *,
                        confirmed_proposal_hash: str) -> Snapshot:
    """Host-only confirmation step. NEVER expose this as an LLM tool.

    Host must obtain the hash through a separate user's explicit review action.
    A supplied hash is binding, not cryptographic evidence of human identity.
    """
    if not isinstance(proposal, Proposal) or proposal.base_hash != snapshot.state_hash:
        raise NetCheckError('Stale proposal: re-review the current records.')
    if confirmed_proposal_hash != proposal.proposal_hash:
        raise NetCheckError('Confirmation does not match this proposal.')
    if proposal.action == 'add' and len(proposal.wire) == 5:
        staged = stage_observation(snapshot, action='add', **dict(zip(WIRE_COLUMNS, proposal.wire)))
        if staged != proposal:
            raise NetCheckError('Proposal does not match the reviewed record.')
        wires = snapshot.wires + (staged.wire,)
    elif proposal.action == 'remove' and len(proposal.wire) == 5:
        staged = stage_observation(snapshot, action='remove', wire_id=proposal.wire[0])
        if staged != proposal:
            raise NetCheckError('Proposal does not match current wire.')
        wires = tuple(w for w in snapshot.wires if w[0] != proposal.wire[0])
    else:
        raise NetCheckError('Invalid proposal.')
    return Snapshot(snapshot.pins, wires, snapshot.observations_complete,
                    snapshot.source_hashes, snapshot.revisions + (proposal.proposal_hash,))


def render_report(snapshot: Snapshot, *, confirmed_state_hash: str) -> dict[str, str]:
    """Return report bytes as text; caller chooses a new file via explicit export."""
    if confirmed_state_hash != snapshot.state_hash:
        raise NetCheckError('Stale export: re-review the current state.')
    payload = {'schema': 'netcheck-report-v1', 'source_hashes': snapshot.source_hashes,
               'revisions': snapshot.revisions,
               'expected_pin_records': snapshot.pins, 'observed_wire_records': snapshot.wires,
               'analysis': compare_connectivity(snapshot),
               'model_status': 'Deterministic core only; no model execution claimed.'}
    report_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    report_html = ('<!doctype html><html lang="en"><meta charset="utf-8">'
                   '<meta name="viewport" content="width=device-width, initial-scale=1">'
                   '<title>NetCheck connection report</title><body>'
                   '<h1>NetCheck connection report</h1><p>Supplied connection records only. '
                   'This is not a physical or electrical safety test.</p>'
                   '<p>Partial observations cannot establish that an unrecorded wire is absent.</p>'
                   '<pre style="white-space:pre-wrap;overflow-wrap:anywhere">'
                   + html.escape(report_json) + '</pre></body></html>')
    return {'json': report_json, 'html': report_html}
