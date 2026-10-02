from pathlib import Path
import pytest
@pytest.fixture(autouse=True)
def use_explicit_local_base(monkeypatch):
    from needle.agent import fetch
    base=Path(__file__).resolve().parents[1]/'运行资源/Cactus-Compute__needle3/needle3.cact'
    monkeypatch.setattr(fetch,'fetch_weights',lambda generation=3, dest_dir=None, force=False: str(base))
