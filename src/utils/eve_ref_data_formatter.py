import json

from src.utils.utils import get_path

# 1: Download latest reference data from: https://data.everef.net/reference-data/
# 2: Extract dogma_attributes.json and types.json into the data folder
# 3: Run this script


TYPES_INPUT_PATH = "data/types.json"
ATTRIBUTES_INPUT_PATH = "data/dogma_attributes.json"
SHIP_OUTPUT_PATH = "data/ships_data.json"
ITEM_OUTPUT_PATH = "data/item_data.json"
SHIP_RELEVANT_GROUP_IDS = [
    1982,  # Abyssal Spaceship Entities
    1997,  # Abyssal Drone Entities
]
ITEM_RELEVANT_GROUP_IDS = [
    384,  # Light Missile
    385,  # Heavy Missile
]


def load_types(types_file):
    with open(types_file, "r", encoding="utf-8") as f:
        types_data = json.load(f)
    return types_data


def load_attributes(attributes_file):
    with open(attributes_file, "r", encoding="utf-8") as f:
        attributes_data = json.load(f)

    attribute_names = dict()
    for key, data in attributes_data.items():
        attribute_names.update({key: data["name"]})
    return attribute_names


def format_data(types_data, attribute_names, output_file, relevant_group_ids):
    # Read and filter data
    output_data = dict()
    for key, data in types_data.items():
        if data.get("group_id") not in relevant_group_ids:
            continue

        relevant_data = dict()
        relevant_data.update({"name": data["name"]["en"]})
        for attribute_id, attribute_value in data.get("dogma_attributes").items():
            attribute_name = attribute_names[attribute_id]
            relevant_data.update({attribute_name: attribute_value["value"]})

        output_data.update({key: relevant_data})

    # Write relevant data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved data to {output_file}")


if __name__ == "__main__":
    _types_data = load_types(get_path(TYPES_INPUT_PATH))
    _attribute_names = load_attributes(get_path(ATTRIBUTES_INPUT_PATH))
    format_data(_types_data, _attribute_names, get_path(SHIP_OUTPUT_PATH), SHIP_RELEVANT_GROUP_IDS)
    format_data(_types_data, _attribute_names, get_path(ITEM_OUTPUT_PATH), ITEM_RELEVANT_GROUP_IDS)

