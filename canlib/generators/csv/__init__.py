import csv
import re
from pathlib import Path

from canlib import config
from canlib.common import utils

re_clean = re.compile(r"\[|]|'|{|}|\"")


def generate(networks_dir: Path, ids_dir: Path, output_dir: Path):
    networks = utils.load_networks(networks_dir, ids_dir)

    utils.create_subtree(output_dir)

    columns = config.COLUMNS_ORDER

    out_file = output_dir / "networks.csv"

    with open(out_file, "w+") as out:
        writer = csv.writer(out)
        writer.writerow(columns)
        for network in networks:
            for message_name, message_contents in network.messages.items():
                # Cleaning message dict and adding network column
                message_contents.pop("fixed_id", None)
                message_contents["name"] = message_name
                message_contents["network"] = network.name

                cols = [""] * len(columns)
                for key, value in message_contents.items():
                    if key not in columns:
                        continue
                    cols[columns.index(key)] = re_clean.sub("", str(value))
                writer.writerow(cols)
