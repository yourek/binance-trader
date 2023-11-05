import yaml

def load_config(config_file):
    # Load the configuration from the YAML file
    with open(config_file, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)

    # Access specific configuration values
    API_KEY = config["API"]["API_KEY"]
    API_SECRET = config["API"]["API_SECRET"]

    return config