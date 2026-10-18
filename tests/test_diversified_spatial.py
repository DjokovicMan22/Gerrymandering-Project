"""Synthetic validations of the sparse label-invariant spatial-probe aggregator."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "research_audit"))
from analyze_diversified_spatial import analyze_spatial


def write_probes(tmp_path):
    steps=[0,1000,2000,3000,4000]
    files=[]
    for i in range(4):
        df=pd.DataFrame({
            "step":steps,
            "reference_fraction_different":[.10+i*.01+j*.01 for j in range(5)],
            "warm_start_fraction_different":[0,.05,.10,.15,.20],
            "assignment_sha256":[f"{i+1}{j:063x}" for j in range(5)],
        })
        p=tmp_path / f"chain_{i}.csv"
        df.to_csv(p,index=False)
        files.append(p)
    return files


def test_spatial_aggregation_has_all_four_chains_and_five_checkpoints(tmp_path):
    files=write_probes(tmp_path)
    raw,summary,audit=analyze_spatial(files)
    assert len(raw)==20
    assert list(summary["step"])==[0,1000,2000,3000,4000]
    assert summary.iloc[0]["warm_mean"]==0
    assert summary.iloc[-1]["warm_mean"]==pytest.approx(.20)
    assert summary.iloc[-1]["unique_assignment_hashes"]==4
    assert audit["endpoint_unique_assignment_hashes"]==4


def test_invalid_digest_and_wrong_checkpoint_fail_closed(tmp_path):
    files=write_probes(tmp_path)
    frame=pd.read_csv(files[0])
    frame.loc[1,"assignment_sha256"]="not-a-sha256"
    frame.to_csv(files[0],index=False)
    with pytest.raises(ValueError,match="invalid assignment hash"):
        analyze_spatial(files)
    files=write_probes(tmp_path)
    frame=pd.read_csv(files[0])
    frame.loc[1,"step"]=99
    frame.to_csv(files[0],index=False)
    with pytest.raises(ValueError,match="checkpoint indices"):
        analyze_spatial(files)


def test_repeated_initial_hashes_are_not_distinct_starts(tmp_path):
    files=write_probes(tmp_path)
    one=pd.read_csv(files[0])
    two=pd.read_csv(files[1])
    two.loc[0,"assignment_sha256"]=one.loc[0,"assignment_sha256"]
    two.to_csv(files[1],index=False)
    with pytest.raises(ValueError,match="warm-start assignment hashes must be distinct"):
        analyze_spatial(files)
