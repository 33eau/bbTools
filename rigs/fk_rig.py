from importlib import reload
import maya.cmds as cmds
from ..core.utils import rig_utils as bb
from ..core.controllers import creator as bc
from ..core.controllers import shape_color
from ..core.data import constants 
from ..core.naming import namer_factory as naming
from ..core.naming import current_project
from ..core.naming import parser

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
				connection_type='parentScale',
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				rig_end_joints = True,
				shape_rotation = None,
				base_orient_loc = None,
				add_rig_jnt = False,
				bind_parent =None,
				ctrl_parent =None,
				mod_parent = None,
				**controller_kwargs
                ):
		self.joints = joints
		self.upper_driver =  upper_driver
		self.rig_name = rig_name
		self.element_name = element_name
		self.side = side
		self.stretch = stretch
		self.squash = squash
		self.offset_names = offset_names or ['zro', 'offset']
		self.shape =  shape
		self.aim_axis =  aim_axis
		self.up_axis =  up_axis
		self.color = color
		self.connection_type = connection_type
		self.stretch_attr =  stretch_attr
		self.squash_attr =  squash_attr
		self.controller_kwargs = controller_kwargs
		self.rig_end_joints =  rig_end_joints
		self.ctrl_parent =  ctrl_parent
		self.shape_rotation = shape_rotation
		self.base_orient_loc =  base_orient_loc
		self.add_rig_jnt =  add_rig_jnt
		self.bind_parent =  bind_parent
		self.mod_parent =  mod_parent

		if not joints or not isinstance(joints, list) or len(joints) < 2:
			raise ValueError("The 'joints' argument must be a list of at least two joint names.")

		
		self.ctrl_grp = None

		self.ctrls, self.grps = self._build()

	def _build(self):

		if self.add_rig_jnt:
			joints = bb.duplicate_joint_chain(self.joints, remove_element=['tmp', 'temp'], add_elements=[self.element_name, 'bnd'])
			self.joints = joints[self.element_name]
			self.bind_jnts = joints['bnd']
			cmds.parent(self.joints[0], self.mod_parent)
			if self.bind_parent:
				cmds.parent(self.bind_jnts[0], self.bind_parent)

		if self.rig_name:
			self.ctrl_grp = bb.create_node('group', self.rig_name, elements=[self.element_name, 'ctrl'], side = self.side, p=self.ctrl_parent)
			cmds.matchTransform(self.ctrl_grp, self.joints[0])

		main_ctrl_grp = self.ctrl_grp if self.rig_name else None

		rig_joints = self.joints[:-1] if not self.rig_end_joints else self.joints

		fk_rig = bc.Controller(objects = rig_joints, 
						main_ctrl_grp = main_ctrl_grp, 
						offset_names = self.offset_names, 
						upper_driver = self.upper_driver,
						shape = self.shape, 
						color = self.color, 
						connection_type =self.connection_type,
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

		if self.add_rig_jnt:
			for rig, bind in zip(self.joints, self.bind_jnts):
				if self.connection_type == 'matrix_parent':
					bb.matrix_constrain(rig, bind)
				else:
					bb.create_constrain([rig], bind, 'pac')

		return self.ctrls, self.grps

	
	def _do_stretch_and_squash(self):
		"""Creates the stretch/squash setup for the FK chain."""
		aim_attr_idx = bb.axis_convert(self.aim_axis, 'index')
		aim_axis_str = bb.axis_convert(self.aim_axis, 'absolute_letter')

		stretch_grps = []
		for i, ctrl in enumerate(self.ctrls):
			base, element, number, side, _ = NAMER.extract(ctrl)
			if not self.rig_end_joints:
				if i < len(self.ctrls) - 1:
					stretch_grp = bb.create_offset_group(self.grps[i+1][0], ['stretch'], remove_elem = ['zro'])
					stretch_grp = stretch_grp[self.grps[i+1][0]][0]
				else:
					base, element, number, side, _ = NAMER.extract(self.joints[-1])
					temp_obj = bb.create_node('locator', base, element + [self.stretch_attr], number, side)
					bb.snap([self.joints[-1]], temp_obj)
					stretch_grp = bb.create_offset_group(temp_obj , ['stretch'], remove_elem = ['zro'])
					stretch_grp = stretch_grp[temp_obj][0]
					cmds.parent(stretch_grp, ctrl)
					cmds.delete(temp_obj)
					#bb.create_constrain([stretch_grp], self.joints[-1], self.connection_type)
			else:
				if i == len(self.ctrls)-1:
					break
				stretch_grp = bb.create_offset_group(self.grps[i+1][0], ['stretch'], remove_elem = ['zro'])
				stretch_grp = stretch_grp[self.grps[i+1][0]][0]

			stretch_grps.append(stretch_grp)
			bb.attr_separator(ctrl)
			cmds.addAttr(ctrl, ln = self.stretch_attr, at='float', k=True)		
			orig_posi = cmds.xform(stretch_grp, q=True, t=True, os = True, r=True)
			orig_posi = cmds.getAttr(f'{stretch_grp}.t{aim_axis_str}')

			orig_posi_adl = bb.create_node('addDoubleLinear', self.rig_name, ['add', 'posi'], number, side)
			cmds.setAttr( f'{orig_posi_adl}.i1', orig_posi)
			cmds.connectAttr(f'{ctrl}.{self.stretch_attr}', f'{orig_posi_adl}.i2')
			
			add_posi = cmds.getAttr(f'{orig_posi_adl}.o')
			if abs(add_posi) == abs(orig_posi):
				cmds.connectAttr(f'{orig_posi_adl}.o', f'{stretch_grp}.t{aim_axis_str}')
			else:
				print(f'New position not match ADD: {add_posi}, ORIG: {orig_posi}')

			if self.squash: 
				cmds.addAttr( ctrl, ln = self.squash_attr, at = 'float', min=0, max=1, dv = 0.0, k = True )
				
				dist_perc_mdv = bb.create_node('multiplyDivide', base, element + [self.squash_attr, 'dist', 'perc'], number, side )
				cmds.setAttr( f'{dist_perc_mdv}.i2x', orig_posi)
				cmds.connectAttr(f'{orig_posi_adl}.o', f'{dist_perc_mdv}.i1x')
				cmds.setAttr(f'{dist_perc_mdv}.op', 2 )
				
				power_mdv = bb.create_node('multiplyDivide', base, element + [self.squash_attr, 'power'], number=number, side=side, )
				cmds.connectAttr(f'{dist_perc_mdv}.ox', f'{power_mdv}.i1x')
				cmds.setAttr( f'{power_mdv}.i2x', 0.5)
				cmds.setAttr(f'{power_mdv}.op', 3 )

				one_div_mdv = bb.create_node('multiplyDivide', base, element + [self.squash_attr, 'one', 'div'], number, side)
				cmds.setAttr( f'{one_div_mdv}.i1x', 1)
				cmds.connectAttr(f'{power_mdv}.ox', f'{one_div_mdv}.i2x')
				cmds.setAttr(f'{one_div_mdv}.op', 2 )

				switch_bcl = bb.create_node('blendColors', base, element, number, side)
				cmds.connectAttr(f'{ctrl}.{self.squash_attr}', f'{switch_bcl}.blender')
				cmds.connectAttr(f'{one_div_mdv}.ox', f'{switch_bcl}.c1r')
				cmds.setAttr( f'{switch_bcl}.c2r', 1)

				scale_attr_mdv = bb.create_node('multiplyDivide', base, [self.squash_attr, 'scale'], number, side)
				cmds.connectAttr(f'{ctrl}.s', f'{scale_attr_mdv}.i1')			

				for axis in 'xyz':
					cmds.connectAttr(f'{switch_bcl}.opr', f'{scale_attr_mdv}.i2{axis}', f=True)
					cmds.connectAttr(f'{scale_attr_mdv}.o{axis}', f'{self.joints[i]}.s{axis}')

		self.end_grp = stretch_grps[-1]

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


