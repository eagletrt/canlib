import csv
import re
from pathlib import Path

from canlib import config
from canlib.common import utils

re_clean = re.compile(r"\[|]|'|{|}|\"")


def generate(networks_dir: Path, ids_dir: Path, output_dir: Path):
    print("====== csv ======")
    networks = utils.load_networks(networks_dir, ids_dir)

    utils.create_subtree(output_dir)

    columns = config.COLUMNS_ORDER

    output_path = output_dir / "networks.csv"

    with open(output_path, "w+") as out:
        writer = csv.writer(out)
        writer.writerow(columns)
        for network in networks:
            print(f"Creating csv with network {network.name}...")
            for message_name, message in network.messages.items():
                # Cleaning message dict and adding network column
                message.pop("fixed_id", None)
                message["name"] = message_name
                message["network"] = network.name

                cols = [""] * len(columns)
                for key, value in message.items():
                    if key not in columns:
                        continue
                    cols[columns.index(key)] = re_clean.sub("", str(value))
                writer.writerow(cols)
        print(f"Saving to {output_path}")
