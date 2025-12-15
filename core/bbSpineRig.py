cmds.file("W:/RIG/PROJ/MAYA_PROJ/HATRIG/scenes/AUTO_RIG/spine_start.ma", o=True, f=True )
from importlib import reload
import maya.cmds as cmds
from .utils import rig_utils as bb
from .controllers import creator as bc
from .naming import namer_factory as naming
from .naming import current_project
from .naming import parser

reload(bb)
reload(bc)
reload(naming)
reload(current_project)
reload(parser)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

class spineRig:
	def __init__(self,
				joints=None,
				rig_name=None,
				side=None,
				
			
	)