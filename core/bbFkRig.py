from importlib import reload
import maya.cmds as cmds
from .utils import rig_utils as bb
from .controllers import creator as bc
from .controllers import shape_color
from .data import constants 
from .naming import namer_factory as naming
from .naming import current_project
from .naming import parser

reload(bb )
reload(bc)
reload(constants)
reload(shape_color)
reload(naming)
reload(current_project)
reload(parser)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

class FKRig:
	def __init__(self, 
				joints=None,
				upper_driver = None,
				rig_name=None,
				element_name='fk',
				side=None,
				stretch=False,
				squash=False,
				aim_axis='x',
				up_axis = 'y',
				offset_names=None,
				shape='crossCircle',
				color=None,
				connection_type='parent',
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				rig_end_joint = True,
				ctrl_parent =None,
				shape_rotation = None,
				base_orient_loc = None,
				**controller_kwargs
                ):
		self.joints = joints
		self.upper_driver =  upper_driver
		self.rig_name = rig_name
		self.element_name = element_name
		self.stretch = stretch
		self.squash = squash
		self.offset_names = offset_names or ['zro', 'offset']
		self.shape =  shape
		self.aim_axis =  aim_axis
		self.up_axis =  up_axis
		self.connection_type = connection_type
		self.stretch_attr =  stretch_attr
		self.squash_attr =  squash_attr
		self.controller_kwargs = controller_kwargs
		self.rig_end_joint =  rig_end_joint
		self.ctrl_parent =  ctrl_parent
		self.shape_rotation = shape_rotation
		self.base_orient_loc =  base_orient_loc

		if not joints or not isinstance(joints, list) or len(joints) < 2:
			raise ValueError("The 'joints' argument must be a list of at least two joint names.")

		if side is None:
			side = parser.find_element(self.joints[0], 'sides')
			self.side = side if side else 'M'
		else:
			self.side = side
		
		if color is None:
			formatted_side = parser.format_side(self.side, 'upper')
			color = shape_color.CTRL_COLOR.get(formatted_side, [0.5, 0.5, 0.5])
			self.color = color
		else: 
			self.color =  color 

		self.ctrl_grp = None
		self.ctrls = None
		self.grps = None

		self.ctrls, self.grps = self._build()

	def _build(self):
		if self.rig_name:
			self.ctrl_grp = bb.create_node('group', self.rig_name, elements=[self.element_name, 'ctrl'], side = self.side, p=self.ctrl_parent)
		main_ctrl_grp = self.ctrl_grp if self.rig_name else None
		if not self.rig_end_joint:
			self.rig_joints = self.joints[:-1]
		else:
			self.rig_joints = self.joints

		fk_rig = bc.Controller(objects = self.rig_joints, 
						main_ctrl_grp = main_ctrl_grp, 
						offset_names = self.offset_names, 
						upper_driver = self.upper_driver,
						shape = self.shape, 
						color = self.color, 
						connection_type = self.connection_type ,
						fk_chain = True , 
						shape_rotation = self.shape_rotation,
						**self.controller_kwargs
						)
						
		self.ctrls = fk_rig.ctrls
		self.grps = fk_rig.offset_grps
		if self.base_orient_loc:
			cmds.matchTransform(self.grps[0][0], self.base_orient_loc)

		if self.stretch:
			self._do_stretch_and_squash()

		return self.ctrls, self.grps
	
	def _do_stretch_and_squash(self):
		"""Creates the stretch/squash setup for the FK chain."""
		stretch_attr_name = self.stretch_attr
		squash_attr_name = self.squash_attr
		aim_attr = bb.axis_convert(self.aim_axis, 'absolute_letter')

		if not self.rig_end_joint:
			base, element, number, side, suffix = NAMER.extract(self.rig_joints[-1])
			self.end_grp = bb.create_node('group', base, element + [stretch_attr_name, 'tip'], number, side, p=self.ctrls[-1])
			cmds.matchTransform(self.end_grp, self.joints[-1])
			self.grps.append([self.end_grp])
			bb.create_constrain([self.end_grp], self.joints[-1])
			stretch_ctrl = self.ctrls
		else:
			stretch_ctrl = self.ctrls[:-1]

		for i, ctrl in enumerate(stretch_ctrl):
			number = parser.find_number(ctrl)
			is_end_case = (i == len(stretch_ctrl)-1 and not self.rig_end_joint)

			if is_end_case:
				stretch_grp = self.grps[-1][0]
				orig_obj = self.grps[-1][0]
			else:
				idx = min(i + 1, len(self.rig_joints) - 1)
				stretch_grp = self.grps[idx][0]
				orig_obj = self.rig_joints[idx]

			original_posi = cmds.getAttr(f'{orig_obj}.t{aim_attr}')
					
			bb.attr_separator(ctrl, ln='extraAttr')
			cmds.addAttr( ctrl, ln = stretch_attr_name, at = 'float', dv = 0.0, k = True )

			base, element, number, side, _ = NAMER.extract(ctrl)
			attr_mdl = bb.create_node('multDoubleLinear', base, element + [ stretch_attr_name], number, side)
			original_add_posi_adl = bb.create_node('addDoubleLinear', base, element + [stretch_attr_name], number, side)

			cmds.setAttr( f'{attr_mdl}.i2', original_posi)
			cmds.setAttr( f'{original_add_posi_adl}.i2', original_posi)

			cmds.connectAttr(f'{ctrl}.{stretch_attr_name}', f'{attr_mdl}.i1')
			cmds.connectAttr(f'{attr_mdl}.o', f'{original_add_posi_adl}.i1')
			cmds.connectAttr(f'{original_add_posi_adl}.o', f'{stretch_grp}.t{aim_attr}')

			if self.squash:
				cmds.addAttr( ctrl, ln = squash_attr_name, at = 'float', min=0, max=1, dv = 0.0, k = True )
				
				dist_perc_mdv = bb.create_node('multiplyDivide', base, element + [squash_attr_name, 'dist', 'perc'], number, side )
				cmds.setAttr( f'{dist_perc_mdv}.i2x', original_posi)
				cmds.connectAttr(f'{original_add_posi_adl}.o', f'{dist_perc_mdv}.i1x')
				cmds.setAttr(f'{dist_perc_mdv}.op', 2 )
				
				power_mdv = bb.create_node('multiplyDivide', base, element + [squash_attr_name, 'power'], number=number, side=side, )
				cmds.connectAttr(f'{dist_perc_mdv}.ox', f'{power_mdv}.i1x')
				cmds.setAttr( f'{power_mdv}.i2x', 0.5)
				cmds.setAttr(f'{power_mdv}.op', 3 )

				one_div_mdv = bb.create_node('multiplyDivide', base, element + [squash_attr_name, 'one', 'div'], number, side)
				cmds.setAttr( f'{one_div_mdv}.i1x', 1)
				cmds.connectAttr(f'{power_mdv}.ox', f'{one_div_mdv}.i2x')
				cmds.setAttr(f'{one_div_mdv}.op', 2 )

				switch_bcl = bb.create_node('blendColors', base, element, number, side)
				cmds.connectAttr(f'{ctrl}.{squash_attr_name}', f'{switch_bcl}.blender')
				cmds.connectAttr(f'{one_div_mdv}.ox', f'{switch_bcl}.c1r')
				cmds.setAttr( f'{switch_bcl}.c2r', 1)
				for axis in 'xyz':
					cmds.connectAttr(f'{switch_bcl}.opr', f'{self.joints[i]}.s{axis}', f=True)
					if i == (len(self.joints)-2):
						cmds.connectAttr(f'{switch_bcl}.opr', f'{self.joints[-1]}.s{axis}', f=True)
	

# ## Example usage
# meep_rig = FKRig( 
# 				['meep_01_jnt', 'meep_02_jnt', 'meep_03_jnt', 'meep_04_jnt'],
# 				rig_name = 'meep',
# 				element_name = 'fk',
# 				side = None,
# 				stretch = True,
# 				squash = True,
# 				aim_axis = 'x',
# 				offset_names = ['offset'],
# 				shape = 'crossCircle',
# 				color = 'pink',
# 				connection_type = 'parent',
# 				scale = 10,
# 				shape_rotation = [0, 0, 90]
# 				)


