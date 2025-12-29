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
				scale = 10,
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				global_scale = '',
				lock_attr = '',
				base_orient_loc = '',
				end_orient_loc = '',
				world_space = None,
				**controller_kwargs
				):
		self.joints =  joints
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

		self.number = parser.find_number(self.rig_name)
		if side is None :
			self.side = parser.find_element(joints[0], 'sides')

		self.ctrl_grp = None
		self.mod_grp = None
		self.ctrls = None

		self._build()
		bb.over_and_out('IkRig', self.rig_name)

	def _build(self):
		base_names =[]
		joint_positions = []
		for jnt in self.joints:
			posi = cmds.xform(jnt, ws=True, q=True, t=True)
			joint_positions.append(posi)
			base_name = parser.get_base_name(jnt)
			base_names.append(base_name)
		
		self.ctrl_grp = bb.create_node('group', base=self.rig_name, elements=[self.element_name, 'ctrl'], side=self.side)
		self.mod_grp = bb.create_node('group', base=self.rig_name, elements=[self.element_name, 'mod'], side=self.side)

		cmds.setAttr( f'{self.joints[1]}.preferredAngle{self.up_axis.capitalize()}', -90)

		node_name = NAMER.format(self.rig_name, ['ik'], self.number, self.side, 'ikh')
		ikh, eff = cmds.ikHandle(sj=self.joints[0], ee=self.joints[2], n = node_name)
		node_name = NAMER.format(self.rig_name, ['ik'], self.number, self.side, 'eff')
		cmds.rename(eff, node_name)
		cmds.parent(ikh, self.mod_grp)

		ikh_end_controller = bc.Controller(objects = [ikh],
					name=self.rig_name+'_ik',
					side = self.side,
					offset_names = self.offset_names,
					main_ctrl_grp = self.ctrl_grp,
					shape = self.ctrl_shape,
					color = self.color,
					connection_type = self.connection_type,
					rotate_order = 'xyz',
					name_template=NAME_TEMPLATE,
					side_case='lower',
					scale = self.scale,
					** self.controller_kwargs
					)
		self.ik_end_ctrl = ikh_end_controller.ctrls[0]
		ik_end_grp = ikh_end_controller.offset_grps[0][0]
		if self.base_orient_loc:
			bb.snap([self.end_orient_loc], ik_end_grp)

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
		ik_base_grp = ik_base_controller.offset_grps[0][0]
		if self.base_orient_loc:
			bb.snap([self.base_orient_loc], ik_base_grp)

		node_name = NAMER.format(self.rig_name, ['pv'], self.number, self.side, 'loc')
		pv_position_loc = bb.pole_vector_position(self.joints[:3], 0.5, create_locator=True)
		pv_position_loc = cmds.rename(pv_position_loc, node_name)

		ik_pv_controller = bc.Controller(objects = [pv_position_loc],
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
		pv_space_grp = ik_pv_controller.offset_grps[0][1]
		cmds.delete(pv_position_loc)
		node_name = NAMER.format(self.rig_name, ['pv'], self.number, self.side, 'pvc')
		cmds.poleVectorConstraint(self.ik_pv_ctrl, ikh, n=node_name)
		bb.add_enum_space_switch([self.ik_base_ctrl, self.ik_end_ctrl], world_space=self.world_space, attr_name='follow', spaces_name=['world', 'base', 'end'], target = pv_space_grp, ctrl=self.ik_pv_ctrl, type = 'parent', default_index=1)
		bb.create_guide_curve(self.ik_pv_ctrl, self.joints[1], parent=self.ctrl_grp, curve_elem='pv')

		self.ctrls = [self.ik_base_ctrl, self.ik_pv_ctrl, self.ik_end_ctrl]

		if self.stretch:
			self.do_strech()
		
	def do_strech(self):
		ctrls = [self.ik_base_ctrl, self.ik_end_ctrl]
		position_locators = []
		for i, point in enumerate(['start', 'end']):
			loc = bb.create_node( node_type='locator', base=self.rig_name, elements=[self.stretch_attr, point], number=self.number, side=self.side, namer=NAMER)
			cmds.matchTransform(loc, ctrls[i])
			# if NAME_TEMPLATE == 'hatrig':
			# 	cmds.parent(loc, ctrls[i])
			# else:
			bb.create_constrain( parents=[ctrls[i]], target=loc, type="parent")
			cmds.parent(loc, self.mod_grp)
			cmds.hide(loc)
			position_locators.append(loc)
		base_loc = position_locators[0]
		end_loc = position_locators[1]

		real_time_distant_dbt = bb.create_node( node_type='distanceBetween', base=self.rig_name, elements=[self.stretch_attr], number=self.number, side=self.side, namer=NAMER)
		cmds.connectAttr(f'{base_loc}.worldPosition[0]',  f'{real_time_distant_dbt}.p1')
		cmds.connectAttr(f'{end_loc}.worldPosition[0]',  f'{real_time_distant_dbt}.p2')
		distance = cmds.getAttr(f'{real_time_distant_dbt}.distance')

		upper_len = cmds.getAttr(f'{self.joints[1]}.t{self.aim_axis}')
		lower_len = cmds.getAttr(f'{self.joints[2]}.t{self.aim_axis}')
		total_len = upper_len+lower_len

		global_scale_mdl = bb.create_node('multDoubleLinear', self.rig_name, ['global', 'scale'], self.number, self.side)
		cmds.setAttr( f'{global_scale_mdl}.i1', total_len)
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


		# if NAME_TEMPLATE == 'hatrig':
		# 	for jnt in self.joints[:2]:
		# 		cmds.connectAttr(f'{bend_cdt}.ocr', f'{jnt}.s{self.aim_axis}')
		# else:
		for jnt in self.joints[1:3]:
			base_name = parser.get_base_name(jnt)
			original_posi = cmds.getAttr(f'{jnt}.t{self.aim_axis}')
			original_posi_mdl = bb.create_node(node_type='multDoubleLinear', base=base_name, elements=[self.stretch_attr], number=self.number, side=self.side)
			cmds.setAttr( f'{original_posi_mdl}.i1', original_posi)
			cmds.connectAttr(f'{bend_cdt}.ocr', f'{original_posi_mdl}.i2')
			joint_global_scale_mdl = bb.create_node('multDoubleLinear', base_name, ['global', 'scale'], self.number, self.side)
			cmds.connectAttr(f'{original_posi_mdl}.o', f'{joint_global_scale_mdl}.i1')
			cmds.connectAttr(f'{self.global_scale}', f'{joint_global_scale_mdl}.i2')
			cmds.connectAttr(f'{joint_global_scale_mdl}.o', f'{jnt}.t{self.aim_axis}')

		if self.squash:
			power_mdv = bb.create_node( node_type='multiplyDivide', base=self.rig_name, elements=[self.squash_attr, 'power'], number=self.number, side=self.side, namer=NAMER)
			cmds.setAttr(f'{power_mdv}.op', 3 )
			cmds.setAttr( f'{power_mdv}.i2x', 0.5)
			cmds.connectAttr(f'{bend_cdt}.ocr', f'{power_mdv}.i1x')

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

		cmds.addAttr( self.ik_pv_ctrl, ln = feature_lock, at ='float' , min = 0, max = 1, dv = 0, k = True )
		point_locs = []
		distance_nodes = []
		for i, point in enumerate (point_names):
			point_loc = bb.create_node('locator', self.rig_name, [point, feature_lock], self.number, self.side)
			cmds.parent(point_loc, self.mod_grp)
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
			init_len = cmds.getAttr(f'{distance_nodes[i]}.distance')
			cmds.setAttr( f'{lock_perc_mdv}.i2{channel}', init_len)
			cmds.connectAttr(f'{distance_nodes[i]}.distance', f'{lock_perc_mdv}.i1{channel}')
			cmds.connectAttr(f'{lock_perc_mdv}.o{channel}', f'{lock_switch_bcl}.c1{lock_channels[i]}')
			cmds.connectAttr(f'{lock_switch_bcl}.op{lock_channels[i]}', f'{self.joints[i]}.s{self.aim_axis}')
	
		for i, ctrl in enumerate(self.ctrls):
			bb.create_constrain([ctrl], point_locs[i], type='pac', maintain_offset=False)

# ik_rig = IkRig( joints = ['l_thigh_jnt', 'l_knee_jnt', 'l_ankle_jnt', 'l_ball_jnt'],
# 				rig_name = 'leg',
# 				element_name = 'ik',
# 				stretch = True,
# 				squash = True,
# 				aim_axis = 'x',
# 				up_axis = 'z',
# 				offset_name = ['offset'],
# 				ctrl_shape = 'cube',
# 				ctrl_color = 'blue',
# 				connection_type = 'parent',
# 				scale = 10,
# 				stretch_attr = 'stretch',
# 				squash_attr = 'squash'
# 				)