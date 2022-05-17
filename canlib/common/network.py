from pathlib import Path

from canlib.config import CAN_CONFIG_VALIDATION_SCHEMA, NETWORK_VALIDATION_SCHEMA

from . import utils


class Network:
    def __init__(
        self,
        name: str,
        version: int,
        messages: dict,
        types: dict,
        topics: dict,
        can_config: dict,
    ):
        self.name = name
        self.version = version
        self.messages = messages
        self.types = types
        self.topics = topics
        self.can_config = can_config

    @classmethod
    def load(cls, name: str, path: Path, can_config_path: Path, ids_path: Path = None):
        network = utils.load_json(path, NETWORK_VALIDATION_SCHEMA)

        version = network["version"]

        messages = {}
        topics = {}
        types = network.get("types", {})

        for message in network["messages"]:
            if "topic" in message:
                topics[message["topic"]] = None
            else:
                topics["FIXED_IDS"] = None
                message["topic"] = "FIXED_IDS"

            message_name = message.pop("name")
            split_senders = message.get("split_senders", False)

            if split_senders:
                sending_devices = message["sending"]
                for device_id, device_name in enumerate(sending_devices):
                    split_message = message.copy()
                    split_message["sending"] = [device_name]
                    generated_split_message_name = f"{message_name}_{device_id}"
                    messages[generated_split_message_name] = split_message
            else:
                messages[message_name] = message

        can_config = utils.load_json(can_config_path, CAN_CONFIG_VALIDATION_SCHEMA)

        if ids_path:
            ids = utils.load_json(ids_path)
            assert ids["version"] == version

            topics_ids = sorted(ids["topics"].items())
            for topic_name, topic_contents in topics_ids:
                topics[topic_name] = topic_contents.get("id")

                messages_ids = sorted(topic_contents["messages"].items())
                for message_name, message_contents in messages_ids:
                    messages[message_name]["id"] = message_contents["id"]

        return cls(name, version, messages, types, topics, can_config)

    def get_messages_by_topic(self, topic):
        messages = {}
        for name, contents in self.messages.items():
            if contents["topic"] != topic:
                continue
            messages[name] = contents

        return messages

    def get_messages_with_fixed_id(self) -> dict:
        messages = {}
        for name, contents in self.messages.items():
            if "fixed_id" in contents:
                messages[name] = contents

        return messages

    def get_reserved_ids(self) -> dict:
        ids = {}
        for name, contents in self.get_messages_with_fixed_id().items():
            ids[name] = contents["fixed_id"]

        return ids
