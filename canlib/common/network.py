from pathlib import Path
from canlib.common.limits import RESERVED_KEYWORKDS

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
            message_name = message.pop("name")
            if "topic" in message:
                topic = message["topic"]
                if topic in RESERVED_KEYWORKDS:
                    raise ValueError(f"Topic {topic} reserved, message {message_name}")
                topics[topic] = None
            else:
                topics["FIXED_IDS"] = None
                message["topic"] = "FIXED_IDS"

            if name in RESERVED_KEYWORKDS:
                raise ValueError(f"Message {message_name} reserved, network {name}")
            messages[message_name] = message

        can_config = utils.load_json(can_config_path, CAN_CONFIG_VALIDATION_SCHEMA)

        if ids_path:
            ids = utils.load_json(ids_path)
            assert ids["version"] == version

            topics_ids = sorted(ids["topics"].items())
            for topic_name, topic_contents in topics_ids:
                topics[topic_name] = topic_contents.get("id")

                messages_ids = sorted(topic_contents["messages"].items())
                for message_name, message in messages_ids:
                    messages[message_name]["id"] = message

        return cls(name, version, messages, types, topics, can_config)

    def get_messages_by_topic(self, topic) -> dict:
        return {
            name: contents
            for name, contents in self.messages.items()
            if contents["topic"] == topic
        }

    def get_messages_with_fixed_id(self) -> dict:
        return {
            name: contents
            for name, contents in self.messages.items()
            if "fixed_id" in contents
        }

    def get_reserved_ids(self) -> set:
        return {
            contents["fixed_id"]
            for contents in self.get_messages_with_fixed_id().values()
        }

    def max_message_length(self):
        return max(
            max(len(name) for name in message["id"].keys())
            for message in self.messages.values()
        )

    def get_message_count(self):
        return sum(len(message["id"]) for message in self.messages.values())
