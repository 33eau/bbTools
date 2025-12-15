# from importlib import reload
# import maya.cmds as cmds
from .utils import rig_utils as bb
from .controllers import creator as bc
from .data import constants 
from .naming import namer_factory as naming
from .naming import current_project
from .naming import parser

reload(bb )
reload(bc)
reload(constants)
reload(naming)
reload(current_project)
reload(parser)

parent_spaces = ['l_leg_ik_ctl', 'placement_grp']
attr_name = 'follow'
spaces_name = ['local', 'world']
target = 'l_leg_pv_offset_grp'
ctrl = 'l_leg_pv_ctl'
type = 'parent'
default_index = 0

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

target_name = parser.get_base_name(target, base_number=True)

parent_groups = []
for i, parent in enumerate(parent_spaces):
	base, element, number, side, suffix = NAMER.extract(parent) 
	space_grp = bb.create_node('group', base, ['space', target_name], number, side )
	cmds.matchTransform(space_grp, target)
	bb.create_constrain
	parent_groups.append(space_grp)
	space_cdt = bb.create_node(node_type='condition', base='', elements=['space'], number=number, side=side )
	


if spaces_name:
	enum_names = ':'.join(spaces_name)
	cmds.addAttr(ctrl, ln = attr_name, at='enum', en=enum_names, dv=default_index, k=True )
	

base, element, number, side, suffix = NAMER.extract(target) 
node_name = NAMER.format(base, ['space'], number, side, 'pac')
space_switch_con = cmds.parentConstraint(parent_groups, target, mo=True, n=node_name)[0]
cmds.setAttr(f'{space_switch_con}.interpType', 2)