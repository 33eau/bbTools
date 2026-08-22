from importlib import reload
import maya.cmds as cmds
from ..core.utils import rig_utils as bb
from ..core.controllers import creator as bc
from ..core.controllers import shape_color
from ..core.naming import namer_factory as naming
from ..core.naming import current_project
from ..core.naming import parser
from ..rigs import ik_rig as ik
from . import fk_rig as fk
from . import ribbon_rig as rbn
from ..core.data import rig_config as cfg


reload(bb)
reload(bc)
reload(naming)
reload(current_project)
reload(parser)
reload(ik)
reload(fk)
reload(rbn)
reload(cfg)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

FK_CTRL_SHAPE = cfg.fk_ctrl_shape
IK_CTRL_SHAPE = cfg.ik_base_ctrl_shape
IK_PV_CTRL_SHAPE = cfg.pv_ctrl_shape
IK_END_CTRL_SHAPE = cfg.ik_ctrl_shape
SETTING_CTRL_SHAPE = cfg.switch_ctrl_shape
RIBBON_CTRL_SHAPE = cfg.ribbon_ctrl_shape
NUM_NURB_SUBDIVISION = 8
BIND_ELEM = 'bnd'

FOOT_FK_CTRL_SHAPE = cfg.foot_ctrl_shape
FOOT_IK_CTRL_SHAPE = cfg.foot_ctrl_shape
SETTING_CTRL_COLOR = cfg.setting_color

class LimbRig:
	def __init__(self,
				joints = None,
				pole_vector_jnt = None, 
				end_rotation_jnts = None,
				setting_jnt = None,
				rig_name = None,
				parts_name = [],
				side = None,
				aim_axis = 'x',
				up_axis = 'z',
				rotate_order = 'zxy',
				connection_type = 'parent',
				scale = 1,
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				global_scale = '',
				base_orient_loc = '',
				end_orient_loc = '',
				world_space = None,
				ctrl_parent =None,
				mod_parent = None,
				bind_parent ='',
				upper_driver = '',
				ribbon = True,
				feature_name = 'ribbon',
				color = None,
				default_fkIk = 1,
				default_ik_base = 0,
				default_ik_end = 1,
				is_leg = False,
				**controller_kwargs
				):
		
		self.joints =  joints
		self.pole_vector_jnt =  pole_vector_jnt
		self.end_rotation_jnts =  end_rotation_jnts
		self.setting_jnt =  setting_jnt
		self.rig_name =  rig_name
		self.aim_axis =  aim_axis
		self.up_axis =  up_axis
		self.rotate_order =  rotate_order
		self.connection_type =  connection_type
		self.scale =  scale
		self.stretch_attr =  stretch_attr
		self.squash_attr =  squash_attr
		self.global_scale =  global_scale
		self.base_orient_loc =  base_orient_loc
		self.end_orient_loc =  end_orient_loc
		self.world_space =  world_space
		self.ctrl_parent =  ctrl_parent
		self.mod_parent =  mod_parent
		self.bind_parent =  bind_parent
		self.upper_driver =  upper_driver
		self.ribbon =  ribbon
		self.feature_name =  feature_name
		self.default_fkIk =  default_fkIk
		self.default_ik_base =  default_ik_base
		self.default_ik_end =  default_ik_end
		self.is_leg =  is_leg
		self.controller_kwargs =  controller_kwargs
	
		if side is None :
			self.side = parser.find_element(joints[0], 'sides')
		else:
			self.side =  side

		if color is None:
			self.formatted_side = parser.format_side(self.side, 'upper')
			color = shape_color.CTRL_COLOR.get(self.formatted_side, [0,5, 0.5, 0.5])
			self.color = color
		else: 
			self.color =  color 

		if not parts_name:
			self.parts_name = []
			for jnt in joints:
				base_name = parser.get_base_name(jnt)
				base_name = parser.clean_name(base_name, 'tmp')
				self.parts_name.append(base_name)
		else:
			self.parts_name =  parts_name

		self.up_vector = bb.axis_convert(up_axis, 'vector')
		default_shape_rotation = [item * 90 for item in self.up_vector]
		self.shape_rotation = controller_kwargs.get('shape_rotation', default_shape_rotation)
			
		self.ctrl_grp = None
		self.mod_grp = None
		self.bind_jnts = None
		self.ctrl_dict = {}
		self.setting_ctrl = None
		self.rig_jnts = None
		self.ik_jnts =  None
		self.fk_ctrls = None

		self._build()
		bb.over_and_out('LimbRig', f'{self.side}{self.rig_name}')

	def _build(self):
		base, element, number, _, _ = NAMER.extract(self.rig_name)
		element = element if element else []
		self.ctrl_grp = bb.create_node('group', base, element + ['Ctrl'], number, self.side, p=self.ctrl_parent)
		self.mod_grp = bb.create_node('group', base, element + ['Mod'], number, self.side, p=self.mod_parent)
		jnt_grp = bb.create_node('group', base, element + ['Jnt'], number, self.side, p=self.mod_grp)
		if self.upper_driver:
			bb.create_constraint([self.upper_driver], self.ctrl_grp, 'parentScale')
			bb.create_constraint([self.upper_driver], jnt_grp, 'parentScale')

		generated_joints = bb.duplicate_joint_chain(self.joints, add_elements=['fk', 'ik', 'rig', BIND_ELEM], remove_element='tmp')
		fk_jnts = generated_joints['fk']
		ik_jnts = generated_joints['ik']
		rig_jnts = generated_joints['rig']
		bind_jnts = generated_joints[BIND_ELEM]

		cmds.parent(fk_jnts[0], ik_jnts[0], rig_jnts[0], jnt_grp)
		if self.bind_parent:
			cmds.parent(bind_jnts[0], self.bind_parent)

		# ---  End Rotation ----------------------
		if self.end_rotation_jnts:
			end_generated_joints = bb.duplicate_joint_chain(self.end_rotation_jnts[1:], add_elements=['fk', 'ik', 'rig', BIND_ELEM], remove_element='tmp')
			end_rotation_jnts = [rig_jnts[-1]] + end_generated_joints['ik']
			end_fk_jnts = end_generated_joints['fk']
			end_ik_jnts = end_generated_joints['ik']
			end_rig_jnts = end_generated_joints['rig']
			end_bnd_jnts = end_generated_joints[BIND_ELEM]
			cmds.parent(end_bnd_jnts[0], bind_jnts[-1])
			cmds.parent(end_fk_jnts[0], fk_jnts[-1])
			cmds.parent(end_rig_jnts[0], rig_jnts[-1])

			fk_rig_jnts = fk_jnts + end_fk_jnts
			rig_end_joints = False
		else:
			end_rotation_jnts = None
			fk_rig_jnts = fk_jnts
			rig_end_joints = True
		# 
		
		ik_rig = ik.IkRig( joints = ik_jnts,
						pole_vector_jnt = self.pole_vector_jnt,
						end_rotation_jnts = end_rotation_jnts,
						rig_name = self.rig_name,
						side = self.side,
						element_name = 'ik',
						stretch = True,
						squash = True,
						aim_axis = self.aim_axis,
						up_axis = self.up_axis,
						ctrl_shape = IK_CTRL_SHAPE,
						ctrl_color = self.color,
						connection_type = self.connection_type,
						scale = self.scale,
						stretch_attr = self.stretch_attr,
						squash_attr = self.squash_attr,
						global_scale = self.global_scale,
						base_orient_loc = self.base_orient_loc,
						end_orient_loc = self.end_orient_loc,
						world_space = self.world_space,
						ctrl_parent = self.ctrl_grp,
						mod_parent = self.mod_grp,
						upper_driver = self.upper_driver,
						default_ik_base = self.default_ik_base,
						default_ik_end = self.default_ik_end,
						pv_shape = IK_PV_CTRL_SHAPE,
						is_leg=self.is_leg
						)
		ik_grps = ik_rig.mod_grp
		self.pivot_mod_grp = ik_rig.pivot_mod_grp
		self.ik_end_ctrl = ik_rig.ik_end_ctrl
		self.stretch_end_loc = ik_rig.stretch_end_loc
		self.leg_ikh = ik_rig.ikh

		fk_rig = fk.FKRig( 
						joints=fk_rig_jnts,
						rig_name = self.rig_name,
						element_name = 'fk',
						side = self.side,
						offset_names=['zro'],
						stretch = True,
						squash = True,
						aim_axis = self.aim_axis,
						up_axis = self.up_axis,
						shape = FK_CTRL_SHAPE,
						color = self.color,
						connection_type = 'None',
						ctrl_parent = self.ctrl_grp,
						scale = self.scale * 1.3,
						rotate_order = self.rotate_order,
						shape_rotation = self.shape_rotation,
						rig_end_joints=rig_end_joints
						)
		fk_ctrls = fk_rig.ctrls	
		fk_grps = fk_rig.grps	

		if not self.is_leg:
			if self.end_orient_loc:
				bb.snap([self.end_orient_loc], fk_grps[-1][0] )

		for ctrl, jnt in zip(fk_ctrls, fk_rig_jnts):
			bb.create_constraint([ctrl], jnt, 'parent')

		bb.create_constraint([fk_rig.end_grp], fk_rig_jnts[-1], 'parentScale')

		bb.create_local_world(local=self.upper_driver, 
						world=self.world_space, 
						target='upper', 
						types=['rotate'], 
						attr_name='worldOrient', 
						ctrl=fk_ctrls[0], 
						dv=1.0)
		
		setting_controller = bc.Controller( 
							objects = [self.setting_jnt],
							main_ctrl_grp = self.ctrl_grp,
							shape = SETTING_CTRL_SHAPE,
							color = SETTING_CTRL_COLOR,
							scale = self.scale * 0.2,
							line_width = 1.25,
							connection_type = 'None',
							shape_rotation = [0,0,0]
							)
		setting_ctrl = setting_controller.ctrls[0]
		setting_grp = setting_controller.offset_grps[0][0]

		bb.create_guide_curve(ctrl = setting_ctrl, target = rig_jnts[2], parent = self.ctrl_grp, curve_elem = '')
		bb.attr_separator(ctrl=setting_ctrl)
		follow_locator, up_obj = bb.aim_follow(parent=rig_jnts[2], upper_parent = rig_jnts[1], target=setting_grp, aim=self.aim_axis, up=self.up_axis, attr_name = 'follow', ctrl = setting_ctrl, dv = 0)
		cmds.parent(follow_locator, up_obj, self.mod_grp)

		bb.fk_ik_switch(
			parents_fk = fk_jnts,
			parents_ik = ik_jnts,
			targets = rig_jnts,
			attr_name = 'fkIk',
			features = ['translation', 'rotation', 'scale'],
			ctrl = setting_ctrl,
			ik_ctrl_grp = ik_rig.ctrl_grp,
			fk_ctrl_grp = fk_rig.ctrl_grp,
			setup_name = self.rig_name,
			default_value = self.default_fkIk
			)

		for rig_jnt, bind_jnt in zip(rig_jnts, bind_jnts):
			bb.matrix_constrain(rig_jnt, bind_jnt, channels=['translate', 'rotate'])
		
		if self.end_rotation_jnts:
			bb.fk_ik_switch(
						parents_fk = end_fk_jnts,
						parents_ik = end_ik_jnts,
						targets = end_rig_jnts,
						attr_name = 'fkIk',
						features = ['translation', 'rotation', 'scale'],
						ctrl = setting_ctrl,
						ik_ctrl_grp = None,
						fk_ctrl_grp = None,
						setup_name = self.rig_name,
						default_value = self.default_fkIk
						)
			for jnt in self.end_rotation_jnts:
				cmds.connectAttr(f'{self.ik_end_ctrl}.s', f'{jnt}.s')

		# ---  Ribbon Rig ----------------------
		if self.ribbon:
			cross_axis = bb.axis_convert(self.aim_axis, 'cross_letter', self.up_axis)
			ribbon_rig = rbn.RibbonRig(joints = rig_jnts,
							rig_name = self.rig_name,
							feature_name = self.feature_name,
							aim_axis = self.aim_axis,
							up_axis = self.up_axis,
							num_nurb_subdivision = NUM_NURB_SUBDIVISION,
							shape = RIBBON_CTRL_SHAPE,
							connection_type = self.connection_type,
							scale = self.scale,
							ctrl_parent = self.ctrl_grp,
							mod_parent = self.mod_grp,
							upper_bind_parent = bind_jnts[0],
							lower_bind_parent = bind_jnts[1],
							color = 'light'+self.color.capitalize(),
							end_orient_loc =self.end_orient_loc,
							upper_driver = self.upper_driver,
							global_scale = self.global_scale,
							**self.controller_kwargs)
			if self.upper_driver:
				bb.create_constraint([self.upper_driver], ribbon_rig.ctrl_grp, 'parentScale')
				bb.create_constraint([self.upper_driver], ribbon_rig.jnts_grp, 'parentScale')
		
		fk_jnts = fk_rig_jnts
		if self.end_rotation_jnts:
			rig_jnts = rig_jnts + end_rig_jnts
			bind_jnts = bind_jnts + end_bnd_jnts
			ik_jnts = ik_jnts + end_ik_jnts
		
		# for rig, bnd in zip(rig_jnts, bind_jnts):
		# 	bb.matrix_constrain(rig, bnd)
		
		self.setting_ctrl = setting_ctrl
		self.bind_jnts = bind_jnts
		self.rig_jnts = rig_jnts
		self.ik_jnts =  ik_jnts
		self.fk_ctrls = fk_ctrls

	def foot_rig(self, foot_joints = ['l_ball_tmp_jnt', 'l_toe_tmp_jnt'], 
						ball_pv_jnt = 'l_ball_pv_jnt', 
						toe_pv_jnt = 'l_ankle_pv_jnt', 
						foot_name = 'foot', 
						aim_axis = 'z',
						up_axis = 'x',
						rotate_order = 'zyx',
						ball_orient_loc = 'l_ball_orientation_loc',
						upper_jnt = None,
						foot_pivots = [ 'l_foot_heel_loc', 'l_foot_toe_loc', 'l_foot_out_loc', 'l_foot_in_loc'],
						color = 'sky',
						subcolor = 'lightBlue'):
		
		upper_jnt = upper_jnt or self.rig_jnts[-1]

		foot_ctrl_grp = bb.create_node('group', foot_name, ['ctrl'], None, self.side, p = self.ctrl_parent)
		foot_mod_grp = bb.create_node('group', foot_name, ['mod'], None, self.side, p = self.mod_parent)

		generated_joints = bb.duplicate_joint_chain(foot_joints, add_elements=['fk', 'ik', 'rig', BIND_ELEM], remove_element='tmp', ignore_jnts=[ball_pv_jnt, toe_pv_jnt])
		foot_fk_jnts = generated_joints['fk']
		foot_ik_jnts = generated_joints['ik']
		foot_rig_jnts = generated_joints['rig']
		foot_bind_jnts = generated_joints[BIND_ELEM]

		base, element, number, side, suffix = NAMER.extract(upper_jnt)
		upper_base_name = parser.get_base_name(upper_jnt, first_name=True)
		for elem in ['fk', 'ik', 'rig', BIND_ELEM]:
			child = generated_joints[elem][0]
			parent = NAMER.format(upper_base_name, [elem], number, side, suffix)
			cmds.parent(child, parent)

		# ————————————————————————————————————————————————————
		##################### Fk Rig #####################
		fk_rig = fk.FKRig( 
				joints=foot_fk_jnts,
				rig_name = foot_name,
				element_name = 'fk',
				side = self.side,
				stretch = True,
				squash = False,
				aim_axis = aim_axis,
				up_axis = up_axis,
				shape = FOOT_FK_CTRL_SHAPE,
				color = self.color,
				connection_type = 'None',
				ctrl_parent = self.fk_ctrls[-1],
				scale = self.scale * 1.2,
				rotate_order = rotate_order,
				rig_end_joint=False,
				base_orient_loc = ball_orient_loc
				)
		fk_ctrl = fk_rig.ctrls[0]
		fk_grps = fk_rig.grps[0]
		fk_end_grp = fk_rig.end_grp

		bb.create_constraint([fk_ctrl], foot_joints[0], 'parent')
		bb.create_constraint([fk_end_grp], foot_joints[1], 'parent')

		# ————————————————————————————————————————————————————
		##################### Ik Rig #####################

		base, element, number, side, suffix = NAMER.extract(foot_ik_jnts[0])
		ball_ikh, ball_eff = bb.create_node('ikSc', base, ['ik'], number, side, sj= self.ik_jnts[-1], ee=foot_ik_jnts[0])

		base, element, number, side, suffix = NAMER.extract(foot_ik_jnts[1])
		toe_ikh, toe_eff = bb.create_node('ikSc', base, ['ik'], number, side, sj=foot_ik_jnts[0], ee=foot_ik_jnts[1])
		foot_ikh = [ball_ikh, toe_ikh]

		pivot_controllers = bc.Controller(objects = foot_pivots,
					offset_names = ['Offset'],
					main_ctrl_grp =  self.ik_end_ctrl,
					shape = 'sphere',
					color = subcolor,
					scale= self.scale * 0.4,
					connection_type = 'None',
					rotate_order = 'xyz',
					shape_rotation = [0, 0, 0],
					fk_chain = True
					)
		pivot_ctrls = pivot_controllers.ctrls

		ball_ik = bc.Controller(objects = [ball_orient_loc],
								offset_names = ['zro', 'Offset'],
								main_ctrl_grp =  pivot_ctrls[-1],
								name = 'ball',
								side = self.side,
								shape = 'cube',
								color =  color,
								connection_type = 'None',
								rotate_order = 'xyz',
								shape_rotation = [0, 0, 0],
								scale= [1.2, 1.2, 0.35],
								)
		ball_ik_ctrl = ball_ik.ctrls[0]

		aim_vector = bb.axis_convert(aim_axis, 'vector')
		move_value = [ val * 4 for val in aim_vector]
		toe_ik = bc.Controller(objects = [ball_orient_loc],
								offset_names = ['zro', 'Offset'],
								main_ctrl_grp =  pivot_ctrls[-1],
								name = 'toe',
								side = self.side,
								shape = 'cube',
								color =  color,
								connection_type = 'None',
								rotate_order = 'xyz',
								shape_rotation = [0, 0, 0],
								scale= [1.2, 1, 0.35],
								move = move_value
								)
		toe_ik_ctrl = toe_ik.ctrls[0]

		cmds.parent(toe_ikh, foot_mod_grp)
		cmds.parent(ball_ikh, self.pivot_mod_grp)

		piv_grp = bb.create_node('group', foot_name, ['piv'], None, side)
		bb.snap([pivot_ctrls[0]], piv_grp)
		cmds.parent(piv_grp, ball_ik_ctrl)

		cmds.delete(self.pivot_mod_grp, constraints=True)
		bb.create_constraint([toe_ik_ctrl], toe_ikh)
		bb.create_constraint([piv_grp], self.pivot_mod_grp)
		bb.create_constraint([toe_ik_ctrl], foot_ik_jnts[0], 'scale')

		cmds.connectAttr(f'{self.ik_end_ctrl}.s', f'{self.ik_jnts[-1]}.s')
		
		# ————————————————————————————————————————————————————
		##################### Foot SDKs #####################

		# Axis conversion for rotations
		ab_aim_axis = bb.axis_convert(aim_axis, 'absolute_letter')
		ab_up_axis = bb.axis_convert(up_axis, 'absolute_letter')
		cross_axis = bb.axis_convert(aim_axis, 'cross_letter', up_axis)
		ab_cross_axis = bb.axis_convert(cross_axis, 'absolute_letter')

		# Foot Poses setup configurations
		# Format: {pose_name: {'ctrls': list, 'driven_attr': string, 'keys': list, 'multipliers': dict}}
		foot_sdk_configs = {
			'footRoll': {
				'ctrls': [ball_ik_ctrl, pivot_ctrls[1], pivot_ctrls[0]], # ball, toe pivot, heel pivot
				'driven_attr': f'r{ab_up_axis}',
				'keys': [
					{-90: 0, 0: 0, 45: 1, 90: 0},   # Ball
					{-90: 0, 0: 0, 45: 0, 90: 1},   # Toe
					{-90: -90, 0: 0, 45: 0, 90: 0} # Heel
				],
				'limit': True,
				'multipliers': {
					'attrs': ['footRoll_bend', 'footRoll_straight'],
					'values': [45, 90]
				}
			},
			'toeTwist': {
				'ctrls': [pivot_ctrls[1]],
				'driven_attr': f'r{ab_cross_axis}',
				'keys': [{-50: -50, 0: 0, 50: 50}]
			},
			'heelTwist': {
				'ctrls': [pivot_ctrls[0]],
				'driven_attr': f'r{ab_cross_axis}',
				'keys': [{-50: -50, 0: 0, 50: 50}]
			},
			'footBank': {
				'ctrls': [pivot_ctrls[3], pivot_ctrls[2]], # in, out
				'driven_attr': f'r{ab_aim_axis}',
				'keys': [{-50: 50, 0: 0, 50: 0}, {-50: 0, 0: 0, 50: -50}]
			}
		}

		bb.attr_separator(self.ik_end_ctrl, 'footPose')

		for pose, config in foot_sdk_configs.items():
			ctrl_list = config['ctrls']
			driven_attr = config['driven_attr']
			multipliers = config.get('multipliers')
			limit_override = config.get('limit')
			
			for i, ctrl in enumerate(ctrl_list):
				key_values = config['keys'][i]
				limit = limit_override if limit_override is not None else (False if len(ctrl_list) > 1 else True)
				
				# Create SDK offset group
				driven_grp = bb.create_offset_group(ctrl, [pose])
				driven_node = driven_grp[ctrl][0]
				driven_full_attr = f'{driven_node}.{driven_attr}'

				# Handle SDK setup (with optional multiplier nodes for footRoll)
				if multipliers and i < len(multipliers['attrs']):
					mul_attr = multipliers['attrs'][i]
					mul_val = multipliers['values'][i]
					
					# Create and connect multiplier node
					base_name = parser.get_base_name(ctrl)
					mdl_node = bb.create_node('multDoubleLinear', base_name, [pose], None, self.side)
					bb.set_driven_key(main_ctrl=self.ik_end_ctrl, attr=pose, driven=f'{mdl_node}.i2', values=key_values, limit=limit)
					
					if not cmds.attributeQuery(mul_attr, node=self.ik_end_ctrl, exists=True):
						cmds.addAttr(self.ik_end_ctrl, ln=mul_attr, at='float', dv=mul_val, k=True)
					
					cmds.connectAttr(f'{self.ik_end_ctrl}.{mul_attr}', f'{mdl_node}.i1')
					cmds.connectAttr(f'{mdl_node}.o', driven_full_attr)
				else:
					# Standard Set Driven Key
					bb.set_driven_key(main_ctrl=self.ik_end_ctrl, attr=pose, driven=driven_full_attr, values=key_values, limit=limit)

		for rig_jnt, bnd_jnt in zip(foot_rig_jnts, foot_bind_jnts):
			#bb.create_constrain([rig_jnt], bnd_jnt, 'parentScale')
			bb.matrix_constrain(rig_jnt, bnd_jnt)

		bb.fk_ik_switch(
			parents_fk = foot_fk_jnts,
			parents_ik = foot_ik_jnts,
			targets = foot_rig_jnts,
			attr_name = 'fkIk',
			features = ['translation', 'rotation', 'scale'],
			ctrl = self.setting_ctrl,
			ik_ctrl_grp = None,
			fk_ctrl_grp = None,
			setup_name = None,
			default_value = None
			)

	def foot_roll(self, 
					foot_crv = None,
					foot_ctrl_pos_jnt = None,
					ball_bp_jnt = None,
					bank_angle = [],
					roll_angle = []
			): #26Aug19

		ankle_ik_jnt = self.ik_jnts[-1]
		upper_bind_jnt = self.bind_jnts[-1]
		ik_ctrl = self.ik_end_ctrl
		leg_ikh = self.leg_ikh
		limb_ctrl_grp = self.ctrl_grp
		limb_mod_grp = self.mod_grp
		formatted_side = self.formatted_side

		base, element, number, side, suffix = NAMER.extract(foot_crv)
		ctrl_grp = bb.create_node('group', base, element + ['ctrl'], number, side, p=limb_ctrl_grp)
		mod_grp = bb.create_node('group', base, element + ['mod'], number, side, p=limb_mod_grp)
		jnt_grp = bb.create_node('group', base, element + ['jnt'], number, side, p=mod_grp)

		cmds.xform(foot_crv, cp=True)
		bb.freeze(foot_crv)
		foot_crv_bb = cmds.xform(foot_crv, bb=True, q=True)
		min_x = foot_crv_bb[0]
		min_z = foot_crv_bb[2]
		max_x = foot_crv_bb[3]
		max_z = foot_crv_bb[5]
		limit_x_val = (max_x - min_x)/2
		limit_z_val = (max_z - min_z)/2

		# ---  Create Reverse Foot Roll Joints ----------------------
		reverse_jnt_tokens = ['main', 'piv', 'inv', 'heel', 'toe', 'ball', 'ankle']
		jnt_parent = jnt_grp
		reverse_jnts = []
		for token in reverse_jnt_tokens:
			jnt = bb.create_node('joint', base, [token, 'rev'], number, side, rad = 0.5)
			cmds.matchTransform(jnt, foot_crv)
			cmds.delete(cmds.orientConstraint(ankle_ik_jnt, jnt, mo=False))
			cmds.makeIdentity( jnt, a=True, r=True, n=0, pn =1)
			cmds.parent(jnt, jnt_parent)
			jnt_parent = jnt
			reverse_jnts.append(jnt)

		# ---  Position Toe And Heel Joint At Min/max Z Value ----------------------
		for i, val in enumerate([min_z, max_z]):
			current_posi = cmds.xform(reverse_jnts[3+i], ws=True, q=True, t=True)
			cmds.xform(reverse_jnts[3+i], t=[current_posi[0], current_posi[1], val], ws=1)

		main_jnt, piv_jnt, inv_jnt, heel_jnt, toe_jnt, ball_jnt, ankle_jnt = reverse_jnts
		cmds.matchTransform(ball_jnt, ball_bp_jnt, pos=True)
		cmds.matchTransform(ankle_jnt, ankle_ik_jnt, pos=True)
		cmds.makeIdentity( ball_jnt, a=True, r=True, n=0, pn =1)
		cmds.makeIdentity( ankle_jnt, a=True, r=True, n=0, pn =1)

		# ---  Create Ik Jnt ----------------------
		ball_ik_jnt = bb.create_node('joint', base, ['ball'], number, side)
		cmds.matchTransform(ball_ik_jnt, ball_bp_jnt, pos=True)
		cmds.parent(ball_ik_jnt, ankle_ik_jnt)
		toe_ik_jnt = bb.create_node('joint', base, ['toe'], number, side)
		cmds.matchTransform(toe_ik_jnt, toe_jnt)
		cmds.parent(toe_ik_jnt, ball_ik_jnt)

		# ---  Create Ikh ----------------------
		ball_ikh, ball_eff = bb.create_node('ikSc', base, ['ball'], number, side, sj=ankle_ik_jnt, ee=ball_ik_jnt)
		toe_ikh, toe_eff = bb.create_node('ikSc', base, ['toe'], number, side, sj=ball_ik_jnt, ee=toe_ik_jnt)
		cmds.parent(ball_ikh, ball_jnt)
		cmds.parent(toe_ikh, toe_jnt)

		# ---  Create Bind Jnts ----------------------
		ball_bnd_jnt = bb.create_node('joint', base, ['ball', 'bnd'], number, side)
		cmds.matchTransform(ball_bnd_jnt, ball_bp_jnt, pos=True)
		cmds.parent(ball_bnd_jnt, upper_bind_jnt)
		bb.create_constraint([ball_ik_jnt], ball_bnd_jnt)
		toe_bnd_jnt = bb.create_node('joint', base, ['toe', 'bnd'], number, side)
		cmds.matchTransform(toe_bnd_jnt, toe_ik_jnt, pos=True)
		cmds.parent(toe_bnd_jnt, ball_bnd_jnt)
		bb.create_constraint([toe_ik_jnt], toe_bnd_jnt)

		# ---  Create Ctrl ----------------------
		tmp_orient_loc = bb.create_node('locator', base, ['tmp', 'orient'], number, side)
		cmds.delete(cmds.orientConstraint(tmp_orient_loc, foot_ctrl_pos_jnt, mo=False))
		bb.freeze(foot_ctrl_pos_jnt)
		cmds.delete(tmp_orient_loc)
		foot_frame_name = NAMER.format(base, element+['frame'], number, side, suffix)
		ctrl_frame_crv = cmds.duplicate(foot_crv, n=foot_frame_name)[0]
		cmds.matchTransform(ctrl_frame_crv, foot_ctrl_pos_jnt, pos=True)
		cmds.setAttr( f'{ctrl_frame_crv}.ove', 1)
		cmds.setAttr( f'{ctrl_frame_crv}.overrideDisplayType', 1)

		foot_ref_name = NAMER.format(base, element+['ref'], number, side, suffix)
		foot_ref_crv = cmds.duplicate(ctrl_frame_crv, n=foot_ref_name)[0]
		bb.scale_shape(foot_ref_crv, scale=0.75)
		cmds.setAttr( f'{foot_ref_crv}.v', 0, l=True)

		controller = bc.Controller(objects = [foot_ctrl_pos_jnt],
				main_ctrl_grp = ctrl_grp,
				name = base,
				side = side,
				offset_names = ['offset'],
				shape = 'sphere',
				color = 'side',
				scale = 0.1,
				line_width = 1.0,
				gimbal = False,
				connection_type = 'None',
				rotate_order = 'yxz',
				lock_attrs = ['ty', 'sx', 'sy', 'sz'],
				deg=1)

		foot_ctrl = controller.ctrls[0]
		foot_ctrl_grp = controller.offset_grps[0][0]
		cmds.parent([ctrl_frame_crv, foot_ref_crv], ctrl_grp)

		bb.attr_separator(foot_ctrl)
		cmds.addAttr( foot_ctrl, ln = 'frameVis', at = 'enum', en = 'OFF:ON' , k = True, dv = 1)
		cmds.connectAttr(f'{foot_ctrl}.frameVis', f'{ctrl_frame_crv}.v')
		cmds.transformLimits(foot_ctrl, etx=(1, 1), etz=(1, 1))
		cmds.transformLimits(foot_ctrl, tx=[limit_x_val*-1, limit_x_val], tz=[limit_z_val*-1, limit_z_val])

		# ---  Piv Calculate ----------------------
		ctrl_pos_dcm = bb.create_node('decomposeMatrix', base, ['pos'], number, side)
		ctrl_shp = cmds.listRelatives(foot_ctrl, s=True)[0]
		cmds.connectAttr(f'{ctrl_shp}.worldMatrix[0]', f'{ctrl_pos_dcm}.inputMatrix')

		ref_pos_npc = bb.create_node('nearestPointOnCurve', base, ['pos'], number, side)
		cmds.connectAttr(f'{ctrl_pos_dcm}.outputTranslate', f'{ref_pos_npc}.inPosition')
		cmds.connectAttr(f'{foot_ref_crv}Shape.worldSpace[0]', f'{ref_pos_npc}.inputCurve')

		piv_pos_poc = bb.create_node('pointOnCurveInfo', base, ['piv', 'pos'], number, side)
		cmds.connectAttr(f'{ref_pos_npc}.parameter', f'{piv_pos_poc}.parameter')
		cmds.connectAttr(f'{foot_crv}Shape.worldSpace[0]', f'{piv_pos_poc}.inputCurve')

		piv_loc = bb.create_node('locator', base, ['piv'], number, side)
		cmds.connectAttr(f'{piv_pos_poc}.result.position ', f'{piv_loc}.t')

		foot_inv_val_mdv = bb.create_node('multiplyDivide', base, ['inv', 'val'], number, side)
		cmds.connectAttr(f'{piv_jnt}.t', f'{foot_inv_val_mdv}.i1')
		cmds.setAttr( f'{foot_inv_val_mdv}.i2', -1, -1, -1)
		cmds.connectAttr(f'{foot_inv_val_mdv}.o', f'{inv_jnt}.t')

		bb.create_constraint([piv_loc], piv_jnt, 'point', maintain_offset=False)

		# ---  Remap Value Nodes ----------------------
		if formatted_side == 'R':
			tx_neg_mdl = bb.create_node('multDoubleLinear', base, ['tx', 'neg'], number, side)	
			cmds.connectAttr(f'{foot_ctrl}.tx', f'{tx_neg_mdl}.i1')
			cmds.setAttr( f'{tx_neg_mdl}.i2', -1)
			tz_neg_mdl = bb.create_node('multDoubleLinear', base, ['tz', 'neg'], number, side)	
			cmds.connectAttr(f'{foot_ctrl}.tz', f'{tz_neg_mdl}.i1')
			cmds.setAttr( f'{tz_neg_mdl}.i2', -1)
			tx_output = f'{tx_neg_mdl}.o'
			tz_output = f'{tz_neg_mdl}.o'
			negate_val = -1
		else:
			tx_output = f'{foot_ctrl}.tx'
			tz_output = f'{foot_ctrl}.tz'
			negate_val = 1

		bank_rmv = bb.create_node('remapValue', base, ['bank'], number, side)
		cmds.connectAttr(tx_output, f'{bank_rmv}.inputValue')
		cmds.setAttr( f'{bank_rmv}.value[0].value_FloatValue', 1)
		cmds.setAttr( f'{bank_rmv}.value[1].value_FloatValue', 0)
		cmds.setAttr( f'{bank_rmv}.inputMin', limit_z_val*-1)
		cmds.setAttr( f'{bank_rmv}.inputMax', limit_z_val)
		cmds.setAttr( f'{bank_rmv}.outputMin', bank_angle[0])
		cmds.setAttr( f'{bank_rmv}.outputMax', bank_angle[1])
		cmds.connectAttr(f'{bank_rmv}.outValue', f'{piv_jnt}.rz')

		roll_rmv = bb.create_node('remapValue', base, ['roll'], number, side)
		cmds.connectAttr(tz_output, f'{roll_rmv}.inputValue')
		cmds.setAttr( f'{roll_rmv}.inputMin', limit_x_val*-1)
		cmds.setAttr( f'{roll_rmv}.inputMax', limit_x_val)
		cmds.setAttr( f'{roll_rmv}.outputMin', roll_angle[0] * negate_val)
		cmds.setAttr( f'{roll_rmv}.outputMax', roll_angle[1] * negate_val)
		cmds.connectAttr(f'{roll_rmv}.outValue', f'{piv_jnt}.ry')

		toe_rmv = bb.create_node('remapValue', base, ['toe', 'roll'], number, side)
		cmds.connectAttr(tz_output, f'{toe_rmv}.inputValue')
		cmds.setAttr( f'{toe_rmv}.value[0].value_FloatValue', 1)
		cmds.setAttr( f'{toe_rmv}.value[1].value_FloatValue', 0.5)
		cmds.setAttr( f'{toe_rmv}.value[1].value_Position', 0.5)
		cmds.setAttr( f'{toe_rmv}.value[2].value_FloatValue', 1)
		cmds.setAttr( f'{toe_rmv}.inputMin', 0)
		cmds.setAttr( f'{toe_rmv}.inputMax', limit_x_val)
		cmds.setAttr( f'{toe_rmv}.outputMin', roll_angle[0])
		cmds.setAttr( f'{toe_rmv}.outputMax', 0)
		cmds.connectAttr(f'{toe_rmv}.outValue', f'{toe_jnt}.ry')

		ball_rmv = bb.create_node('remapValue', base, ['ball', 'roll'], number, side)
		cmds.connectAttr(tz_output, f'{ball_rmv}.inputValue')
		cmds.setAttr( f'{ball_rmv}.value[0].value_FloatValue', 0)
		cmds.setAttr( f'{ball_rmv}.value[1].value_FloatValue', 0.5)
		cmds.setAttr( f'{ball_rmv}.value[1].value_Position', 0.5)
		cmds.setAttr( f'{ball_rmv}.inputMin', 0)
		cmds.setAttr( f'{ball_rmv}.inputMax', limit_x_val)
		cmds.setAttr( f'{ball_rmv}.outputMin', 0)
		cmds.setAttr( f'{ball_rmv}.outputMax', roll_angle[1])

		# ---  Bend Strength Attr ----------------------
		bend_attr = 'bendStrength'
		cmds.addAttr( foot_ctrl, ln = bend_attr, at = 'float', min = 0, max = 1, dv = 0.5, k = True )
		bend_mdl = bb.create_node('multDoubleLinear', base, ['ball', 'bend'], number, side)
		cmds.connectAttr(f'{foot_ctrl}.{bend_attr}', f'{bend_mdl}.i1')
		cmds.setAttr( f'{bend_mdl}.i2', 150)
		cmds.connectAttr(f'{bend_mdl}.o', f'{ball_rmv}.outputMax')
		cmds.connectAttr(f'{ball_rmv}.outValue', f'{ball_jnt}.ry')

		# --- Connect to Stretch loc ----------------------
		bb.create_constraint([ankle_jnt], self.stretch_end_loc)

		# ---  Organize ----------------------
		bb.create_constraint([ankle_jnt], leg_ikh, 'parent')
		bb.create_constraint([ik_ctrl], foot_crv, 'parent')
		bb.create_constraint([ik_ctrl], jnt_grp, 'parent')
		bb.create_constraint([ik_ctrl], ctrl_grp, 'parent')
		cmds.parent([foot_crv, piv_loc], mod_grp)

		# ---  Foot Poses ----------------------
		pose_map = {
			'toeTwist' : [[-45, 45], toe_jnt, 'rx'],
			'ballTwist' : [[-45, 45], ball_jnt, 'rx'],
			'heelTwist' : [[-45, 45], heel_jnt, 'rx'] 
			}
		for pose, data in pose_map.items():
			val = data[0]
			jnt = data[1]
			axis = data[2]
			cmds.addAttr( foot_ctrl, ln = pose, at = 'float', min = val[0], max = val[1], dv = 0, k = True )
			if formatted_side == 'R':
				inv_val_mdl = bb.create_node('multDoubleLinear', base, [pose, 'inv'], number, side)
				cmds.connectAttr(f'{foot_ctrl}.{pose}', f'{inv_val_mdl}.i1')
				cmds.setAttr( f'{inv_val_mdl}.i2', -1)
				output_val = f'{inv_val_mdl}.o'
			else:
				output_val = f'{foot_ctrl}.{pose}'
			cmds.connectAttr(output_val, f'{jnt}.{axis}')

		cmds.connectAttr(f'{foot_ctrl}.rx', f'{inv_jnt}.ry')
		cmds.connectAttr(f'{foot_ctrl}.ry', f'{inv_jnt}.rx')
		cmds.connectAttr(f'{foot_ctrl}.rz', f'{inv_jnt}.rz')






















