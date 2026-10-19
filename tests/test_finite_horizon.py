"""Fail-closed independent-endpoint identity, cohort and numerical interval tests."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"/"research_audit"))
from analyze_finite_horizon import wilson,require_complete,summarize


def cohort(tmp_path,condition="closer"):
    files=[]
    edges,counties,mcd=(760,18,20) if condition=="closer" else (850,24,49)
    for first in (10001,10009,10017,10025):
        rows=[]
        for seed in range(first,first+8):
            rows.append({
                "condition":condition,"rng_seed":seed,
                "steps_including_enacted_reference":801,
                "model_graph_sha256":"a"*64,
                "reference_assignment_sha256":"b"*64,
                "endpoint_sha256":f"{seed:064x}",
                "reference_efficiency_gap":.0033,
                "reference_dem_seats":7,
                "reference_cut_edges":682,
                "independently_rescored_endpoint":True,
                "legal_and_stationary_map_distribution_certified":False,
                "endpoint_max_population_deviation":.0045,
                "geographic_attempts":810,
                "extra_proposal_calls_beyond_recorded_transitions":10,
                "geographic_rejections":300,
                "endpoint_dem_seats":6+seed%3,
                "endpoint_efficiency_gap":-.03+.001*(seed%20),
                "endpoint_cut_edges":edges-5,
                "endpoint_split_counties":counties-1,
                "endpoint_split_county_mcd":mcd-1,
                "endpoint_fraction_precincts_different_from_reference":.13,
            })
        file=tmp_path/f"finite_horizon_{condition}_{first}.csv"
        pd.DataFrame(rows).to_csv(file,index=False)
        files.append(file)
    return files


def test_full_independent_endpoint_cohort(tmp_path):
    files=cohort(tmp_path)
    df=require_complete(files,"closer")
    assert len(df)==32
    assert df.rng_seed.min()==10001
    assert df.rng_seed.max()==10032
    x=summarize(df,"closer")
    assert x["independent_seeded_endpoint_count"]==32
    assert x["model_graph_sha256"]=="a"*64
    assert len(x["metric_summaries"]["endpoint_dem_seats"]["bootstrap_95pct_ci_for_finite_horizon_mean"])==2


def test_wilson_interval_edge_cases():
    assert wilson(0,32)[0]==0
    assert wilson(32,32)[1]==1
    a,b=wilson(16,32)
    assert a<.5<b


def test_one_missing_seed_rejected(tmp_path):
    files=cohort(tmp_path)
    df=pd.read_csv(files[0])
    df.loc[0,"rng_seed"]=10009
    df.to_csv(files[0],index=False)
    with pytest.raises(ValueError,match="Missing/duplicated"):
        require_complete(files,"closer")


def test_graph_provenance_mismatch_rejected(tmp_path):
    files=cohort(tmp_path)
    df=pd.read_csv(files[0],dtype={"model_graph_sha256":"string"})
    df.loc[0,"model_graph_sha256"]="f"*64
    df.to_csv(files[0],index=False)
    with pytest.raises(ValueError,match="Inconsistent common graph"):
        require_complete(files,"closer")


def test_unverified_or_bad_population_rejected(tmp_path):
    files=cohort(tmp_path)
    df=pd.read_csv(files[0])
    df.loc[0,"independently_rescored_endpoint"]=False
    df.to_csv(files[0],index=False)
    with pytest.raises(ValueError,match="Unverified"):
        require_complete(files,"closer")
    files=cohort(tmp_path)
    df=pd.read_csv(files[0])
    df.loc[0,"endpoint_max_population_deviation"]=.012
    df.to_csv(files[0],index=False)
    with pytest.raises(ValueError,match="Invalid population"):
        require_complete(files,"closer")


def test_mismatched_geographic_caps_rejected(tmp_path):
    files=cohort(tmp_path)
    df=pd.read_csv(files[0])
    df.loc[0,"endpoint_cut_edges"]=900
    df.to_csv(files[0],index=False)
    with pytest.raises(ValueError,match="geography cap"):
        require_complete(files,"closer")
