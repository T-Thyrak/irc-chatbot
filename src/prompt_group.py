from dataclasses import dataclass, field

@dataclass
class PromptGroup:
    name: str
    label: str
    prompts: list[str] = field(default_factory=list)