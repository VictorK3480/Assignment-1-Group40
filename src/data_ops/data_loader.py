import json
from pathlib import Path
from typing import Any, Dict, List


class BaseDataLoader:
    """Base loader that reads JSON files from data/<folder>/."""

    def __init__(self, folder: str):
        self.base_path = Path("data") / folder

    def _read_json(self, name: str) -> Any:
        # Centralized file read + parse
        with open(self.base_path / name, "r") as f:
            return json.load(f)

    def load_der_production(self) -> List[float]:
        # Normalize: data can be list[0] with 'hourly_profile_ratio'
        data = self._read_json("DER_production.json")
        obj = data[0] if isinstance(data, list) else data
        return obj["hourly_profile_ratio"]

    def load_appliance_params(self) -> Dict[str, Any]:
        # Some callers expect dict, some list; keep raw and let callers normalize
        return self._read_json("appliance_params.json")

    def load_bus_params(self) -> Dict[str, Any]:
        # Normalize to dict (first element if list)
        data = self._read_json("bus_params.json")
        return data[0] if isinstance(data, list) else data

    def load_usage_preferences(self) -> Dict[str, Any]:
        # Normalize to dict (first element if list)
        data = self._read_json("usage_preference.json")
        return data[0] if isinstance(data, list) else data


# Scenario-specific wrappers for clarity
class DataLoader1a(BaseDataLoader):
    def __init__(self):
        super().__init__("question_1a")


class DataLoader1b(BaseDataLoader):
    def __init__(self):
        super().__init__("question_1b")


class DataLoader1c(BaseDataLoader):
    def __init__(self):
        super().__init__("question_1c")

class DataLoader2b(BaseDataLoader):
    def __init__(self):
        super().__init__("question_2b")
