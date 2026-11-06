import pytest
import aggrun


@pytest.mark.parametrize("case", aggrun.CASES, ids=[c["id"] for c in aggrun.CASES])
def test_case(case):
    h = aggrun.sumrun.run_case(case)
    assert aggrun.sumrun.check(case, h) == []
