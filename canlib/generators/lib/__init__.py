from pathlib import Path

from canlib.common import utils
from canlib.generators.lib import c, python
from canlib.generators.lib.schema import Schema


def generate(networks_dir: Path, ids_dir: Path, output_dir: Path):
    print("====== lib ======")

    networks = utils.load_networks(networks_dir, ids_dir)
    utils.create_subtree(output_dir)

    for network in networks:
        output_dir_network = output_dir / network.name

        schema = Schema(network)

        output_path_python = output_dir_network / "python"
        utils.create_subtree(output_path_python)
        python.generate(network, schema, output_path_python)
        print(f"Generated Python code into {output_path_python}")

        output_path_c = output_dir_network / "c"
        utils.create_subtree(output_path_c)
        c.generate(network, schema, output_path_c)
        print(f"Generated C code into {output_path_c}")
