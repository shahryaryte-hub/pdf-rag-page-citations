"""Offline checks. Run with python -m unittest from the example folder."""
import unittest
from unittest.mock import patch

import example


class CitationExampleTest(unittest.TestCase):
    def test_preview_keeps_the_matching_passage_and_its_original_link(self):
        sentence, page, url = example.find_answer(example.PREVIEW)
        self.assertEqual((sentence, page, url), (
            example.PREVIEW[1]["text"], 6, example.PDF + "#page=6",
        ))

    def test_missing_or_incomplete_evidence_has_no_answer(self):
        partial = dict(example.PREVIEW[1], text="The core concepts in responsible AI")
        for rows in ([], example.PREVIEW[:1], [partial]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                example.find_answer(rows)

    def test_rejects_a_link_to_a_different_page(self):
        with self.assertRaises(ValueError):
            example.find_answer([dict(example.PREVIEW[1], pageNumber=7)])

    def test_live_mode_starts_one_bounded_run_and_reads_its_dataset(self):
        responses = [
            {"data": {"id": "sampleRun", "status": "READY"}},
            {"data": {"status": "SUCCEEDED", "defaultDatasetId": "sampleDataset"}},
            example.PREVIEW,
        ]
        with patch.dict(example.os.environ, {"APIFY_TOKEN": "test-only"}), \
                patch.object(example.time, "sleep"), \
                patch.object(example, "request_json", side_effect=responses) as api, \
                patch("sys.stderr"):
            self.assertEqual(example.live_rows(), example.PREVIEW)
        start, poll, dataset = [call.args for call in api.call_args_list]
        self.assertIn("maxTotalChargeUsd=0.02", start[2])
        self.assertEqual(start[3], {"pdfUrl": example.PDF, "startPage": 6, "maxPages": 2, "maxSpendUsd": 0.02})
        self.assertEqual(poll[2:], ("/actor-runs/sampleRun",))
        self.assertEqual(dataset[2:], ("/datasets/sampleDataset/items?clean=true&limit=100",))


if __name__ == "__main__":
    unittest.main()
