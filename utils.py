from addict import Dict


class Config(Dict):
    "a dict that supports attribute access, with an initialization flag"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "initialized" not in self:
            self.initialized = False

    def check_initialized(self, func):
        "use it to decorate the function that requires the config to be initialized"

        def wrapper(*args, **kwargs):
            if not self.initialized:
                raise Exception("Configuration is not initialized. Call `init` before using this function.")
            return func(*args, **kwargs)

        return wrapper

    def mark_initialized(self):
        self.initialized = True
