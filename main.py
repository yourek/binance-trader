import importlib
import config_loader

importlib.reload(config_loader)
config = config_loader.load_config('..\config.yaml')