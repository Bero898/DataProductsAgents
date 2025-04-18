import yaml

with open(".\Data Products\example-DPs\Data Contract Playground - Pflooky\data-contract-specification.yaml") as stream:
    try:
        print("YAML file loaded successfully.")
        print(str(yaml.safe_load(stream)))
    except yaml.YAMLError as exc:
        print(exc)