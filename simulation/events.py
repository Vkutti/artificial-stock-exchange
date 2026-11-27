from dataclasses import dataclass, field


@dataclass(order=True)
class Event:
    tick: int
    priority: int
    trader: object = field(compare=False)
