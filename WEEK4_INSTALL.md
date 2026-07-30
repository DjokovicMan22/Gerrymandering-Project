# Week 4 patch installation

Copy this patch into the project root so that `scripts/`, `src/`, `docs/`, and `tests/` merge with the existing folders.

Then run:

```bash
python -m pip install -e .
pytest -q
python scripts/run_baseline.py --state mi --steps 100 --seed 2026 --chain-id debug
```

See `docs/week4_markov_chains.md` for the full sequence.
