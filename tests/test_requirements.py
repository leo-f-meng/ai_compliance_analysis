import yaml
from pathlib import Path


def test_requirements_yaml_loads():
    path = Path("data/requirements.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    reqs = data["requirements"]
    assert len(reqs) >= 38
    ids = [r["id"] for r in reqs]
    assert "ART28_DPA_EXECUTED" in ids
    assert "ART28_BREACH_NOTIFICATION" in ids
    assert "ART44_TRANSFER_MECHANISM" in ids
    assert "ART6_LAWFUL_BASIS" in ids


def test_all_requirements_have_required_fields():
    path = Path("data/requirements.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    for req in data["requirements"]:
        assert "id" in req, f"Missing id in {req}"
        assert "description" in req, f"Missing description in {req}"
        assert "article" in req, f"Missing article in {req}"
        assert req["severity"] in ("critical", "high", "medium", "low"), \
            f"Invalid severity in {req['id']}"


def test_no_duplicate_ids():
    path = Path("data/requirements.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    ids = [r["id"] for r in data["requirements"]]
    assert len(ids) == len(set(ids)), "Duplicate requirement IDs found"
