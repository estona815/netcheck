import json
import itertools
import unittest

from netcheck import (NetCheckError, load_connection_tables, compare_connectivity,
                      inspect_pin, stage_observation, confirm_observation, render_report)

PINS = 'component,pin,net\nJ1,1,SIGNAL\nR1,1,SIGNAL\nR1,2,RETURN\nJ1,2,RETURN\nLED,1,RETURN\n'
HEADER = 'wire_id,from_component,from_pin,to_component,to_pin\n'
WIRES = HEADER + 'w1,J1,1,R1,1\nw2,R1,2,J1,2\n'


def load(wires=WIRES, complete=False, pins=PINS):
    return load_connection_tables(pins, wires, observations_complete=complete)


class CoreTests(unittest.TestCase):
    def test_partial_and_complete_have_different_evidence_claims(self):
        partial = compare_connectivity(load())
        complete = compare_connectivity(load(complete=True))
        self.assertEqual(partial['disconnected_expected_nets'][0]['status'], 'unverified_connection')
        self.assertEqual(complete['disconnected_expected_nets'][0]['status'], 'recorded_disconnect')
        self.assertFalse(partial['consistent_with_expected_map'])

    def test_multi_hop_cross_net_witness_uses_actual_wire_ids(self):
        snapshot = load(WIRES + 'wrong,R1,1,R1,2\n')
        result = compare_connectivity(snapshot)
        issue = result['cross_net_connections'][0]
        self.assertEqual(issue['expected_nets'], ['RETURN', 'SIGNAL'])
        witness = issue['witness_paths'][0]
        self.assertEqual(witness['wire_ids'], ['w2', 'wrong', 'w1'])
        self.assertEqual(witness['pins'], [('J1', '2'), ('R1', '2'), ('R1', '1'), ('J1', '1')])

    def test_confirmed_new_observation_completes_map_without_mutating_source(self):
        before = load()
        proposal = stage_observation(before, action='add', wire_id='w3',
                                     from_component='J1', from_pin='2', to_component='LED', to_pin='1')
        self.assertEqual(len(before.wires), 2)
        after = confirm_observation(before, proposal, confirmed_proposal_hash=proposal.proposal_hash)
        self.assertTrue(compare_connectivity(after)['consistent_with_expected_map'])
        self.assertEqual(after.source_hashes, before.source_hashes)
        self.assertEqual(after.revisions, (proposal.proposal_hash,))
        self.assertNotEqual(after.state_hash, before.state_hash)
        with self.assertRaises(NetCheckError):
            confirm_observation(after, proposal, confirmed_proposal_hash=proposal.proposal_hash)

    def test_confirmed_removal_only_removes_selected_record(self):
        before = load(WIRES + 'wrong,R1,1,R1,2\n')
        proposal = stage_observation(before, action='remove', wire_id='wrong')
        after = confirm_observation(before, proposal, confirmed_proposal_hash=proposal.proposal_hash)
        self.assertEqual(after.wires, load().wires)
        self.assertFalse(compare_connectivity(after)['cross_net_connections'])
        self.assertEqual(len(before.wires), 3)

    def test_confirmation_and_export_are_bound_to_exact_state(self):
        before = load()
        proposal = stage_observation(before, action='remove', wire_id='w1')
        with self.assertRaises(NetCheckError):
            confirm_observation(before, proposal, confirmed_proposal_hash='yes')
        after = confirm_observation(before, proposal, confirmed_proposal_hash=proposal.proposal_hash)
        with self.assertRaises(NetCheckError):
            render_report(after, confirmed_state_hash=before.state_hash)
        report = render_report(after, confirmed_state_hash=after.state_hash)
        self.assertEqual(json.loads(report['json'])['analysis']['state_hash'], after.state_hash)

    def test_inspection_returns_neighbors_without_inventing_unseen_connection(self):
        result = inspect_pin(load(), 'LED', '1')
        self.assertEqual(result['recorded_neighbors'], [])
        self.assertEqual(len(result['expected_net_members']), 3)
        with self.assertRaises(NetCheckError):
            inspect_pin(load(), 'LED', '9')

    def test_csv_shape_and_quote_errors(self):
        for text in [HEADER + 'x,J1,1\n', HEADER + 'x,J1,1,R1,1,extra\n',
                     HEADER + '"unclosed', 'wire_id,wire_id\nx,y\n']:
            with self.subTest(text=text), self.assertRaises(NetCheckError):
                load(text)

    def test_reject_duplicate_pin_and_invalid_wire_graph(self):
        with self.assertRaises(NetCheckError):
            load(pins=PINS + 'J1,1,OTHER\n')
        for row in ['w1,LED,1,R1,2', 'w3,R1,1,J1,1', 'w3,BOGUS,1,J1,1', 'w3,J1,1,J1,1']:
            with self.subTest(row=row), self.assertRaises(NetCheckError):
                load(WIRES + row + '\n')

    def test_bounds_and_boolean_are_strict(self):
        for complete in ['false', 1, None]:
            with self.subTest(complete=complete), self.assertRaises(NetCheckError):
                load(complete=complete)
        with self.assertRaises(NetCheckError):
            load('x' * 256001)
        with self.assertRaises(NetCheckError):
            load(pins='component,pin,net\n' + ''.join(f'C{i},1,N\n' for i in range(301)))
        with self.assertRaises(NetCheckError):
            load(pins='component,pin,net\n')
        with self.assertRaises(NetCheckError):
            load(pins=PINS.replace('SIGNAL', 'x' * 81))

    def test_labels_are_inert_and_html_is_escaped(self):
        hostile = '<script>alert(1)</script>'
        snapshot = load(pins=PINS.replace('SIGNAL', hostile))
        report = render_report(snapshot, confirmed_state_hash=snapshot.state_hash)
        self.assertNotIn('<script>', report['html'])
        self.assertIn('&lt;script&gt;', report['html'])
        self.assertIn(hostile, report['json'])
        self.assertEqual(len(compare_connectivity(snapshot)['observed_components']), 3)

    def test_pin_identity_does_not_depend_on_dot_delimiter(self):
        snapshot = load(HEADER, pins='component,pin,net\nA.B,1,N\nA,B.1,M\n')
        self.assertEqual(len(compare_connectivity(snapshot)['observed_components']), 2)

    def test_source_hashes_capture_exact_inputs_and_results_repeat(self):
        first = load()
        other = load(WIRES.replace('\n', '\r\n'))
        self.assertEqual(first.wires, other.wires)
        self.assertNotEqual(first.source_hashes, other.source_hashes)
        self.assertEqual(compare_connectivity(first), compare_connectivity(load()))
        self.assertEqual(render_report(first, confirmed_state_hash=first.state_hash),
                         render_report(first, confirmed_state_hash=first.state_hash))

    def test_empty_observations_are_valid_but_unknown(self):
        analysis = compare_connectivity(load(HEADER))
        self.assertEqual(len(analysis['disconnected_expected_nets']), 2)
        self.assertTrue(all(x['status'] == 'unverified_connection'
                            for x in analysis['disconnected_expected_nets']))

    def test_unicode_and_quoted_commas_survive(self):
        snapshot = load(HEADER, pins='component,pin,net\n"저항,왼쪽",01,신호\n')
        self.assertEqual(inspect_pin(snapshot, '저항,왼쪽', '01')['expected_net'], '신호')

    def test_exhaustive_four_pin_graphs_against_independent_transitive_closure(self):
        pins = 'component,pin,net\nP,0,A\nP,1,A\nP,2,B\nP,3,B\n'
        pairs = list(itertools.combinations(range(4), 2))
        for mask in range(64):
            edges = [p for i, p in enumerate(pairs) if mask & (1 << i)]
            wires = HEADER + ''.join(f'w{i},P,{a},P,{b}\n' for i, (a, b) in enumerate(edges))
            result = compare_connectivity(load(wires, True, pins))
            reach = [[a == b or (min(a,b), max(a,b)) in edges for b in range(4)] for a in range(4)]
            for k in range(4):
                for i in range(4):
                    for j in range(4):
                        reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
            with self.subTest(mask=mask):
                self.assertEqual(bool(result['cross_net_connections']), any(reach[a][b] for a in [0,1] for b in [2,3]))
                self.assertEqual(len(result['disconnected_expected_nets']), int(not reach[0][1]) + int(not reach[2][3]))
                edge_map = {f'w{i}': frozenset((('P',str(a)),('P',str(b)))) for i,(a,b) in enumerate(edges)}
                for issue in result['cross_net_connections']:
                    for path in issue['witness_paths']:
                        for a,b,wire in zip(path['pins'],path['pins'][1:],path['wire_ids']):
                            self.assertEqual(edge_map[wire], frozenset((a,b)))


if __name__ == '__main__':
    unittest.main()
