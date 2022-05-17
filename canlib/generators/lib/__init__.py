from pathlib import Path

from canlib import config
from canlib.common import utils
from canlib.generators.lib.generators import c_gen, py_gen
from canlib.generators.lib.schema import Schema


def generate(networks_dir: Path, ids_dir: Path, output_dir: Path):
    print("====== naked-generator ======")

    networks = utils.load_networks(networks_dir, ids_dir)

    for network in networks:
        output_dir_network = output_dir / network.name

        schema = Schema(network)
        file_name = network.name

        output_path_py = output_dir_network / "py"
        py_gen.generate(file_name, network, schema, output_path_py)
        print(f"Generated Python code into {output_path_py}")

        output_path_c = output_dir_network / "c"
        c_gen.generate(file_name, network, schema, output_path_c)
        print(f"Generated C code into {output_path_c}")

        print(f"Generating includes for network {network.name}")
        utils.create_subtree(output_dir_network)
