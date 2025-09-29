import json

class BaseDataLoader:
    def __init__(self, folder):
        self.base_path = f"data/{folder}/"

    def load_der_production(self):
        with open(self.base_path + "DER_production.json") as f:
            return json.load(f)[0]["hourly_profile_ratio"]

    def load_appliance_params(self):
        with open(self.base_path + "appliance_params.json") as f:
            return json.load(f)

    def load_bus_params(self):
        with open(self.base_path + "bus_params.json") as f:
            return json.load(f)[0]

    def load_usage_preferences(self):
        with open(self.base_path + "usage_preference.json") as f:
            return json.load(f)[0]


# Wrapper classes for clarity
class DataLoader1a(BaseDataLoader):
    def __init__(self):
        super().__init__("question_1a")


class DataLoader1b(BaseDataLoader):
    def __init__(self):
        super().__init__("question_1b")


