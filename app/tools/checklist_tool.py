import yaml
from pathlib import Path
from langchain.tools import BaseTool
from pydantic import BaseModel


class ChecklistInput(BaseModel):
    requirement_id: str


class ChecklistLookupTool(BaseTool):
    name: str = "checklist_lookup"
    description: str = (
        "Look up a GDPR requirement by its ID. "
        "Returns the requirement description, article reference, and severity. "
        "Use this before checking whether a clause satisfies a requirement."
    )
    args_schema: type[BaseModel] = ChecklistInput
    _requirements: dict = {}

    def __init__(self, requirements_path: str = "data/requirements.yaml", **kwargs):
        super().__init__(**kwargs)
        with open(requirements_path) as f:
            data = yaml.safe_load(f)
        self._requirements = {r["id"]: r for r in data["requirements"]}

    def _run(self, requirement_id: str) -> str:
        req = self._requirements.get(requirement_id)
        if not req:
            return f"Requirement '{requirement_id}' not found in checklist."
        return (
            f"ID: {req['id']}\n"
            f"Description: {req['description']}\n"
            f"Article: {req['article']}\n"
            f"Severity: {req['severity']}"
        )
