import math
import re

from canlib.common.network import Network

BASE_TYPE_SIZES = {
    "bool": 1,
    "int8": 8,
    "uint8": 8,
    "int16": 16,
    "uint16": 16,
    "int32": 32,
    "uint32": 32,
    "int64": 64,
    "uint64": 64,
    "float32": 32,
    "float64": 64,
}


class Schema:
    def __init__(self, network: Network):
        self.messages = []
        self.types = {}
        self.messages_size = {}

        for custom_type_name, custom_type_content in network.types.items():
            if custom_type_content["type"] == "bitset":
                self.types[custom_type_name] = BitSet(custom_type_content)
            elif custom_type_content["type"] == "enum":
                self.types[custom_type_name] = Enum(custom_type_content["items"])
            else:
                raise ValueError(f"Unknown type {custom_type_content['type']}")

        messages_names = set()
        for topic_name in network.topics.keys():
            messages = network.get_messages_by_topic(topic_name)
            for message_name, message_content in messages.items():
                if message_name not in messages_names:
                    messages_names.add(message_name)
                    self.messages.append(
                        Message(
                            network.name,
                            message_name,
                            message_content["contents"],
                            message_content.get("frequency", -1),
                            self.types,
                        )
                    )

        for message in self.messages:
            message.fields = sorted(
                message.fields, key=lambda d: d.bit_size, reverse=True
            )
            self.messages_size[message.name] = {
                0: [],
                1: [],
                2: [],
                3: [],
                4: [],
                5: [],
                6: [],
                7: [],
            }
            indice = 0
            start = 8
            for field in message.fields:

                if field.bit_size % 8 == 0:
                    field.shift = 0
                else:
                    if (indice % 8) + field.bit_size >= 8:
                        indice += 8 - (indice % 8)
                        field.shift = 8 - (indice % 8) - field.bit_size
                        start = 8
                    else:
                        field.shift = 8 - (indice % 8) - field.bit_size
                    mask = 0
                    if isinstance(field.type, Enum) or field.type.name == "bool":
                        for bit in reversed(range(start)):
                            if bit >= field.shift:
                                mask = mask | (1 << bit)
                                start = start - 1
                        field.bit_mask = mask

                self.messages_size[message.name][indice // 8].append(field)

                indice += field.bit_size

            message.size = math.ceil(indice / 8)


class Message:
    def __init__(
        self,
        filename: str,
        name: str,
        content: dict,
        frequency: int,
        custom_types: dict,
    ):
        self.name = f"{filename}_{name}"
        self.fields = []
        self.size = None
        self.frequency = frequency

        for field_name, field_content in content.items():
            self.fields.append(Field(field_name, field_content, custom_types))


class Field:
    def __init__(self, field_name: str, field_type, types: dict):
        self.name = (
            field_name if not ":" in field_name else field_name.split(":")[1].strip()
        )
        self.custom_type = (
            field_type if not ":" in field_name else field_name.split(":")[0].strip()
        )

        if isinstance(self.custom_type, list):
            if not self.name in types:
                types[self.name] = Enum(self.custom_type)
            self.type = types[self.name]
        elif self.custom_type in BASE_TYPE_SIZES:
            self.type = Number(self.custom_type)
        elif not isinstance(self.custom_type, list):
            if not self.custom_type in types:
                types[self.custom_type] = Enum(field_type)
            self.type = types[self.custom_type]

        self.bit_size = self.type.bit_size
        self.byte_size = math.ceil(self.bit_size / 8)
        self.shift = None
        self.bit_mask = None


class BitSet:
    def __init__(self, field_content):
        self.name = None
        self.content = []

        if "items" in field_content:
            self.content = [
                Item(field, index) for index, field in enumerate(field_content["items"])
            ]
            self.size = len(field_content["items"])
        elif "size" in field_content:
            self.size = field_content["size"]
        else:
            raise Exception("Invalid bitset format")

        self.bit_size = math.ceil(self.size / 8) * 8
        self.byte_size = self.bit_size // 8 if self.bit_size // 8 != 0 else 1
        self.parent = []
        if "contents" in field_content:
            for bitset in field_content["contents"]:
                self.parent.append(str(bitset))


class Number:
    def __init__(self, field):
        self.name = field
        self.bit_size = BASE_TYPE_SIZES[field]


class Enum:
    def __init__(self, field_content):
        self.name = None
        self.content = []

        for index, enum_item in enumerate(field_content):
            self.content.append(Item(enum_item, index))

        self.bit_size = math.ceil(math.log2(len(self.content)))


class Item:
    def __init__(self, item, index):
        self.item = item
        self.index = index
