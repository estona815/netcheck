"""NetCheck's original, deterministic connection-record comparison core."""

from .core import (
    NetCheckError, Snapshot, Proposal, load_connection_tables,
    compare_connectivity, inspect_pin, stage_observation, confirm_observation,
    render_report,
)

__all__ = [
    'NetCheckError', 'Snapshot', 'Proposal', 'load_connection_tables',
    'compare_connectivity', 'inspect_pin', 'stage_observation',
    'confirm_observation', 'render_report',
]
