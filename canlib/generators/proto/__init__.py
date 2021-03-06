import os
import subprocess
from pathlib import Path
from shutil import which

from canlib.common import utils
from canlib.common.network import Network
from canlib.common.schema import Schema
from canlib.generators.proto import mapping, proto


def generate(networks_dir: Path, ids_dir: Path, output_dir: Path):
    print("====== proto ======")

    networks = utils.load_networks(networks_dir, ids_dir)
    proto_dir = output_dir / ".proto"

    for network in networks:
        output_dir_network = output_dir / network.name

        utils.create_subtree(proto_dir)
        utils.create_subtree(output_dir_network)

        schema = Schema(network)

        proto.generate(network, schema, proto_dir)
        print(f"Generated protobuf files {proto_dir}")

        mapping.generate(network, schema, output_dir_network)

        compile_proto_files(network, proto_dir, output_dir_network)
        print(f"Compiled protobuf files {output_dir_network}")


def get_protoc_executable():
    if "PROTOC" in os.environ:
        return os.environ["PROTO"]

    protoc = which("protoc")
    if not protoc:
        raise RuntimeError("protoc not found")

    return protoc


def compile_proto_files(network: Network, proto_dir, output_dir_network):
    python_dir_network = output_dir_network / "python"
    utils.create_subtree(python_dir_network)

    cpp_dir_network = output_dir_network / "cpp"
    utils.create_subtree(cpp_dir_network)

    compile_subprocess = subprocess.call(
        [
            get_protoc_executable(),
            "--proto_path",
            str(proto_dir),
            "--cpp_out",
            str(cpp_dir_network),
            "--python_out",
            str(python_dir_network),
            str(proto_dir / f"{network.name}.proto"),
        ]
    )

    if compile_subprocess != 0:
        raise RuntimeError("Proto compilation failed")
