import argparse
import json
import os
from pathlib import Path
from .data import load_reference, write_csv, sha256
from .design import PERSONAS, CONCEPTS, PROMPT_VERSION
from .providers import rng_for, demo_response, llm_response, make_prompt
from .metrics import summarize
from .report import write_report


def generate_demo(directory, seed=42):
    rows = []
    for persona in PERSONAS:
        for i in range(20):
            respondent = f"synthetic-{persona}-{i:03}"
            individual = rng_for(seed, respondent, 'reference').gauss(0, .5)
            for concept, c in CONCEPTS.items():
                rng = rng_for(seed, respondent, concept, 'reference')
                utility = sum(w*f for w,f in zip(PERSONAS[persona]['weights'], c['features']))
                rating = min(5, max(1, round(1+4*utility+individual+rng.gauss(0,.8))))
                rows.append(dict(respondent_id=respondent, persona_id=persona, concept_id=concept,
                                 rating=rating, feedback='SYNTHETIC reference response; not a human quotation.', source_type='synthetic_demo'))
    directory.mkdir(parents=True, exist_ok=True)
    write_csv(directory/'reference.csv', rows)
    (directory/'manifest.json').write_text(json.dumps({'source_type':'synthetic_demo', 'seed':seed,
        'description':'Fictional rule-generated benchmark; shares utility assumptions with simulator. Not independent validation.'}, indent=2))
    return directory/'reference.csv', directory/'manifest.json'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Synthetic Consumer Personas: explicit demonstration and held-out validation')
    parser.add_argument('command', choices=['demo','validate'])
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--out', type=Path, default=Path('runs/latest'))
    parser.add_argument('--provider', choices=['demo','openai'], default='demo')
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max-calls', type=int, default=30, help='Hard cap for paid API calls')
    args = parser.parse_args(argv)
    try:
        if args.runs < 1:
            raise ValueError('--runs must be positive')
        if args.out.exists() and any(args.out.iterdir()):
            raise ValueError('Output directory is not empty; choose a fresh --out to preserve prior work')
        if args.command == 'validate' and (not args.reference or not args.manifest):
            raise ValueError('validate requires --reference and --manifest')
        if args.command == 'demo' and (args.reference or args.manifest):
            raise ValueError('Use validate for supplied data')
        if args.command == 'demo' and args.provider != 'demo':
            raise ValueError('demo is offline; use validate --provider openai for explicit paid runs')
        args.out.mkdir(parents=True, exist_ok=True)
        if args.command == 'demo':
            args.reference, args.manifest = generate_demo(args.out/'inputs', args.seed)
        reference, manifest = load_reference(args.reference, args.manifest)
        calls = len(reference)*args.runs
        if args.provider == 'openai' and calls > args.max_calls:
            raise ValueError(f'{calls} API calls exceed --max-calls {args.max_calls}; explicitly raise the cap if intended')
        predictions = []
        for row in reference:
            for run in range(args.runs):
                if args.provider == 'demo':
                    response = demo_response(row['persona_id'], row['concept_id'], row['respondent_id'], args.seed, run)
                else:
                    response = llm_response(row['persona_id'], row['concept_id'])
                predictions.append({**{k: row[k] for k in ['respondent_id','persona_id','concept_id']},
                    'run': run, **response, 'provider':args.provider})
        metrics = summarize(reference, predictions, args.seed)
        status = ('SYNTHETIC DEMONSTRATION — NO REAL CONSUMER VALIDATION' if manifest['source_type']=='synthetic_demo'
                  else 'REAL PUBLIC REFERENCE — '+('LLM COMPARISON' if args.provider=='openai' else 'RULE-BASED BASELINE; NOT LLM VALIDATION'))
        metadata = {'status':status, 'source_type':manifest['source_type'], 'provider':args.provider,
            'model': os.environ.get('OPENAI_MODEL') if args.provider=='openai' else 'rule-v1',
            'seed':args.seed, 'prompt_version':PROMPT_VERSION, 'reference_sha256':sha256(args.reference),
            'manifest_sha256':sha256(args.manifest), 'manifest':manifest,
            'design':{'personas':PERSONAS,'concepts':CONCEPTS},
            'prompts':{f'{p}/{c}':make_prompt(p,c) for p in PERSONAS for c in CONCEPTS},
            'note':'API sampling is not seeded; seed controls offline simulation/bootstrap only.'}
        (args.out/'metrics.json').write_text(json.dumps(metrics, indent=2, allow_nan=False), encoding='utf-8')
        (args.out/'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        (args.out/'predictions.json').write_text(json.dumps(predictions, indent=2), encoding='utf-8')
        write_report(args.out, metrics, metadata)
        print(status)
        print(f"Saved {len(reference)} reference pairs and {len(predictions)} predictions to {args.out}")
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(2, f'Error: {exc}\n')

if __name__ == '__main__':
    main()
