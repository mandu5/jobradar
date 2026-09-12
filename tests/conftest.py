import json
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_text():
    return lambda name: (FIX / name).read_text(encoding="utf-8", errors="ignore")


@pytest.fixture
def fixture_json():
    return lambda name: json.loads((FIX / name).read_text(encoding="utf-8"))
