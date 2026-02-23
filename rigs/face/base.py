from importlib import reload
import maya.cmds as cmds
from ...core.utils import rig_utils as bb
from ...core.controllers import creator as bc
from ...core.controllers import shape_color
from ...core.naming import namer_factory as naming
from ...core.naming import current_project
from ...core.naming import parser

reload(bb)
reload(bc)
reload(shape_color)
reload(naming)
reload(current_project)
reload(parser)

class FaceModule(object):
	'''
		# 26Feb18
		# The parent class for all facial components.
	'''
	def __init__(self, 
				name='face', 
				side='M', 
				parent_ctrl_grp=None, 
				parent_mod_grp=None,
				remove_elem='bp'
			):

		self.name = name
		self.side = side
		self.parent_ctrl_grp = parent_ctrl_grp
		self.parent_mod_grp = parent_mod_grp
		self.remove_elem = remove_elem

		self.namer = naming.get_namer(current_project.PROJECT)

		self.ctrl_grp = None
		self.mod_grp = None
		self.jnt_grp = None
	
	def build(self):
		self.build_hierarchy(self.name, self.side)
		dead_jnt = bb.create_node('joint', self.name, ['dead'], None, None)
		cmds.parent(dead_jnt, self.jnt_grp)

	def build_hierarchy(self, name, side):
		'''
			Create structure for the module
		'''
		name = name if name else self.name
		side = side if side else self.side
		self.ctrl_grp = bb.create_node('group', name, ['ctrl'], None, side)
		if self.parent_ctrl_grp:
			cmds.parent(self.ctrl_grp, self.parent_ctrl_grp)

		self.mod_grp = bb.create_node('group', name, ['mod'], None, side)
		if self.parent_mod_grp:
			cmds.parent(self.mod_grp, self.parent_mod_grp)
		
		self.jnt_grp = bb.create_node('group', name, ['jnt'], None, side)
		cmds.parent(self.jnt_grp, self.mod_grp)

	def create_rig_joint(self, bp_jnt, offset_names=['jnt'], parent_jnt_grp=None, rad=0.25, remove_elem = 'bp', add_elem = None):
		base, element, number, side, suffix = self.namer.extract(bp_jnt)
		element = element if element else []
		element = element + [add_elem] if add_elem else element
		base_name = parser.clean_name(base, remove_elem)

		rig_jnt = bb.create_node('joint', base_name, element, number, side, rad = rad)
		grp_dict = bb.create_offset_group(rig_jnt, offset_names)
		grp = grp_dict[rig_jnt][0]

		bb.snap([bp_jnt], grp)

		if parent_jnt_grp:
			cmds.parent(grp, parent_jnt_grp)
		else:
			cmds.parent(grp, self.jnt_grp)
		
		return grp, rig_jnt
	
	def create_controller(self, obj, shape, scale, rotate, move, connection_type, 
					   offset_names=['ctrl'], color_set = 'sec', color_shade = 'default', **kwargs):
		
		# Auto detect side for colot if not provided
		side_for_color = parser.find_element(obj, 'sides')
		format_side = parser.format_side(side_for_color, 'upper') or 'M'

		if color_set == 'sec':
			side_color = shape_color.CTRL_SEC_COLOR[format_side]
		elif color_set == 'ter':
			side_color = shape_color.CTRL_TER_COLOR[format_side]
		elif color_set == 'grp':
			side_color = shape_color.CTRL_GRP_COLOR[format_side]
		else:
			side_color = shape_color.CTRL_COLOR[format_side]
		
		# Default to face ctrl grp if not provided
		target_main_grp = kwargs.pop('ctrl_grp', self.ctrl_grp)

		if color_shade == 'default':
			side_color = side_color
		else:
			try:
				side_color = color_shade + side_color.capitalize()
			except:
				print(f'Specific Color Shade cannot be found: "{color_shade}" [light, default, dark, deep]')
				side_color = side_color

		controller = bc.Controller(
			objects=[obj],
			main_ctrl_grp=target_main_grp,
			offset_names=offset_names,
			shape=shape,
			color=side_color,
			scale=scale,
			connection_type=connection_type,
			shape_rotation=rotate,
			move=move,
			clean_elem=self.remove_elem,

			**kwargs
		)
	
		return controller.offset_grps[0], controller.ctrls[0]


		

