"""Host review regressions. No SDK/model imports or calls.

Generated reports stay in project _tmp for review; no automatic deletion.
"""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from netcheck import core
from netcheck.agent_cli import ToolSession, review_on_terminal

EXPECTED = 'component,pin,net\nA,1,N\nB,1,N\nC,1,N\n'
OBSERVED = 'wire_id,from_component,from_pin,to_component,to_pin\n'


class HostReviewTests(unittest.TestCase):
    def test_stale_second_proposal_is_skipped_and_first_change_exports(self):
        session = ToolSession(EXPECTED, OBSERVED)
        session.load()
        original = session.snapshot
        first = session.stage(action='add', wire_id='w1', from_component='A',
                              from_pin='1', to_component='B', to_pin='1')
        second = session.stage(action='add', wire_id='w2', from_component='B',
                               from_pin='1', to_component='C', to_pin='1')
        reviewed = core.confirm_observation(original, session.proposals[first['proposal_hash']],
                                            confirmed_proposal_hash=first['proposal_hash'])
        temp_root = Path(__file__).resolve().parents[1] / '_tmp'
        temp_root.mkdir(exist_ok=True)
        retained = Path(tempfile.mkdtemp(prefix='host-review-', dir=temp_root))
        expected_file, observed_file = retained / 'expected.csv', retained / 'observed.csv'
        expected_file.write_text(EXPECTED)
        observed_file.write_text(OBSERVED)
        destination = retained / 'report'
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch('sys.stdin.isatty', return_value=True), \
                patch('builtins.input', side_effect=[first['proposal_hash'], reviewed.state_hash]) as answer, \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            review_on_terminal(session, destination)
        self.assertEqual(answer.call_count, 2, 'stale proposal must not prompt or auto-confirm')
        events = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual([e['event'] for e in events], [
            'human_confirmed_record_change', 'stale_proposal_skipped',
            'export_preview', 'human_confirmed_export'])
        self.assertEqual(events[1]['proposal_hash'], second['proposal_hash'])
        self.assertEqual(session.snapshot, reviewed)
        self.assertEqual(len(original.wires), 0)
        self.assertEqual(expected_file.read_text(), EXPECTED)
        self.assertEqual(observed_file.read_text(), OBSERVED)
        report = json.loads((destination / 'netcheck-report.json').read_text())
        self.assertEqual(report['analysis']['state_hash'], reviewed.state_hash)
        self.assertEqual(report['observed_wire_records'], [['w1', 'A', '1', 'B', '1']])
        self.assertIn('<!doctype html>', (destination / 'netcheck-report.html').read_text())

    def test_declining_first_does_not_make_second_stale(self):
        session = ToolSession(EXPECTED, OBSERVED)
        session.load()
        session.stage(action='add', wire_id='w1', from_component='A', from_pin='1',
                      to_component='B', to_pin='1')
        second = session.stage(action='add', wire_id='w2', from_component='B', from_pin='1',
                               to_component='C', to_pin='1')
        output = io.StringIO()
        with patch('sys.stdin.isatty', return_value=True), \
                patch('builtins.input', side_effect=['', second['proposal_hash']]) as answer, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            review_on_terminal(session, None)
        self.assertEqual(answer.call_count, 2)
        self.assertEqual([w[0] for w in session.snapshot.wires], ['w2'])
        self.assertNotIn('stale_proposal_skipped', output.getvalue())


if __name__ == '__main__':
    unittest.main()
