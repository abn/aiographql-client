import time
import dataclasses
from aiographql.client.codec import DefaultGraphQLCodec

@dataclasses.dataclass
class User:
    id: int
    name: str
    is_active: bool
    email: str

codec = DefaultGraphQLCodec()

data = {
    "id": 1,
    "name": "Alice",
    "is_active": True,
    "email": "alice@example.com"
}

# Warmup
for _ in range(10):
    codec.decode(data, User)

start = time.perf_counter()
for _ in range(100000):
    codec.decode(data, User)
end = time.perf_counter()

print(f"Time taken: {end - start:.4f} seconds")
