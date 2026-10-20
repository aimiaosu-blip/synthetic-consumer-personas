"""Portable static HTML/SVG report; no network dependencies."""
import html
import json


def write_report(directory, metrics, metadata):
    status = html.escape(metadata['status'])
    bars = []
    for i, (concept, values) in enumerate(metrics['concept_means'].items()):
        x = 135 + i*210
        for offset, key, color in [(0,'reference','#526378'),(52,'prediction','#168575')]:
            height = values[key]*46
            bars.append(f'<rect x="{x+offset}" y="{280-height}" width="40" height="{height}" fill="{color}"/><text x="{x+offset+20}" y="{272-height}" text-anchor="middle">{values[key]:.2f}</text>')
        bars.append(f'<text x="{x+46}" y="305" text-anchor="middle">{html.escape(concept)}</text>')
    ticks = ''.join(f'<text x="65" y="{285-i*46}">{i}</text><line x1="85" x2="760" y1="{280-i*46}" y2="{280-i*46}" stroke="#ddd"/>' for i in range(6))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 380" role="img" aria-label="Mean purchase intent by concept"><rect width="800" height="380" fill="white"/><g font-family="sans-serif" font-size="14" fill="#213142"><text x="85" y="25">Mean purchase intent (1–5); reference vs simulated prediction</text>{ticks}{"".join(bars)}<text x="350" y="335">Product concept</text><text x="85" y="365">Reference: gray | Simulation: green · {html.escape(metadata["source_type"])}</text></g></svg>'
    (directory/'concept_means.svg').write_text(svg, encoding='utf-8')
    cells = ''.join(f'<tr><td>{html.escape(c["persona_id"])}</td><td>{html.escape(c["concept_id"])}</td><td>{c["n"]}</td><td>{c["reference_mean"]:.2f}</td><td>{c["prediction_mean"]:.2f}</td><td>{c["signed_bias"]:+.2f}</td></tr>' for c in metrics['cells'])
    detail = html.escape(json.dumps({k:v for k,v in metrics.items() if k not in ('cells','concept_means')}, indent=2))
    text = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic Consumer Personas — Validation Report</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;color:#213142;max-width:1000px;margin:40px auto;padding:0 24px;background:#fafbf9}}h1{{line-height:1.15;font-size:38px}}.label{{background:#fff0ce;padding:16px;border-left:4px solid #976b12}}svg{{width:100%;height:auto}}table{{border-collapse:collapse;width:100%;background:white}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #ddd}}pre{{overflow:auto;background:#edf2f0;padding:20px}}.table{{overflow:auto}}footer{{margin-top:32px;color:#526378}}</style>
<p>RESEARCH PROTOTYPE · v0.1.0</p><h1>Synthetic Consumer Personas</h1><p>LLM Validation for Consumer Insights</p><p class="label">{status}</p>
<p>{metrics['n_respondents']} reference respondents · {metrics['n_reference_pairs']} respondent/concept pairs · {metrics['runs']} simulation runs per pair. Provider: {html.escape(metadata['provider'])}.</p>
<h2>Concept comparison</h2>{svg}<p>Means average repeated predictions within each reference pair first. Equal weighting of observed pairs; no population weighting.</p>
<h2>Where the simulator differs</h2><div class="table"><table><thead><tr><th>Persona</th><th>Concept</th><th>n pairs</th><th>Reference</th><th>Prediction</th><th>Signed bias</th></tr></thead><tbody>{cells}</tbody></table></div>
<h2>Error, agreement and stability</h2><pre>{detail}</pre>
<p>MAE/RMSE and bias use the mean prediction per pair. Exact/within-one agreement compare individual draws with the reference. Stability is sample SD within a pair and pairwise exact agreement across runs; unavailable for one run. Spearman uses concept means, with average ranks for ties; undefined for constant ranks. CI is a 500-resample respondent-cluster percentile bootstrap.</p>
<h2>Interpretation boundary</h2><p>Synthetic benchmarks test the pipeline only. Shared assumptions between generators can inflate agreement. A real-public label reflects the supplied provenance declaration, not independent verification. Scores are ordinal; numeric distances assume equal spacing. Three concepts give very limited ranking evidence. Small cells are descriptive, and no score demonstrates that AI can replace consumers.</p>
<p>Feedback text is exported for qualitative review. Automated semantic validity and demographic fairness have not been established. No company data or real research findings are included in the shipped demonstration.</p><footer>Prepared as an independent application portfolio prototype for the Essity thesis topic. No affiliation or endorsement implied.</footer></html>'''
    (directory/'report.html').write_text(text, encoding='utf-8')
