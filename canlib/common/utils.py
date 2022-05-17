import errno
import json
import os
from pathlib import Path

from jsonschema import validate

from canlib.common.network import Network


def load_json(path: Path, validation_schema_path=None) -> dict:
    with open(path, "r") as file:
        data = json.load(file)

    if validation_schema_path is not None:
        with open(validation_schema_path, "r") as file:
            schema = json.load(file)
        validate(data, schema)

    return data


def create_subtree(path: Path):
    if not path.exists():
        try:
            path.mkdir(parents=True)
        except OSError as exception:  # Guard against race condition
            if exception.errno != errno.EEXIST:
                raise exception


def load_networks(networks_dir: Path, ids_dir: Path = None):
    networks = []

    for directory in networks_dir.iterdir():
        name = directory.name

        path = networks_dir / name / "network.json"
        assert path.exists()

        can_config_path = networks_dir / name / "can_config.json"

        if ids_dir is None:
            ids_path = None
        else:
            ids_path = ids_dir / name / "ids.json"
            assert ids_path.exists()

        network = Network.load(name, path, can_config_path, ids_path)
        networks.append(network)

    return networks


def to_camel_case(string: str, delimiter=" "):
    return "".join([x.capitalize() for x in string.split(delimiter)])


def to_snake_case(string: str, delimiter=" "):
    return "".join([x.lower() for x in string.split(delimiter)])
