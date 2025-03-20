import json

from src.utils.utils import get_path


ship_names = ["Lucifer Cynabal"]
with open(get_path("data/abyss_rooms.json")) as f:
    rooms = json.load(f)

current_room = None
for _, room in rooms.items():
    room_ships = room["ship_names"]
    for ship in ship_names:
        if ship not in room_ships:
            break
    else:
        current_room = room
        break

print(current_room["name"])