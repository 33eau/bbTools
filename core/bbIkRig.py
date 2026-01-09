import maya.cmds as cmds
from importlib import reload
from .utils import rig_utils as bb
from .controllers import creator as bc
from .data import constants as constants
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

class IkRig:
	def __init__(self,
				joints = None,
				pole_vector_jnt = None,
				end_rotation_jnts = [],
				rig_name = 'leg',
				side = None,
				element_name = 'ik',
				stretch = True,
				squash = True,
				aim_axis = 'x',
				up_axis = 'z',
				offset_names = ['zro', 'offset'],
				ctrl_shape = 'cube',
				ctrl_color = 'blue',
				connection_type = 'parent',
				scale = 1,
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				global_scale = '',
				base_orient_loc = None,
				end_orient_loc = None,
				world_space = None,
				ctrl_parent =None,
				mod_parent = None,
				upper_driver = None,
				default_ik_base = 0,
				default_ik_pv = 1,
				default_ik_end = 0,
				base_parent_type = 'orient',
				**controller_kwargs
				):
		self.joints =  joints
		self.end_rotation_jnts =  end_rotation_jnts
		self.pole_vector_jnt =  pole_vector_jnt
		self.rig_name =  rig_name
		self.element_name =  element_name
		self.stretch =  stretch
		self.squash =  squash
		self.aim_axis =  aim_axis
		self.up_axis =  up_axis
		self.offset_names =  offset_names
		self.ctrl_shape =  ctrl_shape
		self.color =  ctrl_color
		self.connection_type =  connection_type
		self.scale =  scale
		self.stretch_attr =  stretch_attr
		self.squash_attr =  squash_attr
		self.global_scale =  global_scale
		self.controller_kwargs =  controller_kwargs
		self.base_orient_loc =  base_orient_loc
		self.end_orient_loc =  end_orient_loc
		self.world_space =  world_space
		self.ctrl_parent =  ctrl_parent
		self.mod_parent =  mod_parent
		self.upper_driver =  upper_driver
		self.default_ik_base =  default_ik_base
		self.default_ik_pv =  default_ik_pv
		self.default_ik_end =  default_ik_end
		self.base_parent_type =  base_parent_type

		self.number = parser.find_number(self.rig_name)
		if side is None :
			self.side = parser.find_element(joints[0], 'sides')
		else:
			self.side =  side
		
		self.ctrl_grp = None
		self.mod_grp = None
		self.ctrls = None

		self._build()
		#bb.over_and_out('IkRig', self.rig_name)

	def _build(self):
		base_names =[]
		joint_positions = []
		for jnt in self.joints:
			posi = cmds.xform(jnt, ws=True, q=True, t=True)
			joint_positions.append(posi)
			base_name = parser.get_base_name(jnt)
			base_names.append(base_name)
		
		self.ctrl_grp = bb.create_node('group', base=self.rig_name, elements=[self.element_name, 'ctrl'], side=self.side, p=self.ctrl_parent)
		self.mod_grp = bb.create_node('group', base=self.rig_name, elements=[self.element_name, 'mod'], side=self.side, p=self.mod_parent)
		self.pivot_mod_grp = bb.create_node('group', base=self.rig_name, elements=[self.element_name, 'pivot', 'mod'], side=self.side, p=self.mod_grp)
		cmds.matchTransform(self.pivot_mod_grp, self.joints[-1])

		node_name = NAMER.format(self.rig_name, [self.element_name], self.number, self.side, 'ikh')
		ikh, eff = cmds.ikHandle(sj=self.joints[0], ee=self.joints[-1], n = node_name, sol='ikRPsolver' )

		node_name = NAMER.format(self.rig_name, [self.element_name], self.number, self.side, 'eff')
		cmds.rename(eff, node_name)
		cmds.parent(ikh, self.pivot_mod_grp)

		ik_base_controller = bc.Controller(objects = [self.joints[0]],
					side = self.side,
					offset_names = self.offset_names,
					main_ctrl_grp = self.ctrl_grp,
					shape = self.ctrl_shape,
					color = self.color,
					connection_type = self.connection_type,
					rotate_order = 'xyz',
					shape_rotation = [0, 0, -90],
					name_template=NAME_TEMPLATE,
					side_case='lower',
					scale = self.scale,
					** self.controller_kwargs
					)
		self.ik_base_ctrl = ik_base_controller.ctrls[0]
		ik_base_grp = ik_base_controller.offset_grps[0]

		bb.add_enum_space_switch( [self.upper_driver], world_space=self.world_space, attr_name='follow', spaces_name=['world', 'local'], target = ik_base_grp[0], ctrl= self.ik_base_ctrl, type = self.base_parent_type, default_index=self.default_ik_base)	

		ikh_end_controller = bc.Controller(objects = [ikh],
					name=self.rig_name+'_ik',
					side = self.side,
					offset_names = ['zro', 'space', 'offset'],
					main_ctrl_grp = self.ctrl_grp,
					shape = self.ctrl_shape,
					color = self.color,
					connection_type = 'None',
					rotate_order = 'xyz',
					name_template=NAME_TEMPLATE,
					side_case='lower',
					scale = self.scale,
					** self.controller_kwargs
					)
		self.ik_end_ctrl = ikh_end_controller.ctrls[0]
		ik_end_grps = ikh_end_controller.offset_grps[0]

		# ————————————————————————————————————————————————————
		##################### Base Orient #####################
		if self.base_orient_loc is None:
			base_orient_loc = bb.create_node('locator', self.rig_name, ['end', 'orient'], None, self.side)
			bb.snap([self.joints[0]], base_orient_loc)
			bb.snap([base_orient_loc], ik_base_grp[0])
			cmds.delete(base_orient_loc)
		else:
			bb.snap([self.base_orient_loc], ik_base_grp[0])

		##################### End Orient #####################
		if self.end_orient_loc is None:
			end_orient_loc = bb.create_node('locator', self.rig_name, ['end', 'orient'], None, self.side)
			bb.snap([self.joints[-1]], end_orient_loc)
			bb.snap([end_orient_loc], ik_end_grps[0])
			cmds.delete(end_orient_loc)
		else:
			bb.snap([self.end_orient_loc], ik_end_grps[0])
		# ————————————————————————————————————————————————————

		bb.add_enum_space_switch(parent_spaces = [self.upper_driver], world_space=self.world_space, attr_name='follow', spaces_name=['world', 'local'], target = ik_end_grps[1], ctrl=self.ik_end_ctrl, type = 'parent', default_index= self.default_ik_end)
		#bb.create_constrain([self.ik_end_ctrl], ikh, 'point')
		node_name = NAMER.format(self.rig_name, ['pv'], self.number, self.side, 'loc')

		# ————————————————————————————————————————————————————
		##################### End Rotation #####################
		if self.end_rotation_jnts:
			end_rot_ikhs = []
			cmds.parent(self.end_rotation_jnts[1:], self.joints[-1])
			for i in range(0, len(self.end_rotation_jnts[:1])):
				base_jnt = self.joints[-1]
				end_jnt = self.end_rotation_jnts[i+1]
				base, element, number, side, suffix = NAMER.extract(end_jnt)
				end_rot_ikh, eff = bb.create_node('ikRp', base, [self.element_name], self.number, self.side, sj=base_jnt, ee=end_jnt)
				if len(end_rot_ikhs) > 0:
					cmds.parent(end_rot_ikh, end_rot_ikhs[-1])
				else:
					bb.create_constrain([self.ik_end_ctrl], end_rot_ikh, 'parent')
					cmds.parent(end_rot_ikh, self.mod_grp)
		# ————————————————————————————————————————————————————

		ik_pv_controller = bc.Controller(objects = [self.pole_vector_jnt],
								offset_names = ['zro', 'space', 'Offset'],
								main_ctrl_grp = self.ctrl_grp,
								shape = 'diamond',
								color = self.color,
								connection_type = 'None',
								rotate_order = 'xyz',
								shape_rotation = [0, 0, 0],
								name_template=NAME_TEMPLATE,
								side_case='lower',
								scale=self.scale * 0.4,
								lock_attrs=['rx', 'ry', 'rz', 'sx', 'sy', 'sz']
								)
		self.ik_pv_ctrl = ik_pv_controller.ctrls[0]
		self.ik_pv_grp = ik_pv_controller.offset_grps
		pv_space_grp = ik_pv_controller.offset_grps[0][1]
		node_name = NAMER.format(self.rig_name, ['pv'], self.number, self.side, 'pvc')
		cmds.poleVectorConstraint(self.ik_pv_ctrl, ikh, n=node_name)
		bb.create_guide_curve(self.ik_pv_ctrl, self.joints[1], parent=self.ctrl_grp, curve_elem='pv')
		bb.add_enum_space_switch( [self.ik_base_ctrl, self.ik_end_ctrl] , world_space=self.world_space, attr_name='follow', spaces_name=['world', 'base', 'end'], target = self.ik_pv_grp[0][1], ctrl= self.ik_pv_ctrl, type = 'parent', default_index=self.default_ik_pv)	
		self.ctrls = [self.ik_base_ctrl, self.ik_pv_ctrl, self.ik_end_ctrl]

		if self.stretch:
			self.do_strech()
		
	def do_strech(self):
		ctrls = [self.ik_base_ctrl, self.ik_end_ctrl]
		position_locators = []
		for i, point in enumerate(['start', 'end']):
			loc = bb.create_node( node_type='locator', base=self.rig_name, elements=[self.stretch_attr, point], number=self.number, side=self.side, namer=NAMER)
			cmds.matchTransform(loc, ctrls[i])
			cmds.hide(loc)
			position_locators.append(loc)

		base_loc = position_locators[0]
		end_loc = position_locators[1]
		cmds.parent(base_loc, self.mod_grp)
		cmds.parent(end_loc, self.pivot_mod_grp)
		bb.create_constrain( parents=[self.ik_base_ctrl], target=base_loc, type="parent")
		bb.create_constrain( parents=[self.ik_end_ctrl], target=self.pivot_mod_grp, type="parent")
				
		real_time_distant_dbt = bb.create_node( node_type='distanceBetween', base=self.rig_name, elements=[self.stretch_attr], number=self.number, side=self.side, namer=NAMER)
		cmds.connectAttr(f'{base_loc}.worldPosition[0]',  f'{real_time_distant_dbt}.p1')
		cmds.connectAttr(f'{end_loc}.worldPosition[0]',  f'{real_time_distant_dbt}.p2')

		aim_attr = bb.axis_convert(self.aim_axis, 'absolute_letter')
		total_len = 0
		for jnt in self.joints[1:]:
			jnt_len = cmds.getAttr(f'{jnt}.t{aim_attr}')
			total_len += abs(jnt_len)

		global_scale_mdl = bb.create_node('multDoubleLinear', self.rig_name, ['global', 'scale'], self.number, self.side)
		cmds.setAttr( f'{global_scale_mdl}.i1', total_len )
		cmds.connectAttr(self.global_scale, f'{global_scale_mdl}.i2')
		for ax in 'xyz':
			cmds.connectAttr(self.global_scale, f'{self.ctrl_grp}.s{ax}')

		dist_perc_mdv = bb.create_node( node_type='multiplyDivide', base=self.rig_name, elements=['dist', 'perc'], number=self.number, side=self.side, namer=NAMER)
		cmds.connectAttr(f'{real_time_distant_dbt}.distance', f'{dist_perc_mdv}.i1x')
		cmds.connectAttr(f'{global_scale_mdl}.o', f'{dist_perc_mdv}.i2x')
		cmds.setAttr(f'{dist_perc_mdv}.op', 2 )

		attr_name = 'auto' + self.stretch_attr.capitalize()
		mannual_attr = 'mannual' + self.stretch_attr.capitalize()
		bb.attr_separator(self.ik_end_ctrl, ln='extraAttr')
		cmds.addAttr( self.ik_end_ctrl, ln = attr_name, at = 'double', min = 0, max = 1, dv = 1, k = True )
		cmds.addAttr( self.ik_end_ctrl, ln = mannual_attr, at = 'float', min = -1, max = 10, dv = 1, k = True )

		feature_switch = bb.create_node( node_type='blendColors', base=self.rig_name, elements=[self.stretch_attr], number=self.number, side=self.side, namer=NAMER)
		cmds.connectAttr(f'{self.ik_end_ctrl}.{attr_name}', f'{feature_switch}.blender')
		cmds.connectAttr(f'{dist_perc_mdv}.ox', f'{feature_switch}.c1r')
		cmds.setAttr( f'{feature_switch}.c2', 1,1,1 )

		mannual_mdl = bb.create_node( node_type='multDoubleLinear', base=self.rig_name, elements=[self.stretch_attr], number=self.number, side=self.side, namer=NAMER)
		cmds.connectAttr(f'{self.ik_end_ctrl}.{mannual_attr}', f'{mannual_mdl}.i2')
		cmds.connectAttr(f'{feature_switch}.opr', f'{mannual_mdl}.i1')

		bend_cdt = bb.create_node( node_type='condition', base=self.rig_name, elements=[self.stretch_attr], number=self.number, side=self.side, namer=NAMER)
		cmds.connectAttr(f'{real_time_distant_dbt}.distance', f'{bend_cdt}.ft')
		cmds.connectAttr(f'{global_scale_mdl}.o', f'{bend_cdt}.st')
		cmds.setAttr(f'{bend_cdt}.op', 2 )
		cmds.connectAttr(f'{mannual_mdl}.o', f'{bend_cdt}.ctr')
		cmds.connectAttr(f'{self.ik_end_ctrl}.{mannual_attr}', f'{bend_cdt}.cfr')

		for jnt in self.joints[1:]:
			base_name = parser.get_base_name(jnt)
			original_posi = cmds.getAttr(f'{jnt}.t{aim_attr}')
			original_posi_mdl = bb.create_node(node_type='multDoubleLinear', base=base_name, elements=[self.stretch_attr], number=self.number, side=self.side)
			cmds.setAttr( f'{original_posi_mdl}.i1', original_posi)
			cmds.connectAttr(f'{bend_cdt}.ocr', f'{original_posi_mdl}.i2')
			joint_global_scale_mdl = bb.create_node('multDoubleLinear', base_name, ['global', 'scale'], self.number, self.side)
			cmds.connectAttr(f'{original_posi_mdl}.o', f'{joint_global_scale_mdl}.i1')
			cmds.connectAttr(f'{self.global_scale}', f'{joint_global_scale_mdl}.i2')
			cmds.connectAttr(f'{joint_global_scale_mdl}.o', f'{jnt}.t{aim_attr}')

		if self.squash:
			power_mdv = bb.create_node( node_type='multiplyDivide', base=self.rig_name, elements=[self.squash_attr, 'power'], number=self.number, side=self.side, namer=NAMER)
			cmds.setAttr(f'{power_mdv}.op', 3 )
			cmds.setAttr( f'{power_mdv}.i2x', 0.5)

			bend_output_abs = bb.create_node('absolute', self.rig_name, [self.squash_attr, 'abs'], self.number, self.side)
			cmds.connectAttr(f'{bend_cdt}.ocr', f'{bend_output_abs}.input')
			cmds.connectAttr(f'{bend_output_abs}.output', f'{power_mdv}.i1x')

			one_div_mdv = bb.create_node( node_type='multiplyDivide', base=self.rig_name, elements=[self.squash_attr, 'one', 'div'], number=self.number, side=self.side, namer=NAMER)
			cmds.setAttr( f'{one_div_mdv}.i1x', 1)
			cmds.setAttr(f'{one_div_mdv}.op', 2 )
			cmds.connectAttr(f'{power_mdv}.ox', f'{one_div_mdv}.i2x')

			attr_name = 'auto' + self.squash_attr.capitalize()
			cmds.addAttr( self.ik_end_ctrl, ln = attr_name, at = 'float', min = 0, dv = 1, k = True )

			sq_switch = bb.create_node( node_type='blendColors', base=self.rig_name, elements=[self.squash_attr], number=self.number, side=self.side, namer=NAMER)
			cmds.connectAttr(f'{self.ik_end_ctrl}.{attr_name}', f'{sq_switch}.blender')
			cmds.connectAttr(f'{one_div_mdv}.ox', f'{sq_switch}.c1r')
			cmds.setAttr( f'{sq_switch}.c2r', 1)
			cmds.setAttr( f'{sq_switch}.c2', 1,1,1 )

			scale_axes = 'xyz'.replace(self.aim_axis, '')
			for jnt in self.joints:
				for ax in scale_axes: 
					cmds.connectAttr(f'{sq_switch}.opr', f'{jnt}.s{ax}')

		# elbow_lock
		point_names = ['upper', 'lower', 'end']
		feature_lock = 'lock'

		loc_lock_grp = bb.create_node('group', self.rig_name, [feature_lock], None, self.side, p=self.mod_grp)
		cmds.setAttr(f'{loc_lock_grp}.v', 0)
		cmds.addAttr( self.ik_pv_ctrl, ln = feature_lock, at ='float' , min = 0, max = 1, dv = 0, k = True )
		point_locs = []
		distance_nodes = []
		for i, point in enumerate (point_names):
			point_loc = bb.create_node('locator', self.rig_name, [point, feature_lock], self.number, self.side)
			cmds.parent(point_loc, loc_lock_grp)
			#bb.create_constrain([self.ctrls[i]], point_loc, type='pac', maintain_offset=False)
			point_locs.append(point_loc)
			bb.snap([self.joints[i]], point_loc)

			if len(point_locs) > 1:
				len_dtb = bb.create_node('distanceBetween', self.rig_name, [point], self.number, self.side)
				cmds.connectAttr(f'{point_locs[i]}.worldPosition[0]', f'{len_dtb}.point1')
				cmds.connectAttr(f'{point_locs[i-1]}.worldPosition[0]', f'{len_dtb}.point2')
				distance_nodes.append(len_dtb)

		upper_lock_loc, lower_lock_loc, end_lock_loc = point_locs
		lock_switch_bcl = bb.create_node('blendColors', self.rig_name, [feature_lock], self.number, self.side)
		cmds.setAttr( f'{lock_switch_bcl}.c2', 1,1,1 )
		cmds.connectAttr(f'{self.ik_pv_ctrl}.{feature_lock}', f'{lock_switch_bcl}.blender')
		lock_channels = 'rg'

		lock_perc_mdv = bb.create_node('multiplyDivide', self.rig_name, [feature_lock], self.number, self.side)
		cmds.setAttr(f'{lock_perc_mdv}.op', 2 )

		for i, channel in enumerate('xy'):
			distance_abs = bb.create_node('absolute', self.rig_name, [point_names[i+1], 'abs'], self.number, self.side)
			cmds.connectAttr(f'{distance_nodes[i]}.distance', f'{distance_abs}.i')
			cmds.connectAttr(f'{distance_abs}.o', f'{lock_perc_mdv}.i2{channel}')

			cmds.connectAttr(f'{distance_nodes[i]}.distance', f'{lock_perc_mdv}.i1{channel}')
			cmds.connectAttr(f'{lock_perc_mdv}.o{channel}', f'{lock_switch_bcl}.c1{lock_channels[i]}')
			cmds.connectAttr(f'{lock_switch_bcl}.op{lock_channels[i]}', f'{self.joints[i]}.s{aim_attr}', f=True)
	
		for i, ctrl in enumerate(self.ctrls):
			bb.create_constrain([ctrl], point_locs[i], type='pac', maintain_offset=False)


### Example use:
# path = r'W:/RIG/PROJ/MAYA_PROJ/JINXIE/scenes/RIG_JINXIE_tmp_jnt.ma'
# cmds.file(path, open=True, f=True)
# from bbTools.core.controllers import creator as bc
# from bbTools.core import bbIkRig
# reload(bbIkRig)
# reload(bc)
# CHARACTER_SCALE = 3
# super_rig = bc.SuperRoot(ctrl_scale=CHARACTER_SCALE)
# ik_rig = bbIkRig.IkRig( joints = ['l_shoulder_tmp_jnt', 'l_elbow_tmp_jnt', 'l_wrist_tmp_jnt'],
# 				rig_name = 'arm',
# 				element_name = 'ik',
# 				stretch = True,
# 				squash = True,
# 				aim_axis = 'x',
# 				up_axis = 'y',
# 				ctrl_shape = 'cube',
# 				ctrl_color = 'blue',
# 				connection_type = 'parent',
# 				scale = 1,
# 				stretch_attr = 'stretch',
# 				squash_attr = 'squash',
# 				global_scale = super_rig.scale_uniform,
# 				base_orient_loc = 'shoulder_orientation_loc',
# 				end_orient_loc = 'wrist_orientation_loc',
# 				world_space = super_rig.placement_ctrl,
# 				ctrl_parent =super_rig.ctrl_grp,
# 				mod_parent = super_rig.mod_grp,
# 				)