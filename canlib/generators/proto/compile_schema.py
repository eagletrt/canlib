import re

from canlib.generators.proto.generators.proto_gen import generate
from canlib.generators.proto.schema import Schema


def compile_schema(network, output_path):
    # Load schema
    schema = Schema(schema=generate_schema_from_network(network))

    file_name = network.name

    if True:  # Generate proto
        generate(schema, file_name, output_path)
        print(f"Generated {file_name}.proto for Protocol Buffers into {output_path}")

    return schema


def generate_schema_from_network(network):
    schema = {"types": {}, "structs": {}}
    for topic_name, _ in network.topics.items():
        schema["types"] = network.types
        for message_name, message_contents in network.get_messages_by_topic(
            topic_name
        ).items():
            struct = {}
            for field_name, field in message_contents["contents"].items():
                if isinstance(field, list):
                    if ":" in field_name:  # Named enum
                        enum_name = field_name.split(":")[0].strip().title()
                        field_name = field_name.split(":")[1].strip()
                    else:
                        enum_name = field_name.title()
                    schema["types"][enum_name] = {"type": "enum", "items": field}
                    field = enum_name
                struct[field_name] = field
            schema["structs"][message_name] = struct

    return schema
