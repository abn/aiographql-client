from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class GraphQLError:
    extensions: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = field(default=None)
