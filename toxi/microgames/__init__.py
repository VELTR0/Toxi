from .base import SCREEN_H, SCREEN_W
from .sword_arena import SwordArena
from .maze_portals import MazePortals
from .platform_gates import PlatformGates
from .lab_catcher import LabCatcher
from .comet_click import CometClick
from .pokemon_battle import PokemonBattle

MICROGAME_TYPES = {
    "sword_arena": SwordArena,
    "maze_portals": MazePortals,
    "platform_gates": PlatformGates,
    "lab_catcher": LabCatcher,
    "comet_click": CometClick,
    "pokemon_battle": PokemonBattle,
}
