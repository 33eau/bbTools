from . import default_namer, hatrig_namer
from importlib import reload

import importlib
importlib.reload(default_namer)
importlib.reload(hatrig_namer)

DefaultNamer = default_namer.DefaultNamer
HatRigNamer = hatrig_namer.HatRigNamer

def get_namer(project: str):
    if project == "default":
        return DefaultNamer()
    if project == "hatrig":
        return HatRigNamer()
    # if project == "qdp":
    #     return QDPNamer()

# from . import namer_factory as naming
# full_name = 'armFk01LFT_ctrl'
# namer = naming.get_namer("hatrig")
# #new_name = namer.extract(full_name)
# new_name = namer.auto(full_name)
# print(new_name)