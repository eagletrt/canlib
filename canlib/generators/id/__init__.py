import json
from pathlib import Path

from canlib.common.network import Network, utils

# xxxxxx xxxxx => can id has 11 bits
# ^^^^^^       => bits for message id
#        ^^^^^ => bits for topic id

MESSAGE_BITS = 6
TOPIC_BITS = 5

MAX_PRIORITY = 7

MESSAGES_PER_PRIORITY = int(2**MESSAGE_BITS / (MAX_PRIORITY + 1))


def generate_ids(network: Network, blacklist=None):
    if len(network.messages) >= 2**MESSAGE_BITS:
        raise Exception(f"No messages (>{2**MESSAGE_BITS})")

    ids = {}
    topics = generate_topics_id(network)

    for name, id in topics.items():
        if name == "FIXED_IDS":
            continue

        messages = network.get_messages_by_topic(name)
        message_ids = generate_messages_id(messages, id, blacklist)

        ids[name] = {"id": id, "messages": message_ids}

    return ids


def generate_messages_id(topic_messages, topic_id, blacklist=None):
    message_ids = {}
    # keeps track of how many items are present in each priority level
    items_count = [0] * (MAX_PRIORITY + 1)

    for message_name, message_contents in topic_messages.items():
        message_priority = message_contents["priority"]

        if message_priority > MAX_PRIORITY:
            raise Exception(f'"{message_name}" out of range (0-{MAX_PRIORITY})')

        item_id = items_count[message_priority]

        # try to assign next available id
        while True:
            items_count[message_priority] += 1
            start = MESSAGES_PER_PRIORITY * (MAX_PRIORITY - message_priority)
            if item_id >= MESSAGES_PER_PRIORITY:
                raise Exception(f"No more messages (>{MESSAGES_PER_PRIORITY})")

            scoped_id = item_id + start
            global_id = (scoped_id << TOPIC_BITS) + topic_id

            if global_id not in blacklist:
                break

            item_id += 1  # next one

        message_ids[message_name] = {"id": global_id}

    return message_ids


def generate_topics_id(network: Network):
    ids = {topic: index for index, topic in enumerate(network.topics)}
    if len(ids) >= 2**TOPIC_BITS:
        raise Exception(f"No more topics (>{2**TOPIC_BITS})")

    return ids


def generate_fixed_ids(network: Network):
    ids = {}
    for name, content in network.get_messages_with_fixed_id().items():
        ids[name] = {"id": content["fixed_id"]}
    return ids


def generate(networks_dir: Path, output_dir: Path):
    print("====== id-generator ======")
    print(f"Max topics: {2**TOPIC_BITS}")
    print(f"Max messages per topic: {2**MESSAGE_BITS}")
    print(f"Priority range: {0}-{MAX_PRIORITY}")
    print(f"Max messages per priority per topic: {MESSAGES_PER_PRIORITY}")

    networks = utils.load_networks(networks_dir)

    for network in networks:
        print(f"Generating ids for network {network.name}...")
        reserved_ids = network.get_reserved_ids().keys()

        # Generating IDs
        ids = generate_ids(network, blacklist=reserved_ids)

        # Adding fixed IDs
        fixed_ids = generate_fixed_ids(network)
        if fixed_ids:  # Don't create the topic unless there is at least one fixed id
            ids["FIXED_IDS"] = {"messages": fixed_ids}

        output = {"version": network.version, "topics": ids}

        output_file = output_dir / network.name / "ids.json"
        print(f"Saving to {output_file}")

        utils.create_subtree(output_file.parent)
        with open(output_file, "w+") as file:
            json.dump(output, file, indent=4)
