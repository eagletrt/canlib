from pathlib import Path

import jinja2 as j2

from canlib.common.network import Network
from canlib.generators.lib.schema import Schema

BASE_DIR = Path(__file__).parent

TEMPLATE_IDS = j2.Template((BASE_DIR / "ids.py.j2").read_text())


def generate(network: Network, schema: Schema, output_path: Path):
    ids_path = output_path / "ids.py"
    ids_path.write_text(TEMPLATE_IDS.render(network=network, schema=schema))
