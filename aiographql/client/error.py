from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union


@dataclass(frozen=True)
class GraphQLError:
    """
    GraphQL error response object.
    """

    extensions: Dict[str, Any] = field(default_factory=dict)
    locations: Optional[List[Dict[str, int]]] = field(default=None)
    message: Optional[str] = field(default=None)
    path: Optional[List[Union[str, int]]] = field(default=None)
    type: Optional[str] = field(default=None)
