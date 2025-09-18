from pydantic import BaseModel

class RuleUpdate(BaseModel):
    rule_content: str
    rule_file: str = "local.rules"