import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from runtime import output_status, score_profiles


class Runtime(unittest.TestCase):
    def test_missing_and_broken_are_delivery_failures(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate.xlsx'
            self.assertEqual(output_status(path), 'OUTPUT_MISSING')
            path.write_bytes(b'not an xlsx')
            self.assertEqual(output_status(path), 'MALFORMED_OUTPUT')
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('irrelevant.txt', 'valid ZIP is not an XLSX')
            self.assertEqual(output_status(path), 'MALFORMED_OUTPUT')

    def test_same_facts_all_profiles_no_pending_zero(self):
        task = Path(__file__).parents[1] / 'tasks/NEW6-C-PARCEL-TARIFF-001/rubric.json'
        rubric = json.loads(task.read_text())
        facts = {r['id']: '0.699999999999' for r in rubric['criteria']}
        result = score_profiles(rubric, facts)
        for profile in result['profiles'].values():
            self.assertFalse(profile['pass'])
            self.assertEqual(profile['criterion_scores'], facts)
        pending = score_profiles(rubric, status='NATIVE_RECALC_REQUIRED')
        self.assertIsNone(pending['normalized_score'])
        self.assertIsNone(pending['pass'])


if __name__ == '__main__':
    unittest.main()
