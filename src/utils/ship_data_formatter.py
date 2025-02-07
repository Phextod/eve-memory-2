import json

from src.utils.utils import get_path


# 1: Download latest reference data from: https://data.everef.net/reference-data/
# 2: Extract dogma_attributes.json and types.json into the data folder
# 3: Run this script


TYPES_INPUT_PATH = "data/types.json"
ATTRIBUTES_INPUT_PATH = "data/dogma_attributes.json"
OUTPUT_PATH = "data/ships_data.json"
RELEVANT_GROUP_IDS = [
    1982,  # Abyssal Spaceship Entities
]


def format_data(types_file, attributes_file, output_file):
    # Read types
    with open(types_file, "r", encoding="utf-8") as f:
        types_data = json.load(f)

    # Read attributes
    with open(attributes_file, "r", encoding="utf-8") as f:
        attributes_data = json.load(f)

    # Decode attributes
    attribute_names = dict()
    for key, data in attributes_data.items():
        attribute_names.update({key: data["name"]})

    # Read and filter data
    output_data = dict()
    for key, data in types_data.items():
        if data.get("group_id") not in RELEVANT_GROUP_IDS:
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
    format_data(get_path(TYPES_INPUT_PATH), get_path(ATTRIBUTES_INPUT_PATH), get_path(OUTPUT_PATH))
