from __future__ import annotations

import numpy as np
import pytest

from redistricting.diagnostics.convergence import split_rhat
from redistricting.ensemble.chain import ChainConfig, exact_efficiency_gap


def test_chain_config_rejects_one_step():
    with pytest.raises(ValueError):
        ChainConfig(total_steps=1).validate()


def test_efficiency_gap_balanced_example():
    # D wins one district 60-40; R wins the other 60-40. Equal turnout and symmetry.
    assert exact_efficiency_gap([60, 40], [40, 60]) == pytest.approx(0.0)


def test_efficiency_gap_no_votes_is_nan():
    assert np.isnan(exact_efficiency_gap([0], [0]))


def test_split_rhat_identical_stationary_chains_has_expected_finite_sample_value():
    # Split halves each have length n=10. With identical chains, B=0,
    # so classical R-hat equals sqrt((n - 1) / n).
    chain = np.tile([0.0, 1.0], 10)
    expected = np.sqrt(9.0 / 10.0)
    assert split_rhat([chain, chain]) == pytest.approx(expected)


def test_split_rhat_requires_two_chains():
    assert np.isnan(split_rhat([np.arange(10)]))


def test_split_rhat_detects_drift():
    chain = np.arange(20, dtype=float)
    assert split_rhat([chain, chain]) > 1.1
