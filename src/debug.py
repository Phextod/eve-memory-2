from src.abyss.abyss_bot import AbyssBot
from src.utils.utils import *


self = AbyssBot(CHARACTER_NAME)
print("Ready")

asd = self.ui.locations.get_entry("Personal Locations/Abyss/safe spot")
click(asd, MOUSE_RIGHT)

self.ui.context_menu.click("Set Destination")
