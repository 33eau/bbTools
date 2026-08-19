# ==========================================
# QUADRUPED LEG RIG
# ==========================================

from importlib import reload
import maya.cmds as cmds
from ..core.utils import rig_utils as bb
from ..core.controllers import creator as bc
from ..core.naming import namer_factory as naming
from ..core.naming import current_project
from ..core.naming import parser
from ..core.data import rig_config as cfg
from . import fk_rig as fkr
reload(cfg)
NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

class QuadruppedLeg(object):
	def __init__( self,
				name = 'leg',
				root_jnt = None,
				scale = 1,
				feature = 'fkIk',
				default_fkIk = 1,
				is_hind = False,
				aim = 'x',
				up = 'z',
				bind_parent = None,
				ctrl_parent = None,
				mod_parent = None,
				upper_driver = None,
				parent_spaces = None
				):
		self.name = name
		self.root_jnt = root_jnt
		self.scale = scale
		self.feature = feature
		self.default_fkIk = default_fkIk
		self.is_hind = is_hind
		self.aim = aim
		self.bind_parent = bind_parent
		self.ctrl_parent = ctrl_parent
		self.mod_parent = mod_parent
		self.upper_driver = upper_driver
		self.parent_spaces = parent_spaces

		self.leg_joint_num = 4
		self.region = 'hind' if self.is_hind else 'front'

		self.joint_map = {}
		self.controllers = {}

		self.side = parser.find_element(self.root_jnt, 'sides')
		self.number = parser.find_number(self.name)
		self.rig_name = self.name + '_' + self.region

		self.aim_vector = bb.axis_convert(self.aim, 'vector')
		self.up_vector = bb.axis_convert(up, 'vector')
		self.cross_vector = bb.axis_convert(self.aim_vector, 'cross_vector', up_axis=up)

		self.world_space = 'placement_ctrl'

		self.move_val = -5 if '-' in self.aim else 5

	def build(self):
		self.create_groups()
		self.duplicate_joint_chain()
		if self.feature == 'fk':
			self.build_fk()
		elif self.feature == 'ik':
			self.build_ik()
			# Clean Up
			cmds.delete(self.lower_world_pos)
		
		else:
			self.build_ik()

			switch_pos_loc = cmds.duplicate(self.lower_world_pos, n='switch_pos_loc')[0]
			move_val = [x * (self.scale*10) for x in self.up_vector]
			cmds.move(*move_val, switch_pos_loc, r=True, os = True)

			# Create switch controller
			controller = bc.Controller(objects = [switch_pos_loc],
					main_ctrl_grp = self.ctrl_grp,
					name = f'{self.name}{self.region.capitalize()}Switch',
					side = self.side,
					offset_names = ['ctrl', 'space'],
					shape = cfg.switch_ctrl_shape,
					color = cfg.switch_color,
					scale = self.scale*0.2,
					line_width = 1.0,
					gimbal = False,
					connection_type = 'None',
					rotate_order = 'yxz',
					lock_attrs = ['t','r','s'],
					shape_rotation = [0, 0, 0],
					move = [0,0,0],
					deg=1)

			switch_ctrl = controller.ctrls[0]
			switch_ctrl_grp = controller.offset_grps[0][0]
			switch_ctrl_space_grp = controller.offset_grps[0][1]
			
			bb.create_constraint([self.lower_jnt], switch_ctrl_space_grp)
			bb.create_guide_curve(switch_ctrl, self.joint_chain[2], switch_ctrl_grp)

			fk_rig = fkr.FKRig( 
					joints = self.joint_map['fk'],
					rig_name = self.rig_name,
					element_name = 'fk',
					side = self.side,
					stretch = True,
					squash = True,
					aim_axis = self.aim,
					offset_names = ['offset'],
					shape = cfg.fk_ctrl_shape,
					color = 'side',
					connection_type = 'parent',
					scale = self.scale,
					shape_rotation = [0, 0, 90],
					mod_parent=self.fk_mod_grp
					)
			self.fk_ctrl_grp = fk_rig.ctrl_grp
			cmds.parent(self.fk_ctrl_grp, self.ctrl_grp)
			
			bb.fk_ik_switch(
					parents_fk = self.joint_map['fk'],
					parents_ik = self.joint_map['ik'],
					targets = self.joint_chain[:self.leg_joint_num],
					attr_name = 'fkIk',
					features = ['translation', 'rotation', 'scale'],
					ctrl = switch_ctrl,
					ik_ctrl_grp = self.ik_ctrl_grp,
					fk_ctrl_grp = self.fk_ctrl_grp,
					setup_name = self.rig_name,
					default_value = self.default_fkIk
					)

			# Clean Up
			cmds.delete(switch_pos_loc, self.lower_world_pos)

	def create_groups(self):
		self.ctrl_grp = bb.create_node('group', self.rig_name, ['ctrl'], self.number, self.side)
		self.ik_ctrl_grp = bb.create_node('group', self.rig_name, ['ik', 'ctrl'], self.number, self.side, p=self.ctrl_grp)

		self.mod_grp = bb.create_node('group', self.rig_name, ['mod'], self.number, self.side)
		self.jnt_grp = bb.create_node('group', self.rig_name, ['jnt'], self.number, self.side, p=self.mod_grp)

		bb.create_constraint([self.ctrl_grp], self.mod_grp)

		if 'fk' in (self.feature).lower():
			self.fk_mod_grp = bb.create_node('group', self.rig_name, ['fk', 'mod'], self.number, self.side, p=self.mod_grp)
		if 'ik' in (self.feature).lower():
			self.ik_mod_grp = bb.create_node('group', self.rig_name, ['ik', 'mod'], self.number, self.side, p=self.mod_grp)

		if self.ctrl_parent:
			cmds.parent(self.ctrl_grp, self.ctrl_parent)
		if self.mod_parent:
			cmds.parent(self.mod_grp, self.mod_parent)
		if self.upper_driver:
			bb.create_constraint([self.upper_driver], self.ctrl_grp, 'parentScale')

	def duplicate_joint_chain(self):
		elem_list = ['fk', 'ik', 'stretch']
		if self.is_hind:
			elem_list.append('driver')
		
		base, element, number, side, suffix = NAMER.extract(self.root_jnt)
		self.joint_chain = cmds.listRelatives(self.root_jnt, ad=True, type='joint')
		self.joint_chain.append(self.root_jnt)
		self.joint_chain.reverse()
		cmds.parent(self.joint_chain[0], self.jnt_grp)

		self.upper_jnt = self.joint_chain[0]
		self.mid_jnt = self.joint_chain[1]
		self.lower_jnt = self.joint_chain[2]
		self.end_jnt = self.joint_chain[3]

		for elem in elem_list:
			elem_jnts = []
			for i in range(self.leg_joint_num):
				rig_jnt = self.joint_chain[i]
				base, element, number, side, suffix = NAMER.extract(rig_jnt)
				elem_jnt = bb.create_node('joint', base, [elem], number, side)
				cmds.matchTransform(elem_jnt, rig_jnt)
				bb.freeze(elem_jnt)
				if len(elem_jnts) > 0:
					cmds.parent(elem_jnt, elem_jnts[-1])
				else:
					cmds.parent(elem_jnt, self.jnt_grp)
				elem_jnts.append(elem_jnt)
			self.joint_map[elem] = elem_jnts
		
		self.fk = self.joint_map['fk']
		self.ik = self.joint_map['ik']
		self.stretch = self.joint_map['stretch']
		if self.is_hind:
			self.driver = self.joint_map['driver']
		
		if self.bind_parent:
			cmds.parent(self.joint_chain[0], self.bind_parent)
		
		cmds.parent(self.fk[0], self.fk_mod_grp)

	def build_fk(self):
		fk_rig = fkr.FKRig( 
				joints = self.joint_map['fk'],
				rig_name = self.rig_name,
				element_name = 'fk',
				side = self.side,
				stretch = True,
				squash = True,
				aim_axis = self.aim,
				offset_names = ['offset'],
				shape = cfg.fk_ctrl_shape,
				color = 'side',
				connection_type = 'parent',
				scale = self.scale,
				shape_rotation = [0, 0, 90],
				mod_parent=self.fk_mod_grp
				)
		fk_base_ctrl = fk_rig.ctrls[0]
		space_grp = bb.create_offset_group(fk_base_ctrl, ['space'])
		space_grp = space_grp[fk_base_ctrl][0]
		
		bb.attr_separator(ctrl=fk_base_ctrl)

		enum_names = ['World']
		for obj in self.parent_spaces:
			base_name = parser.get_base_name(obj)
			split_list = base_name.split('_')
			n = [ n.capitalize() for n in split_list]
			n = ''.join(n)
			enum_names.append(n)

		bb.add_enum_space_switch( parent_spaces=self.parent_spaces, 
								world_space=self.ctrl_parent, 
								attr_name='follow', 
								spaces_name=enum_names, 
								target=space_grp, 
								ctrl=fk_base_ctrl, 
								type='orient',
								default_index = 1)

	def build_ik(self):
		ik_upper_jnt = self.joint_map['ik'][0]
		ik_mid_jnt = self.joint_map['ik'][1]
		ik_lower_jnt = self.joint_map['ik'][2]
		ik_end_jnt = self.joint_map['ik'][3]

		knee_ikh, knee_eff = bb.create_node('ikRp', self.rig_name, ['knee'], self.number, self.side, sj = ik_upper_jnt, ee = ik_lower_jnt)
		hock_ikh, hock_eff = bb.create_node('ikSc', self.rig_name, ['hock'], self.number, self.side, sj = ik_lower_jnt, ee = ik_end_jnt)

		if self.is_hind:
			driver_upper_jnt = self.joint_map['driver'][0]
			driver_mid_jnt = self.joint_map['driver'][1]
			driver_lower_jnt = self.joint_map['driver'][2]
			driver_end_jnt = self.joint_map['driver'][3]
			driver_ikh, driver_eff = bb.create_node('ikRp', self.rig_name, ['driver'], self.number, self.side, sj = driver_upper_jnt, ee = driver_end_jnt)
		
		# ---  Create Controllers ----------------------
		# Create Base Ctrl
		controller = bc.Controller(objects = [ik_upper_jnt],
		main_ctrl_grp = self.ik_ctrl_grp,
		name = f'{self.name}Base{self.region.capitalize()}',
		side = self.side,
		offset_names = ['zro', 'space'],
		shape = cfg.ik_base_ctrl_shape,
		color = 'side',
		scale = self.scale * 1.2 ,
		line_width = 1.0,
		gimbal = False,
		connection_type = 'parent',
		rotate_order = 'yxz',
		lock_attrs = ['s'],
		shape_rotation = [0, 0, 90],
		deg=1)
		ik_base_ctrl = controller.ctrls[0]
		ik_base_ctrl_zro_grp = controller.offset_grps[0][0]
		ik_base_ctrl_space_grp = controller.offset_grps[0][1]

		# Create Main Ctrl
		controller = bc.Controller(objects = [ik_end_jnt],
				main_ctrl_grp = self.ik_ctrl_grp,
				name = f'{self.name}{self.region.capitalize()}',
				side = self.side,
				offset_names = ['zro', 'space'],
				shape = cfg.ik_ctrl_shape,
				color = 'side',
				scale = self.scale ,
				line_width = 1.0,
				gimbal = False,
				connection_type = 'None',
				rotate_order = 'yxz',
				lock_attrs = ['s'],
				shape_rotation = [0, 0, 90],
				deg=1)
		ik_ctrl = controller.ctrls[0]
		ik_ctrl_zro_grp = controller.offset_grps[0][0]
		ik_ctrl_space_grp = controller.offset_grps[0][1]

		# Add Space Switch
		enum_names = ['World']
		for obj in self.parent_spaces:
			base_name = parser.get_base_name(obj)
			split_list = base_name.split('_')
			n = [ n.capitalize() for n in split_list]
			n = ''.join(n)
			enum_names.append(n)
		world_idx = len(self.parent_spaces)
		bb.attr_separator(ctrl=ik_base_ctrl)

		bb.add_enum_space_switch( parent_spaces=self.parent_spaces, 
								world_space=self.ctrl_parent, 
								attr_name='follow', 
								spaces_name=enum_names, 
								target=ik_base_ctrl_space_grp, 
								ctrl=ik_base_ctrl, 
								type='parent', 
								default_index=1 )

		if self.is_hind:
			bb.add_enum_space_switch( parent_spaces=self.parent_spaces, 
						world_space=self.ctrl_parent, 
						attr_name='follow', 
						spaces_name=enum_names, 
						target=self.driver[0], 
						ctrl=ik_base_ctrl, 
						type='parent', 
						default_index=1 )
		
		bb.attr_separator(ctrl=ik_ctrl)
		bb.add_enum_space_switch( parent_spaces=self.parent_spaces, 
								world_space=self.ctrl_parent, 
								attr_name='follow', 
								spaces_name=enum_names, 
								target=ik_ctrl_space_grp, 
								ctrl=ik_ctrl, 
								type='parent', 
								default_index=0 )

		# Create PV ctrl
		pv_loc = bb.pole_vector_position(self.joint_map['ik'], offset = 0.5, create_output='locator', name = self.rig_name)
		move_coor = [ v*-1 for v in self.cross_vector ]
		cmds.move(*move_coor, pv_loc, r=True, os=True, wd=True)

		####################################################################
		# SNUBBS hard coded movement
		cmds.move(0, -4, 0, r=True, ws=True, wd=True)
		####################################################################

		controller = bc.Controller(objects = [pv_loc],
				main_ctrl_grp = self.ik_ctrl_grp,
				offset_names = ['zro', 'space'],
				shape = cfg.pv_ctrl_shape,
				color = 'side',
				scale = self.scale * 0.5,
				line_width = 1.0,
				connection_type = 'None',
				rotate_order = 'yxz',
				lock_attrs=['t', 'r']
				)
		
		pv_ctrl = controller.ctrls[0]
		pv_space_grp = controller.offset_grps[0][1]
		bb.create_guide_curve(pv_ctrl, ik_mid_jnt, self.ik_ctrl_grp)
		pv_parent_loc = bb.pole_vector_space(ik_upper_jnt, ik_ctrl, pv_space_grp, self.aim_vector, self.up_vector, self.ik_mod_grp, constrain=False)
		bb.attr_separator(pv_ctrl)
		bb.add_enum_space_switch( parent_spaces = [pv_parent_loc],
							world_space = self.world_space,
							attr_name = 'follow',
							spaces_name = ['local', 'world'],
							target = pv_space_grp,
							ctrl = pv_ctrl,
							type = 'parent',
							default_index = 1,
							#mod_grp = None
						)

		# Create Hock Ctrl
		self.lower_world_pos = bb.create_node('locator', f'{self.rig_name}', ['lower'], self.number, self.side)
		cmds.matchTransform(self.lower_world_pos, self.lower_jnt, pos=True)
		rotate_val = [ a*(-90) + u*(-90) for a, u in zip( self.aim_vector, self.up_vector)]
		cmds.setAttr(f'{self.lower_world_pos}.r', *rotate_val)

		controller = bc.Controller(objects = [self.lower_world_pos],
						main_ctrl_grp = self.ik_ctrl_grp,
						name = f'{self.name}{self.region.capitalize()}Hock',
						side = self.side,
						offset_names = ['zro', 'space'],
						shape = cfg.hock_ctrl_shape,
						color = 'grp',
						scale = self.scale * 0.5,
						connection_type = 'None',
						rotate_order = 'yxz',
						shape_rotation = [0, 0, 90],
						lock_attrs=['r', 's'],
						deg=1 )
		hock_ctrl = controller.ctrls[0]
		hock_space_grp = controller.offset_grps[0][1]
		bb.create_constraint([ik_ctrl], hock_space_grp, 'point')

		# ---  Hock Heirarchy ----------------------
		ik_hock_rot_zro_grp = bb.create_node('group', self.rig_name, ['hock', 'rot', 'zro'], self.number, self.side) 
		ik_hock_rot_grp = bb.create_node('group', self.rig_name, ['hock', 'rot'], self.number, self.side, p =ik_hock_rot_zro_grp)

		cmds.matchTransform(ik_hock_rot_zro_grp, ik_end_jnt, pos=True)
		#cmds.parent(knee_ikh, ik_hock_rot_grp)
		#cmds.parent([ik_hock_rot_zro_grp, hock_ikh], ik_ctrl)
		bb.create_constraint([ik_hock_rot_grp], knee_ikh, 'pac')
		cmds.parent(knee_ikh, self.mod_grp)

		if self.is_hind:
			cmds.parent(ik_hock_rot_zro_grp, self.driver[2])
			cmds.parent(hock_ikh, self.driver[3])
			cmds.parent(driver_ikh, self.ik_mod_grp)
			bb.create_constraint([ik_ctrl], driver_ikh, 'pac')
			cmds.poleVectorConstraint(pv_ctrl, driver_ikh)
		else:
			bb.create_constraint([ik_ctrl], hock_ikh, 'pac')
			cmds.parent(hock_ikh, self.mod_grp)
			cmds.parent(ik_hock_rot_zro_grp, self.ctrl_grp)
			bb.create_constraint([ik_ctrl], ik_hock_rot_zro_grp, 'point')
			cmds.poleVectorConstraint(pv_ctrl, knee_ikh)
		
		bb.create_constraint([ik_ctrl], ik_end_jnt, 'orc')

		# ---  Hock Translation ----------------------
		HOCK_MUL_VAL = -15
		hock_mdv_mul = [HOCK_MUL_VAL]*3
		hock_mdv = bb.create_node('multiplyDivide', self.rig_name, ['hock'], self.number, self.side)

		cmds.setAttr( f'{hock_mdv}.i2', *hock_mdv_mul)
		cmds.connectAttr(f'{hock_ctrl}.t', f'{hock_mdv}.i1')
		cmds.connectAttr(f'{hock_mdv}.oy', f'{ik_hock_rot_grp}.rx')
		cmds.connectAttr(f'{hock_mdv}.oz', f'{ik_hock_rot_grp}.ry')

		# ==========================================
		# CREATE STRETCHY IK 
		# ==========================================
		feature_stretch = 'stretch'

		stretch_upper_jnt = self.joint_map['stretch'][0]
		stretch_mid_jnt = self.joint_map['stretch'][1]
		stretch_lower_jnt = self.joint_map['stretch'][2]
		stretch_end_jnt = self.joint_map['stretch'][3]

		stretch_end_loc = bb.create_node('locator', self.rig_name, ['stretch', 'end'], self.number, self.side)
		cmds.matchTransform(stretch_end_loc, stretch_end_jnt)
		bb.create_constraint([ik_ctrl], stretch_end_loc, 'parent')
		cmds.parent(stretch_end_loc, self.ik_mod_grp)

		# Total lenght of each bone 
		limb_len_pma = bb.create_node('plusMinusAverage', self.rig_name, ['limb', 'len'], self.number, self.side)
		for i in range(self.leg_joint_num-1):
			work_jnt = self.joint_map['stretch'][i]
			next_jnt = self.joint_map['stretch'][i+1]
			name = parser.get_base_name(work_jnt)
			bone_dist_dtb = bb.create_node('distanceBetween', self.name, [], self.number, self.side)
			cmds.connectAttr(f'{work_jnt}.worldMatrix', f'{bone_dist_dtb}.inMatrix1')
			cmds.connectAttr(f'{next_jnt}.worldMatrix', f'{bone_dist_dtb}.inMatrix2')
			cmds.connectAttr(f'{work_jnt}.rotatePivotTranslate', f'{bone_dist_dtb}.point1')
			cmds.connectAttr(f'{next_jnt}.rotatePivotTranslate', f'{bone_dist_dtb}.point2')
			cmds.connectAttr(f'{bone_dist_dtb}.distance', f'{limb_len_pma}.input1D[{i}]')
		
		stretch_len_dist = bb.create_node('distanceBetween', self.rig_name, ['stretch', 'len'], self.number, self.side)
		cmds.connectAttr(f'{stretch_upper_jnt}.worldMatrix', f'{stretch_len_dist}.inMatrix1')
		cmds.connectAttr(f'{stretch_end_loc}.worldMatrix', f'{stretch_len_dist}.inMatrix2')
		cmds.connectAttr(f'{stretch_upper_jnt}.rotatePivotTranslate', f'{stretch_len_dist}.point1')
		cmds.connectAttr(f'{stretch_end_loc}.rotatePivotTranslate', f'{stretch_len_dist}.point2')
		# Scale perc compare to the default len
		scale_mdv = bb.create_node('multiplyDivide', self.rig_name, ['scale', 'factor'], self.number, self.side)
		cmds.setAttr(f'{scale_mdv}.op', 2 )

		enabler_cdt = bb.create_node('condition', self.rig_name, ['enabler'], self.number, self.side)
		cmds.setAttr(f'{enabler_cdt}.op', 2 )
		cmds.setAttr( f'{enabler_cdt}.st', 1)
		
		# Connect the stretch distance to the scale factor mdv 
		cmds.connectAttr(f'{stretch_len_dist}.distance', f'{scale_mdv}.i1x')
		# Connect the full leg distance to the scale factor mdv / Divide by default len
		cmds.connectAttr(f'{limb_len_pma}.output1D', f'{scale_mdv}.i2x')

		# Connect the stretch factor to ft
		cmds.connectAttr(f'{scale_mdv}.ox', f'{enabler_cdt}.ft')
		cmds.connectAttr(f'{scale_mdv}.ox', f'{enabler_cdt}.ctr')

		abs_aim = bb.axis_convert(self.aim, 'absolute_letter')
		for i, jnt in enumerate(self.ik[1:]):
			base, element, number, side, suffix = NAMER.extract(jnt)
			# Get orginal translate value
			orig_t_value = cmds.getAttr(f'{jnt}.t{abs_aim}')
			t_mdl = bb.create_node('multDoubleLinear', base, element, number, side)
			cmds.setAttr( f'{t_mdl}.i1', orig_t_value)
			cmds.connectAttr(f'{enabler_cdt}.ocr', f'{t_mdl}.i2')
			cmds.connectAttr(f'{t_mdl}.o', f'{jnt}.t{abs_aim}')
			if self.is_hind:
				cmds.connectAttr(f'{t_mdl}.o', f'{self.driver[i+1]}.t{abs_aim}')

		stretch_switch_bcl = bb.create_node('blendColors', self.rig_name, ['switch'], number, side)
		cmds.connectAttr(f'{scale_mdv}.ox', f'{stretch_switch_bcl}.c1r')
		cmds.setAttr( f'{stretch_switch_bcl}.c2r', 1)
		cmds.connectAttr(f'{stretch_switch_bcl}.opr', f'{enabler_cdt}.ctr', f=True)

		cmds.addAttr( ik_ctrl, ln = feature_stretch, at = 'float', min = 0, max = 1, dv = 1, k = True )
		cmds.connectAttr(f'{ik_ctrl}.{feature_stretch}', f'{stretch_switch_bcl}.blender')

		# ==========================================
		# ADD ROLL JOINT 
		# ==========================================
		joint_pos_index = [0, 3, 0, 0]
		roll_jnt_map = {}

		for i, idx in enumerate(joint_pos_index):
			base, element, number, side, suffix = NAMER.extract(self.joint_chain[idx])
			parent_obj = self.joint_chain[idx]
			if i > 2:
				elem = element + ['follow', 'tip']
			elif i > 1:
				elem = element + ['follow']
			else:
				elem = element + ['roll']		

			roll_jnt = bb.create_node('joint', base, elem, number, side, rad=2)
			cmds.matchTransform(roll_jnt, self.joint_chain[idx])
			cmds.makeIdentity(roll_jnt, a=True, r=True, s=True)		

			if '_'.join(elem) in roll_jnt_map.keys():
				roll_jnt_map['_'.join(elem)].append(roll_jnt)
			else:
				roll_jnt_map['_'.join(elem)] = [roll_jnt]
			
			if i < 2:
				#cmds.parent(roll_jnt, self.joint_chain[idx])
				cmds.parent(roll_jnt, self.jnt_grp)
				bb.create_constraint([self.joint_chain[idx]], roll_jnt, 'point')
			elif i > 2:
				cmds.parent(roll_jnt, roll_jnt_map['follow'])
		
		follow_jnt = roll_jnt_map['follow'][0]
		follow_tip_jnt = roll_jnt_map['follow_tip'][0]
		roll_upper_jnt = roll_jnt_map['roll'][0]
		roll_lower_jnt = roll_jnt_map['roll'][1]

		cmds.delete(cmds.pointConstraint(self.joint_chain[0], self.joint_chain[1], follow_tip_jnt))
		move_coor = [ v* self.move_val for v in self.up_vector ]
		cmds.move(*move_coor, follow_jnt, r=True, os=True, wd=True)

		# ---  Upper Leg Roll ----------------------
		# Name elements come from joint_chain[0] still
		upper_ref_jnt = self.joint_chain[1]
		roll_up_loc = bb.create_node('locator', base, ['roll', 'up'], number, side)
		cmds.matchTransform(roll_up_loc, follow_jnt)
		cmds.parent(roll_up_loc, follow_jnt)
		cmds.move(*move_coor, roll_up_loc, r=True, os=True, wd=True)
		# Aim
		cmds.aimConstraint(upper_ref_jnt, roll_upper_jnt, aim=self.aim_vector, u=self.up_vector, wut = 'object', wuo = roll_up_loc)

		# Create Ik handle
		roll_ikh, roll_up_eff = bb.create_node('ikSc', base, ['follow'], number, side, sj=follow_jnt, ee=follow_tip_jnt)
		#cmds.parent(roll_ikh, upper_ref_jnt)
		cmds.parent(roll_ikh, self.jnt_grp)
		cmds.matchTransform(roll_ikh, upper_ref_jnt)
		for ax in 'XYZ':
			cmds.setAttr( f'{roll_ikh}.poleVector{ax}', 0)
		bb.create_constraint([upper_ref_jnt], roll_ikh, 'pac')
		
		# ---  Lower Leg Roll ----------------------
		lower_ref_jnt = self.joint_chain[3]
		base, element, number, side, suffix = NAMER.extract(lower_ref_jnt)
		roll_lower_loc = bb.create_node('locator', base, ['roll', 'low'], number, side)
		cmds.matchTransform(roll_lower_loc, roll_lower_jnt)
		#cmds.parent(roll_lower_loc, lower_ref_jnt)
		cmds.parent(roll_lower_loc, self.jnt_grp)
		bb.create_constraint([lower_ref_jnt], roll_lower_loc, 'pac')
		cmds.move(*move_coor, roll_lower_loc, r=True, os=True, wd=True)
		# Aim
		neg_aim_vector = [ v*-1 for v in self.aim_vector]
		cmds.aimConstraint(self.joint_chain[2], roll_lower_jnt, aim=neg_aim_vector, u=self.up_vector, wut = 'object', wuo = roll_lower_loc)
		cmds.parent(follow_jnt, self.jnt_grp)

		# Clean up 
		cmds.delete(pv_loc)
		bb.create_constraint([self.ctrl_grp], follow_jnt)
		bb.create_constraint([self.ctrl_grp], self.stretch[0])


# from bbTools.rigs import quadruped_leg_rig as qdr
# reload(qdr)

# l_hind_leg = qdr.QuadrupedLeg(	name = 'leg',
# 								root_jnt = None,
# 								scale = 1,
# 								feature = 'fk',
# 								fkIk_default = 1,
# 								is_hind = True,
# 								aim = 'x',
# 								up = 'z'		
# 								)
# l_hind_leg.build()

# r_hind_leg = qdr.QuadrupedLeg(	name = 'leg',
# 								root_jnt = None,
# 								scale = 1,
# 								feature = 'fk',
# 								fkIk_default = 1,
# 								is_hind = True,
# 								aim = 'x',
# 								up = 'z'		
# 								)
# r_hind_leg.build()

# l_front_leg = qdr.QuadrupedLeg(	name = 'leg',
# 								root_jnt = None,
# 								scale = 1,
# 								feature = 'fk',
# 								fkIk_default = 1,
# 								is_hind = False,
# 								aim = 'x',
# 								up = 'z'		
# 								)
# l_front_leg.build()

# r_front_leg = qdr.QuadrupedLeg(	name = 'leg',
# 								root_jnt = None,
# 								scale = 1,
# 								feature = 'fk',
# 								fkIk_default = 1,
# 								is_hind = False,
# 								aim = 'x',
# 								up = 'z'		
# 								)
# r_front_leg.build()

