"""Descriptive validation; repetitions are not independent human observations."""
import math
import random
import statistics as st
from collections import defaultdict
from itertools import combinations

def rank_correlation(a, b):
    def ranks(values):
        return [1 + sum(x < v for x in values) + (sum(x == v for x in values) - 1) / 2 for v in values]
    x, y = ranks(a), ranks(b)
    mx, my = st.mean(x), st.mean(y)
    denominator = math.sqrt(sum((v-mx)**2 for v in x) * sum((v-my)**2 for v in y))
    return sum((u-mx)*(v-my) for u,v in zip(x,y)) / denominator if denominator else None

def summarize(reference, predictions, seed=42):
    expected = {(r['respondent_id'], r['concept_id']): r for r in reference}
    if not expected or len(expected) != len(reference):
        raise ValueError("Nonempty unique reference pairs required")
    by_pair, seen = defaultdict(list), set()
    for p in predictions:
        key = (p['respondent_id'], p['concept_id'])
        unique = key + (p['run'],)
        if key not in expected or unique in seen or p['persona_id'] != expected[key]['persona_id']:
            raise ValueError("Unmatched, duplicate, or inconsistent prediction")
        if type(p['rating']) is not int or not 1 <= p['rating'] <= 5:
            raise ValueError("Prediction rating out of range")
        seen.add(unique)
        by_pair[key].append(p)
    if set(by_pair) != set(expected):
        raise ValueError("Missing predictions")
    run_sets = {tuple(sorted(p['run'] for p in rows)) for rows in by_pair.values()}
    if len(run_sets) != 1:
        raise ValueError("Every reference pair must have the same runs")
    errors, clusters, cells, concepts = [], defaultdict(list), defaultdict(list), defaultdict(list)
    exact, within, variability, agreement = [], [], [], []
    for key, rows in by_pair.items():
        ref = expected[key]
        ratings = [p['rating'] for p in rows]
        mean_prediction = st.mean(ratings)
        error = mean_prediction - ref['rating']
        errors.append(error)
        clusters[ref['respondent_id']].append(abs(error))
        cells[(ref['persona_id'], ref['concept_id'])].append((ref['rating'], mean_prediction))
        concepts[ref['concept_id']].append((ref['rating'], mean_prediction))
        exact.append(st.mean(v == ref['rating'] for v in ratings))
        within.append(st.mean(abs(v-ref['rating']) <= 1 for v in ratings))
        if len(ratings) > 1:
            variability.append(st.stdev(ratings))
            agreement.append(st.mean(a == b for a,b in combinations(ratings, 2)))
    # Respondent-cluster bootstrap preserves repeated concept observations.
    cluster_values = list(clusters.values())
    rng = random.Random(seed)
    bootstrap = []
    if len(cluster_values) >= 2:
        for _ in range(500):
            sampled = [v for group in rng.choices(cluster_values, k=len(cluster_values)) for v in group]
            bootstrap.append(st.mean(sampled))
        bootstrap.sort()
    cell_results = []
    for (persona, concept), values in sorted(cells.items()):
        human, predicted = [x[0] for x in values], [x[1] for x in values]
        cell_results.append(dict(persona_id=persona, concept_id=concept, n=len(values), reference_mean=st.mean(human),
                                 prediction_mean=st.mean(predicted), signed_bias=st.mean(predicted)-st.mean(human)))
    cm = {k: dict(reference=st.mean(v[0] for v in values), prediction=st.mean(v[1] for v in values)) for k,values in sorted(concepts.items())}
    return {"n_respondents": len(clusters), "n_reference_pairs": len(reference), "n_predictions": len(predictions),
            "runs": len(next(iter(run_sets))), "mae_mean_prediction": st.mean(abs(e) for e in errors),
            "rmse_mean_prediction": math.sqrt(st.mean(e*e for e in errors)), "signed_bias": st.mean(errors),
            "exact_agreement_single_draw": st.mean(exact), "within_one_single_draw": st.mean(within),
            "mean_within_pair_sd": st.mean(variability) if variability else None,
            "repeat_exact_agreement": st.mean(agreement) if agreement else None,
            "mae_cluster_bootstrap_95_ci": [bootstrap[12], bootstrap[487]] if bootstrap else None,
            "concept_spearman": rank_correlation([v['reference'] for v in cm.values()], [v['prediction'] for v in cm.values()]),
            "max_absolute_cell_bias": max(abs(c['signed_bias']) for c in cell_results), "cells": cell_results, "concept_means": cm}
