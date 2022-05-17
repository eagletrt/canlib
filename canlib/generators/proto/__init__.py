import os
import subprocess
from pathlib import Path
from shutil import which

from canlib.common import utils
from canlib.generators.proto.compile_schema import compile_schema
from canlib.generators.proto.generators.utils_gen import generate_utils


def get_protoc_executable():
    if "PROTOC" in os.environ and os.path.exists(os.environ["PROTOC"]):
        protoc = os.environ["PROTO"]
    else:
        protoc = which("protoc")

    if not protoc:
        raise RuntimeError(
            "Procol buffer not found, please install it using given requirements.txt"
        )
    else:
        return protoc


def generate(networks_dir: Path, ids_dir: Path, output_dir: Path):
    print("====== flatbuf-generator ======")

    networks = utils.load_networks(networks_dir, ids_dir)

    for network in networks:
        proto_dir = output_dir / "dev"
        output_dir_network = output_dir / "gen" / network.name
        utils_dir_network = output_dir_network

        schema = compile_schema(network, proto_dir)
        compile_proto_files(proto_dir, output_dir_network, network.name)

        generate_utils(schema, network, network.name, utils_dir_network)


def compile_proto_files(proto_dir, output_dir_network, network_name):
    python_dir_network = output_dir_network / "python"
    utils.create_subtree(python_dir_network)

    cpp_dir_network = output_dir_network / "cpp"
    utils.create_subtree(cpp_dir_network)

    if (
        subprocess.call(
            [
                get_protoc_executable(),
                "--proto_path",
                str(proto_dir),
                "--python_out",
                str(python_dir_network),
                str(f"{network_name}.proto"),
            ]
        )
        != 0
    ):
        raise RuntimeError("Proto compilation failed for Python")
    else:
        print(f"Generated {network_name}_pb2.py for Python into {python_dir_network}")

    if (
        subprocess.call(
            [
                get_protoc_executable(),
                "--proto_path",
                str(proto_dir),
                "--cpp_out",
                str(cpp_dir_network),
                str(f"{network_name}.proto"),
            ]
        )
        != 0
    ):
        raise RuntimeError("Proto compilation failed for C++")
    else:
        print(
            f"Generated {network_name}.pb.h and {network_name}.pb.cc for C++ into {cpp_dir_network}"
        )
