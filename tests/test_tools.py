from app.tools.checklist_tool import ChecklistLookupTool


def test_checklist_lookup_known_id():
    tool = ChecklistLookupTool()
    result = tool._run("ART28_DPA_EXECUTED")
    assert "ART28_DPA_EXECUTED" in result
    assert "critical" in result.lower()
    assert "Art. 28" in result


def test_checklist_lookup_unknown_id():
    tool = ChecklistLookupTool()
    result = tool._run("NONEXISTENT_ID")
    assert "not found" in result


def test_checklist_lookup_breach_notification():
    tool = ChecklistLookupTool()
    result = tool._run("ART28_BREACH_NOTIFICATION")
    assert "breach" in result.lower()
    assert "critical" in result.lower()
