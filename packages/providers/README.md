# Provider System

A plugin architecture for data source providers using decorator-based registration.

## How It Works

1. **Define**: Create a provider class in `providers/<name>.py`
2. **Register**: Decorate with `@register_provider("<name>")`
3. **Use**: Call `get_provider("<name")` to instantiate

## Create a Provider

```python
# providers/mydatasource/main.py
from pydantic import BaseModel

from packages.providers import register_provider
from packages.providers.interface import ProviderBase


@register_provider("mydata")
class MyDataProvider(ProviderBase):
    default_config = {}

    def fetch(self) -> dict[str, list[dict]]:
        # Return raw data
        return {"dataset": [{"id": 1, "name": "item"}]}

    def normalize(self, raw_data) -> dict[str, list[BaseModel]]:
        # Convert to Pydantic models
        return {"dataset": [...]}

    def load(self, normalized) -> dict[str, list[dict]]:
        # Convert models to dicts for persistence
        return {k: [m.model_dump() for m in v] for k, v in normalized.items()}

    def schema(self) -> dict[str, type[BaseModel]]:
        # Define the data model
        return {"dataset": MyModel}
```
