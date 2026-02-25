from dataclasses import asdict, dataclass
import uuid


@dataclass
class Rarity:
    id: str
    name: str
    min_roll: float
    max_roll: float
    color: str = "#888888"
    drop_sound: str = ""
    drop_effect: str = ""

    @classmethod
    def create(cls, **kwargs):
        return cls(id=str(uuid.uuid4()), **kwargs)


@dataclass
class Item:
    id: str
    name: str
    rarity_id: str
    weight: float
    image_path: str = ""
    description: str = ""

    @classmethod
    def create(cls, **kwargs):
        return cls(id=str(uuid.uuid4()), **kwargs)


@dataclass
class LevelSettings:
    base_xp: int = 8
    xp_growth: float = 1.35

    def to_dict(self):
        return asdict(self)
