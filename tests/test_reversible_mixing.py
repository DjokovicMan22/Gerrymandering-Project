"""Synthetic fail-closed cohort checks for reproducible reversible Michigan MH runs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"/"research_audit"))
from analyze_reversible_mixing import validate_mh_cohort


def make_four(tmp_path,states=121):
    base={"step":0,"dem_seats":7,"efficiency_gap":.00333,
          "mean_median":-.014,"cut_edges":681,"max_population_deviation":.004}
    chains,metas,refs=[],[],[]
    for i,seed in enumerate((101,202,303,404)):
        stem=f"mi_2020_reversible_closer_warm{seed}_sample{seed+7000}_{states}states"
        csv=tmp_path/(stem+"_plan_metrics.csv")
        meta=tmp_path/(stem+"_metadata.json")
        reference=tmp_path/(stem+"_reference.json")
        steps=np.arange(states)
        attempted=steps.copy()
        accepted=steps//5
        poprej=attempted-accepted
        frame=pd.DataFrame({
            "step":steps,
            "mh_attempted_total":attempted,
            "mh_accepted_total":accepted,
            "mh_population_rejected_total":poprej,
            "mh_contiguity_rejected_total":0,
            "mh_geography_rejected_total":0,
            "mh_ratio_rejected_total":0,
            "state_changed_since_previous": np.r_[0,np.diff(accepted)],
            "dem_seats":7,
            "efficiency_gap":.0033,
            "mean_median":-.014,
            "cut_edges":700,
            "split_counties":17,
            "split_county_mcd":19,
            "max_population_deviation":.0045,
        })
        frame.to_csv(csv,index=False)
        m={
            "kernel":"boundary_uniform_choice_local_flip_swap_mh_v1",
            "warmed_step0_is_reference":False,
            "states":states,
            "config":{"epsilon":.005,"flip_probability":.5,
                      "max_cut_edges":760,"max_split_counties":18,"max_split_county_mcd":20},
            "warm_start_sha256":str(i+1)*64,
            "warm_seed":seed,
            "sample_seed":seed+7000,
            "source_sha256":"a"*64,
            "source_blob_sha1":"a4dfe70818f87b97924781216f3d86a672cfc66a",
            "reference_election_scores":base,
            "final_from_warm":{"fraction_different":.01},
        }
        meta.write_text(json.dumps(m))
        reference.write_text(json.dumps(base))
        chains.append(csv); metas.append(meta); refs.append(reference)
    return chains,metas,refs


def test_valid_cohort_returns_separately_scored_enacted_reference(tmp_path):
    scores,metas,refs=make_four(tmp_path)
    baseline,rows=validate_mh_cohort(scores,metas,refs,condition="closer",
                                    expected_states=121)
    assert baseline["dem_seats"]==7
    assert len(rows)==4
    assert all(row["accepted_transitions"]==24 for row in rows)
    assert all(row["acceptance_rate"]==pytest.approx(.2) for row in rows)


def test_duplicate_warm_map_rejected(tmp_path):
    scores,metas,refs=make_four(tmp_path)
    a=json.loads(metas[0].read_text())
    b=json.loads(metas[1].read_text())
    b["warm_start_sha256"]=a["warm_start_sha256"]
    metas[1].write_text(json.dumps(b))
    with pytest.raises(ValueError,match="four distinct seeded warm maps"):
        validate_mh_cohort(scores,metas,refs,condition="closer",expected_states=121)


def test_mismatched_reference_rejected(tmp_path):
    scores,metas,refs=make_four(tmp_path)
    a=json.loads(refs[0].read_text())
    a["dem_seats"]=8
    refs[0].write_text(json.dumps(a))
    with pytest.raises(ValueError,match="enacted reference mismatch"):
        validate_mh_cohort(scores,metas,refs,condition="closer",expected_states=121)


def test_missing_attempt_detected(tmp_path):
    scores,metas,refs=make_four(tmp_path)
    df=pd.read_csv(scores[0]);df.loc[21,"mh_attempted_total"]=22;df.to_csv(scores[0],index=False)
    with pytest.raises(ValueError,match="missing proposals"):
        validate_mh_cohort(scores,metas,refs,condition="closer",expected_states=121)


def test_corrupted_geographic_observation_rejected(tmp_path):
    scores,metas,refs=make_four(tmp_path)
    df=pd.read_csv(scores[0]);df.loc[10,"cut_edges"]=900;df.to_csv(scores[0],index=False)
    with pytest.raises(ValueError,match="geographic proxy cap"):
        validate_mh_cohort(scores,metas,refs,condition="closer",expected_states=121)


def test_wrong_kernel_rejected(tmp_path):
    scores,metas,refs=make_four(tmp_path)
    m=json.loads(metas[0].read_text());m["kernel"]="recom";metas[0].write_text(json.dumps(m))
    with pytest.raises(ValueError,match="stationary-law"):
        validate_mh_cohort(scores,metas,refs,condition="closer",expected_states=121)


def test_missing_observation_rejected(tmp_path):
    scores,metas,refs=make_four(tmp_path)
    df=pd.read_csv(scores[0]).drop(index=17);df.to_csv(scores[0],index=False)
    with pytest.raises(ValueError,match="missing/duplicate sampled"):
        validate_mh_cohort(scores,metas,refs,condition="closer",expected_states=121)
