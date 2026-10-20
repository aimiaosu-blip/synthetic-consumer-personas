import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from personas.__main__ import generate_demo, main
from personas.data import load_reference, write_csv, sha256
from personas.metrics import summarize, rank_correlation
from personas.providers import demo_response, llm_response, make_prompt, validate_response


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.csv, self.manifest = generate_demo(self.root/'inputs')
        self.rows, self.meta = load_reference(self.csv, self.manifest)

    def test_demo_shape_and_reproducibility(self):
        self.assertEqual(len(self.rows), 240)
        self.assertEqual(len({r['respondent_id'] for r in self.rows}), 80)
        a, _ = generate_demo(self.root/'second')
        self.assertEqual(a.read_bytes(), self.csv.read_bytes())
        a = demo_response('value','refill','test',42,0)
        self.assertEqual(a, demo_response('value','refill','test',42,0))

    def test_shipped_provenance_hashes(self):
        example = Path(__file__).resolve().parents[1] / "examples/demo"
        meta = json.loads((example / "metadata.json").read_text())
        self.assertEqual(meta["reference_sha256"], sha256(example / "inputs/reference.csv"))
        self.assertEqual(meta["manifest_sha256"], sha256(example / "inputs/manifest.json"))

    def test_rating_boundaries(self):
        for rating in ['nan','inf',0,6,2.5]:
            rows = copy.deepcopy(self.rows)
            rows[0]['rating'] = rating
            write_csv(self.csv,rows)
            with self.assertRaises(ValueError): load_reference(self.csv,self.manifest)

    def test_duplicates_rejected(self):
        write_csv(self.csv,self.rows+[self.rows[0]])
        with self.assertRaises(ValueError): load_reference(self.csv,self.manifest)

    def test_mixed_provenance_rejected(self):
        self.rows[0]['source_type']='real_public'
        write_csv(self.csv,self.rows)
        with self.assertRaises(ValueError): load_reference(self.csv,self.manifest)

    def test_real_manifest_required(self):
        self.manifest.write_text('{"source_type":"real_public"}')
        with self.assertRaises(ValueError): load_reference(self.csv,self.manifest)

    def test_real_import_contract(self):
        # Fabricated fixture exercises the contract; not a real research dataset.
        for r in self.rows: r['source_type']='real_public'
        write_csv(self.csv,self.rows)
        meta = {k:'TEST FIXTURE ONLY' for k in ['license','collected_at','population','question','persona_mapping','concept_mapping']}
        meta.update(source_type='real_public',source_url='https://example.org/fixture',deidentified=True,holdout=True)
        self.manifest.write_text(json.dumps(meta))
        rows, _ = load_reference(self.csv,self.manifest)
        self.assertEqual(len(rows),240)

    def test_known_metrics(self):
        refs = [dict(respondent_id='a',persona_id='value',concept_id='essential',rating=1),
                dict(respondent_id='b',persona_id='value',concept_id='refill',rating=5)]
        preds = [{**r,'rating':v,'run':run} for r,v in zip(refs,[2,3]) for run in [0,1]]
        m = summarize(refs,preds)
        self.assertEqual(m['mae_mean_prediction'],1.5)
        self.assertAlmostEqual(m['rmse_mean_prediction'],(2.5)**.5)
        self.assertEqual(m['signed_bias'],-.5)
        self.assertEqual(m['within_one_single_draw'],.5)
        self.assertEqual(m['mean_within_pair_sd'],0)
        self.assertEqual(m['repeat_exact_agreement'],1)
        self.assertEqual(m['concept_spearman'],1)

    def test_missing_and_duplicate_predictions(self):
        refs = self.rows[:2]
        preds = [{**r,'run':0} for r in refs]
        for bad in [preds[:1],preds+[preds[0]]]:
            with self.assertRaises(ValueError): summarize(refs,bad)

    def test_single_run_stability_undefined(self):
        m = summarize(self.rows,[{**r,'run':0} for r in self.rows])
        self.assertIsNone(m['mean_within_pair_sd'])
        self.assertIsNone(m['repeat_exact_agreement'])
        self.assertEqual(m['mae_mean_prediction'],0)

    def test_ties_and_constant_rank(self):
        self.assertIsNone(rank_correlation([1,1],[2,3]))
        self.assertAlmostEqual(rank_correlation([1,2,2],[3,1,1]),-1)

    def test_prompt_has_no_answers_or_ids(self):
        prompt = json.dumps(make_prompt('value','refill'))
        for word in ['respondent_id','rating','feedback','weights','features']:
            self.assertNotIn(word,prompt)

    def test_invalid_llm_outputs(self):
        for v in [{'rating':True,'feedback':'x'},{'rating':6,'feedback':'x'},{'rating':2,'feedback':''},[]]:
            with self.assertRaises(ValueError): validate_response(v)

    @patch.dict(os.environ,{'OPENAI_API_KEY':'test-placeholder','OPENAI_MODEL':'test-model'})
    def test_mock_api_and_no_reference_leakage(self):
        response = io.BytesIO(json.dumps({'model':'test-model','id':'test-id','choices':[{'finish_reason':'stop','message':{'content':'{"rating": 3, "feedback": "Benefit and concern"}'}}]}).encode())
        with patch('urllib.request.urlopen',return_value=response) as mock:
            result = llm_response('value','refill')
        self.assertEqual(result['rating'],3)
        body = json.loads(mock.call_args.args[0].data)
        self.assertFalse(body['store'])
        self.assertNotIn('respondent_id',body['messages'][1]['content'])

    @patch.dict(os.environ,{},clear=True)
    def test_missing_key_fails(self):
        with self.assertRaises(ValueError): llm_response('value','refill')

    def test_end_to_end_and_no_overwrite(self):
        out = self.root/'run'
        main(['demo','--out',str(out)])
        m = json.loads((out/'metrics.json').read_text())
        self.assertEqual(m['n_predictions'],720)
        self.assertIn('NO REAL CONSUMER VALIDATION',(out/'report.html').read_text())
        with self.assertRaises(SystemExit): main(['demo','--out',str(out)])

    def test_paid_call_cap(self):
        with patch('personas.__main__.llm_response') as api:
            with self.assertRaises(SystemExit):
                main(['validate','--reference',str(self.csv),'--manifest',str(self.manifest),'--provider','openai','--out',str(self.root/'paid')])
            api.assert_not_called()

if __name__ == '__main__': unittest.main()
