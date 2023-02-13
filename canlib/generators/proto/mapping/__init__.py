from pathlib import Path

import jinja2 as j2

from canlib.common.network import Network
from canlib.common.schema import Schema

BASE_DIR = Path(__file__).parent

TEMPLATE_MAPPING_CPP = j2.Template((BASE_DIR / "mapping.h.j2").read_text())
TEMPLATE_PROTO_INTERFACE_CPP = j2.Template(
    (BASE_DIR / "proto_interface.h.j2").read_text()
)


def generate(network: Network, schema: Schema, output_dir: Path):
    (output_dir / "cpp").mkdir(parents=True, exist_ok=True)
    mapping_path = (output_dir / "cpp") / "mapping.h"
    mapping_path.write_text(TEMPLATE_MAPPING_CPP.render(network=network, schema=schema))

    mapping_path = (output_dir / "cpp") / "proto_interface.h"
    mapping_path.write_text(
        TEMPLATE_PROTO_INTERFACE_CPP.render(network=network, schema=schema)
    )
