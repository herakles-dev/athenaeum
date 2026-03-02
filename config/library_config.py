"""Library configuration loader — reads config/library.yml and exposes typed config."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_LIBRARY_YML = Path(__file__).parent / "library.yml"


@dataclass
class LibraryMeta:
    name: str
    title: str
    author: str
    domain: str
    subdomain: str
    description: str


@dataclass
class Ports:
    db: int
    api: int
    frontend: int


@dataclass
class RagPersona:
    name: str
    short_description: str
    voice: str
    key_themes: list[str]
    system_prompt_template: str

    def build_system_prompt(self) -> str:
        """Build the full system prompt from the template and fields."""
        key_themes_bullet = "\n".join(f"- {t}" for t in self.key_themes)
        return self.system_prompt_template.format(
            name=self.name,
            short_description=self.short_description,
            voice=self.voice,
            key_themes_bullet=key_themes_bullet,
        )


@dataclass
class TopicRule:
    triggers: list[str]
    label: str
    weight: float

    def as_tuple(self) -> tuple[list[str], str, float]:
        """Return (triggers, label, weight) tuple for cluster.py compatibility."""
        return (self.triggers, self.label, self.weight)


@dataclass
class FrontendConfig:
    suggestions: list[str]
    hero_tagline: str
    accent_color: str


@dataclass
class LibraryConfig:
    library: LibraryMeta
    ports: Ports
    rag_persona: RagPersona
    topic_rules: list[TopicRule]
    frontend: FrontendConfig


def _load_raw(path: Path = _LIBRARY_YML) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_config(raw: dict[str, Any]) -> LibraryConfig:
    lib = raw["library"]
    library_meta = LibraryMeta(
        name=lib["name"],
        title=lib["title"],
        author=lib["author"],
        domain=lib["domain"],
        subdomain=lib["subdomain"],
        description=lib["description"],
    )

    ports_raw = raw["ports"]
    ports = Ports(
        db=int(ports_raw["db"]),
        api=int(ports_raw["api"]),
        frontend=int(ports_raw["frontend"]),
    )

    persona_raw = raw["ragPersona"]
    rag_persona = RagPersona(
        name=persona_raw["name"],
        short_description=persona_raw["shortDescription"],
        voice=persona_raw["voice"],
        key_themes=list(persona_raw["keyThemes"]),
        system_prompt_template=persona_raw["systemPromptTemplate"],
    )

    topic_rules = [
        TopicRule(
            triggers=[str(t) for t in rule["triggers"]],
            label=str(rule["label"]),
            weight=float(rule["weight"]),
        )
        for rule in raw.get("topicRules", [])
    ]

    fe_raw = raw["frontend"]
    frontend = FrontendConfig(
        suggestions=list(fe_raw["suggestions"]),
        hero_tagline=fe_raw["heroTagline"],
        accent_color=fe_raw["accentColor"],
    )

    return LibraryConfig(
        library=library_meta,
        ports=ports,
        rag_persona=rag_persona,
        topic_rules=topic_rules,
        frontend=frontend,
    )


_config: LibraryConfig | None = None


def get_library_config(path: Path = _LIBRARY_YML) -> LibraryConfig:
    """Return singleton LibraryConfig, loading from library.yml on first call."""
    global _config
    if _config is None:
        raw = _load_raw(path)
        _config = _parse_config(raw)
    return _config
