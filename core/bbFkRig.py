from importlib import reload
import maya.cmds as cmds
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

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

class FKRig:
	def __init__(self, 
				joints=None,
				rig_name=None,
				element_name='fk',
				side=None,
				stretch=False,
				squash=False,
				aim_axis='x',
				offset_names=[],
				ctrl_shape='crossCircle',
				ctrl_color=None,
				connection_type='parent',
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				**controller_kwargs
                ):
		self.joints = joints
		self.rig_name = rig_name
		self.element_name = element_name
		self.stretch = stretch
		self.squash = squash
		self.offset_names = offset_names
		self.ctrl_shape =  ctrl_shape
		self.aim_axis =  aim_axis
		self.connection_type = connection_type
		self.stretch_attr =  stretch_attr
		self.squash_attr =  squash_attr
		self.controller_kwargs = controller_kwargs
		self.controller_group = None

		if not joints or not isinstance(joints, list) or len(joints) < 2:
			raise ValueError("The 'joints' argument must be a list of at least two joint names.")

		if side is None:
			side = parser.find_element(self.joints[0], 'sides')
			self.side = side if side else 'M'
		else:
			self.side = side
		
		if ctrl_color is None:
			formatted_side = parser.format_side(self.side, 'upper')
			color = constants.CTRL_COLOR.get(formatted_side, [0,5, 0.5, 0.5])
			self.ctrl_color = color
		else: 
			self.ctrl_color =  ctrl_color 



		self.fk_ctrls, self.fk_groups = self._build()

	def _build(self):
		self.controller_group = bb.create_node('group', self.rig_name, elements=[self.element_name, 'ctrl'], side = self.side)
		fk_rig = bc.Controller(objects = self.joints[:-1], 
						main_ctrl_grp = self.controller_group, 
						name = self.rig_name, 
						side = self.side, 
						offset_names = self.offset_names, 
						shape = self.ctrl_shape, 
						color = self.ctrl_color, 
						connection_type = self.connection_type ,
						fk_chain = True , 
						**self.controller_kwargs)
						
		fk_ctrls = fk_rig.ctrls
		fk_groups = fk_rig.top_grps

		base, _, number, _, _ = NAMER.extract(self.joints[-1])
		tip_ctrl_grp = bb.create_node(node_type='group', base=base, elements=[self.element_name, 'tip'], number=number, side = self.side)
		cmds.matchTransform(tip_ctrl_grp, self.joints[-1])
		cmds.parent(tip_ctrl_grp, fk_ctrls[-1])
		bb.create_constrain([tip_ctrl_grp], self.joints[-1], self.connection_type)
		fk_groups.append([tip_ctrl_grp])

		if self.stretch:
			self._do_stretch_and_squash(fk_ctrls, fk_groups)

		return fk_ctrls, fk_groups
	
	def _do_stretch_and_squash(self, fk_ctrls, fk_groups):
		"""Creates the stretch/squash setup for the FK chain."""
		stretch_attr_name = self.stretch_attr
		squash_attr_name = self.squash_attr

		for i, ctrl in enumerate(fk_ctrls):
			stretch_grp = fk_groups[i+1][0]
			number = parser.find_number(ctrl)
			original_posi = cmds.getAttr(f'{self.joints[i+1]}.t{self.aim_axis}')

			cmds.addAttr( ctrl, ln = stretch_attr_name, at = 'float', dv = 0.0, k = True )

			attr_mdl = bb.create_node('multDoubleLinear', self.rig_name, [self.element_name], number, side = self.side)
			original_add_posi_adl = bb.create_node('addDoubleLinear', self.rig_name, [self.element_name], number, side = self.side)

			cmds.setAttr( f'{attr_mdl}.i2', original_posi)
			cmds.setAttr( f'{original_add_posi_adl}.i2', original_posi)

			cmds.connectAttr(f'{ctrl}.{stretch_attr_name}', f'{attr_mdl}.i1')
			cmds.connectAttr(f'{attr_mdl}.o', f'{original_add_posi_adl}.i1')
			cmds.connectAttr(f'{original_add_posi_adl}.o', f'{stretch_grp}.t{self.aim_axis}')

			if self.squash:
				cmds.addAttr( ctrl, ln = squash_attr_name, at = 'float', min=0, max=1, dv = 0.0, k = True )
				
				dist_perc_mdv = bb.create_node(node_type='multiplyDivide', base=self.rig_name, elements=[self.element_name, 'dist', 'perc'], number=number, side=self.side )
				cmds.setAttr( f'{dist_perc_mdv}.i2x', original_posi)
				cmds.connectAttr(f'{original_add_posi_adl}.o', f'{dist_perc_mdv}.i1x')
				cmds.setAttr(f'{dist_perc_mdv}.op', 2 )
				
				power_mdv = bb.create_node(node_type='multiplyDivide', base=self.rig_name, elements=[self.element_name, 'power'], number=number, side=self.side, )
				cmds.connectAttr(f'{dist_perc_mdv}.ox', f'{power_mdv}.i1x')
				cmds.setAttr( f'{power_mdv}.i2x', 0.5)
				cmds.setAttr(f'{power_mdv}.op', 3 )

				one_div_mdv = bb.create_node(node_type='multiplyDivide', base=self.rig_name, elements=[self.element_name, 'one', 'div'], number=number, side=self.side )
				cmds.setAttr( f'{one_div_mdv}.i1x', 1)
				cmds.connectAttr(f'{power_mdv}.ox', f'{one_div_mdv}.i2x')
				cmds.setAttr(f'{one_div_mdv}.op', 2 )

				switch_bcl = bb.create_node(node_type='blendColors', base=self.rig_name, elements=[self.element_name], number=number, side=self.side )
				cmds.connectAttr(f'{ctrl}.{squash_attr_name}', f'{switch_bcl}.blender')
				cmds.connectAttr(f'{one_div_mdv}.ox', f'{switch_bcl}.c1r')
				cmds.setAttr( f'{switch_bcl}.c2r', 1)
				for axis in 'xyz':
					cmds.connectAttr(f'{switch_bcl}.opr', f'{self.joints[i]}.s{axis}', f=True)
					print(i)
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
# 				ctrl_shape = 'crossCircle',
# 				ctrl_color = 'pink',
# 				connection_type = 'parent',
# 				scale = 10,
# 				shape_rotation = [0, 0, 90]
# 				)


