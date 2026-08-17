# SKIRT RIG II, NPC

# path = r'W:/RIG/__BCK/port/75/BB_RIG/scenes/2026_rebuild_skirt_rig.0012.ma'
# cmds.file(path, open=True, f=True)

import maya.cmds as cmds
from bbTools.core.utils import rig_utils as bb
from bbTools.core.controllers import creator as bc
from bbTools.core.naming import namer_factory as naming
from bbTools.core.naming import current_project
from bbTools.core.naming import parser
from bbTools.core.naming import templates

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

skirt_joints_dict = {
	'l_fnt': 'l_fnt_bp_jnt',
	'l_bck': 'l_bck_bp_jnt',
	'r_bck': 'r_bck_bp_jnt',
	'r_fnt': 'r_fnt_bp_jnt',
	'l_side': 'l_side_bp_jnt',
	'r_side': 'r_side_bp_jnt',
	'fnt' : 'fnt_bp_jnt',
	'bck' : 'bck_bp_jnt'
}

class SkirtRig:
	# Class constants, sharing across all instances of SkirtRig

	MECHANICS_MAP = {
			('l', 'fnt'): [2, 'main'],
			('l', 'bck'): [4, 'main'],

			('r', 'fnt'): [2, 'main'],
			('r', 'bck'): [4, 'main'],

			('l', 'side'): [2, 'side'],
			('r', 'side'): [2, 'side'],

			('c', 'fnt'):  [2, 'main'],
			('c', 'bck'):  [4, 'main']
		}
	# 2 = Greater Than, 4 = Less Than
	# 'main' = primary rotation axis, 'side' = calculated side cross axis

	def __init__( 
			self,
			name = 'skirt',
			rotate_axis = 'x',
			aim_axis = 'y',
			limit_angle = 110,

			# Configurations defaults
			ctrl_shape = 'cube',
			ctrl_color = 'grp',
			scale = 0.1,
			amplifier = 1	
		):

		# Store configuration states
		self.name = name
		self.rotate_axis = rotate_axis
		self.aim_axis = aim_axis
		self.limit_angle = limit_angle

		# Unpack rig presentation controls
		self.ctrl_settings = {
			'offset_names': ['ctrl', 'auto'],
			'shape': ctrl_shape,
			'color': ctrl_color,
			'scale': scale,
			'line_width': 1.0,
			'rotate_order': 'yxz',
			'connection_type': 'parentScale',
			'deg': 1
		}

		self.amplifier = amplifier

		# Derived instance properties
		self.side_axis = bb.axis_convert(axis = self.rotate_axis, return_type = 'cross_letter', up_axis = self.aim_axis)
		self.switch_attr = f'auto{self.name.capitalize()}'
		self.amp_attr = 'amplifier'
	
	def build(self, bottom_crv, driver_jnts, end_jnts, skirt_joints_dict ):
		base, element, global_number, global_side, suffix = NAMER.extract(self.name)
		ctrl_grp = bb.create_node('group', base, ['ctrl'], global_number, global_side)
		mod_grp = bb.create_node('group', base, ['mod'], global_number, global_side)
		jnt_grp = bb.create_node('group', base, ['jnt'], global_number, global_side, p=mod_grp)

		if cmds.objExists('skirt_bp_jnt'):
			cmds.hide('skirt_bp_jnt')
		
		side_drivers, position_locs = self._build_driver_system(bottom_crv, driver_jnts, end_jnts, mod_grp)
	
		blendweight_nodes = []
		front_parents = []
		back_parents = []

		for key, bp_jnt in skirt_joints_dict.items():
			side, region, number = self._get_joint_tokens(key, bp_jnt)
			skirt_jnt, skirt_ctrl, skirt_auto_grp = self._create_base_control(bp_jnt, region, number, side, ctrl_grp, jnt_grp)

			if region != 'side' and side != 'c':
				front_parents.append(skirt_jnt) if region == 'fnt' else back_parents.append(skirt_jnt)

			if side == 'c':
				parents_blend_bwt = self._setup_center_joint(skirt_ctrl, skirt_auto_grp, region, number, side)
				blendweight_nodes.append(parents_blend_bwt)
			else:
				self._setup_side_joint(position_locs[side], skirt_jnt, side_drivers[side], skirt_ctrl, skirt_auto_grp, region, number, side)

		cmds.connectAttr(f'{front_parents[0]}.r{self.rotate_axis}', f'{blendweight_nodes[0]}.input[0]')
		cmds.connectAttr(f'{front_parents[1]}.r{self.rotate_axis}', f'{blendweight_nodes[0]}.input[1]')
		
		cmds.connectAttr(f'{back_parents[0]}.r{self.rotate_axis}', f'{blendweight_nodes[1]}.input[0]')
		cmds.connectAttr(f'{back_parents[1]}.r{self.rotate_axis}', f'{blendweight_nodes[1]}.input[1]')

	def _reorder_joints(self, joint_list):
		left_driver_jnt = None
		right_driver_jnt = None

		for jnt in joint_list:
			side = parser.find_element(jnt, 'sides')
			format_side = parser.format_side(side, 'lower')
			if format_side == 'l':
				left_driver_jnt = jnt
			elif format_side == 'r':
				right_driver_jnt = jnt
			else:
				pass

		return [ left_driver_jnt, right_driver_jnt ]
	
	def _get_joint_tokens(self, key, jnt):
		parts = key.split('_')
		base, element, number, side, suffix = NAMER.extract(jnt)
		side = 'c' if len(parts) == 1 else parts[0]
		region = parts[0] if len(parts) == 1 else parts[1]
		
		return side, region, number
	
	def _build_driver_system(self, bottom_crv, driver_jnts, end_jnts, mod_grp):
		'''
			Create main driver joint for each side and create a locator that stays closest to end_jnt along the bottom_crv
		'''

		side_drivers = {'l': None, 'r': None}
		position_locs = {'l': None, 'r': None}

		sorted_drivers = self._reorder_joints(driver_jnts)
		sorted_ends = self._reorder_joints(end_jnts)

		for driver_i, driver_jnt in enumerate(sorted_drivers):
			end_jnt = sorted_ends[driver_i]

			base, element, number, side, suffix = NAMER.extract(driver_jnt)

			# Create locator and NPC
			position_loc = bb.create_node('locator', self.name, ['pos'], number, side)
			nearest_pos_npc = bb.create_node('nearestPointOnCurve', self.name, ['nearest'], number, side)
			cmds.connectAttr(f'{bottom_crv}.worldSpace[0]', f'{nearest_pos_npc}.inputCurve')

			# Decompose matrix from the end joint 
			end_pos_dcm = bb.create_node('decomposeMatrix', self.name, ['pos'], number, side)
			cmds.connectAttr(f'{end_jnt}.worldMatrix[0]', f'{end_pos_dcm}.inputMatrix')
			cmds.connectAttr(f'{end_pos_dcm}.outputTranslate', f'{nearest_pos_npc}.inPosition')
			cmds.connectAttr(f'{nearest_pos_npc}.position', f'{position_loc}.t')

			# Create skirt main jnt
			skirt_main_jnt = bb.create_node('joint', self.name, ['main'], number, side)
			cmds.matchTransform(skirt_main_jnt, driver_jnt)

			# Inverse matrix to get the actual rotation starting from zero
			skirt_main_ivm = bb.create_node('inverseMatrix', self.name, ['main', 'inv'], number, side)
			cmds.connectAttr(f'{driver_jnt}.worldMatrix[0]', f'{skirt_main_ivm}.inputMatrix')

			skirt_main_mmt = bb.create_node('multMatrix', self.name, ['main', 'mul'], number, side)
			skirt_mtx_val = cmds.getAttr(f'{skirt_main_jnt}.worldMatrix[0]')
			cmds.setAttr( f'{skirt_main_mmt}.matrixIn[0]', skirt_mtx_val, type='matrix')
			cmds.connectAttr(f'{skirt_main_ivm}.outputMatrix', f'{skirt_main_mmt}.matrixIn[1]')

			skirt_inv_ivm = bb.create_node('inverseMatrix', self.name, ['main'], number, side)
			cmds.connectAttr(f'{skirt_main_mmt}.matrixSum', f'{skirt_inv_ivm}.inputMatrix')

			skirt_main_dcm = bb.create_node('decomposeMatrix', self.name, ['main'], number, side)
			cmds.connectAttr(f'{skirt_inv_ivm}.outputMatrix', f'{skirt_main_dcm}.inputMatrix')
			cmds.connectAttr(f'{skirt_main_dcm}.outputRotate', f'{skirt_main_jnt}.rotate')

			cmds.parent(skirt_main_jnt, mod_grp)
			cmds.parent(position_loc, mod_grp)

			formatted_side = parser.format_side(side, 'lower')

			side_drivers[formatted_side] = skirt_main_jnt
			position_locs[formatted_side] = position_loc

		return side_drivers, position_locs

	def _create_base_control(self, source_jnt, region, number, side, ctrl_grp, jnt_grp):
		skirt_jnt = bb.create_node('joint', self.name, [region], number, side)
		cmds.matchTransform(skirt_jnt, source_jnt)
		bb.freeze(skirt_jnt)
		cmds.parent(skirt_jnt, jnt_grp)

		skirt_controller = bc.Controller(
							main_ctrl_grp = ctrl_grp,
							**self.ctrl_settings			
		)
		skirt_ctrl = skirt_controller.ctrls[0]
		skirt_auto_grp = skirt_controller.offset_grps[0][1]

		# Add skirt attr
		bb.attr_separator(skirt_ctrl)
		cmds.addAttr( skirt_ctrl, ln = self.switch_attr, at = 'enum', en='OFF:ON', k=True)
		cmds.setAttr( f'{skirt_ctrl}.{self.switch_attr}', 1)

		cmds.addAttr( skirt_ctrl, ln = self.amp_attr, at = 'float', min = 0.1, dv = self.amplifier, k = True )

		return skirt_jnt, skirt_ctrl, skirt_auto_grp

	def _setup_center_joint(self, skirt_ctrl, skirt_auto_grp, region, number, side):
		parents_blend_bwt = bb.create_node('blendWeighted', self.name, [region, 'blend'], number, side)

		half_val_mdl = bb.create_node('multDoubleLinear', self.name, [region, 'half'], number, side)
		cmds.connectAttr(f'{parents_blend_bwt}.o', f'{half_val_mdl}.i1')
		cmds.setAttr( f'{half_val_mdl}.i2', 0.5)

		amp_mdl = bb.create_node('multDoubleLinear', self.name, [region, 'amp'], number, side)
		cmds.connectAttr(f'{half_val_mdl}.o', f'{amp_mdl}.i1')
		cmds.connectAttr(f'{skirt_ctrl}.{self.amp_attr}', f'{amp_mdl}.i2')

		rotation_clm = bb.create_node('clamp', self.name, [region, 'limit'], number, side)
		limit_extrema = 'min' if self.limit_angle < 0 else 'max'
		cmds.setAttr( f'{rotation_clm}.{limit_extrema}R', self.limit_angle)
		cmds.connectAttr(f'{amp_mdl}.o', f'{rotation_clm}.inputR')
		cmds.connectAttr(f'{rotation_clm}.opr', f'{skirt_auto_grp}.r{self.rotate_axis}')

		return parents_blend_bwt

	def _setup_side_joint(self, position_loc, skirt_jnt, driver_jnt, skirt_ctrl, skirt_auto_grp, region, number, side):
		'''
			Private function to rig the non-centered joints
		'''
		operation_val = self.MECHANICS_MAP[(side, region)][0]
		axis_type = self.MECHANICS_MAP[(side, region)][1]
		rot_ax = self.rotate_axis if axis_type == 'main' else self.side_axis

		skirt_jnt_pos_mtx = cmds.getAttr(f'{skirt_jnt}.worldMatrix[0]')
		loc_dist_dbt = bb.create_node('distanceBetween', self.name, [region, 'dist'], number, side)
		cmds.setAttr( f'{loc_dist_dbt}.inMatrix1', skirt_jnt_pos_mtx, type='matrix')
		cmds.connectAttr(f'{position_loc}.worldMatrix[0]', f'{loc_dist_dbt}.inMatrix2')

		# inv_dir_pma = bb.create_node('plusMinusAverage', self.name, [region, 'inv', 'val'], number, side)
		# cmds.setAttr(f'{inv_dir_pma}.op', 2 )
		# cmds.setAttr( f'{inv_dir_pma}.input1D[0]', 1)
		# cmds.connectAttr(f'{loc_dist_dbt}.distance', f'{inv_dir_pma}.input1D[1]')

		# # Normalize the inverse value, less distance-closer:1, more distance-farther away: 0
		# distance_val = cmds.getAttr(f'{loc_dist_dbt}.distance')
		# normalize_rmv = bb.create_node('remapValue', self.name, [region, 'normalize'], number, side)
		# cmds.connectAttr(f'{inv_dir_pma}.output1D', f'{normalize_rmv}.inputValue')
		# # ⬇️⬇️⬇️ Check if we can use input Max without multiplying -1 instead?
		# cmds.setAttr( f'{normalize_rmv}.inputMin', distance_val * (-1))
		
		# Normalize the distance, less distance-closer:1, more distance-farther away: 0
		distance_val = cmds.getAttr(f'{loc_dist_dbt}.distance')
		normalize_rmv = bb.create_node('remapValue', self.name, [region, 'normalize'], number, side)
		cmds.connectAttr(f'{loc_dist_dbt}.distance', f'{normalize_rmv}.inputValue')
		
		# Yes! We can directly map distance without plusMinusAverage:
		# 0 distance -> 1 (closer), Initial distance -> 0 (farther away)
		cmds.setAttr( f'{normalize_rmv}.inputMin', 0)
		cmds.setAttr( f'{normalize_rmv}.inputMax', distance_val)

		cmds.setAttr( f'{normalize_rmv}.value[0].value_FloatValue', 0)
		cmds.setAttr( f'{normalize_rmv}.value[1].value_FloatValue', 1)

		# Multiply with driver_jnt's rotation
		driver_rot_mdl = bb.create_node('multDoubleLinear', self.name, [region, 'driver', 'rot'], number, side)
		cmds.connectAttr(f'{normalize_rmv}.outValue', f'{driver_rot_mdl}.i1')
		cmds.connectAttr(f'{driver_jnt}.r{rot_ax}', f'{driver_rot_mdl}.i2')

		# Amplifier
		amp_mdl = bb.create_node('multDoubleLinear', self.name, [region, 'amp'], number, side)
		cmds.connectAttr(f'{driver_rot_mdl}.o', f'{amp_mdl}.i1')
		cmds.connectAttr(f'{skirt_ctrl}.{self.amp_attr}', f'{amp_mdl}.i2')

		# Direction muliply
		dir_mul_val = -1 if operation_val == 2 else 1
		dir_mdl = bb.create_node('multDoubleLinear', self.name, [region, 'dir'], number, side)
		cmds.connectAttr(f'{amp_mdl}.o', f'{dir_mdl}.i1')
		cmds.setAttr( f'{dir_mdl}.i2', 1 * dir_mul_val)

		# Condition
		dir_cdt = bb.create_node('condition', self.name, [region, 'dir'], number, side)
		cmds.setAttr(f'{dir_cdt}.op', operation_val )
		cmds.connectAttr(f'{driver_jnt}.r{rot_ax}', f'{dir_cdt}.ft')
		cmds.connectAttr(f'{dir_mdl}.o', f'{dir_cdt}.ctr')
		cmds.setAttr( f'{dir_cdt}.cfr', 0)

		# Main Switch
		switch_mdl = bb.create_node('multDoubleLinear', self.name, [region, 'switch'], number, side)
		cmds.connectAttr(f'{dir_cdt}.ocr', f'{switch_mdl}.i1')
		cmds.connectAttr(f'{skirt_ctrl}.{self.switch_attr}', f'{switch_mdl}.i2')

		# Result
		cmds.connectAttr(f'{switch_mdl}.o', f'{skirt_auto_grp}.r{self.rotate_axis}')

## Example usage
# from bbTools.core import skirt_rig as skr
# reload(skr)

# skirt_joints_dict = {
# 	'l_fnt': 'l_fnt_bp_jnt',
# 	'l_bck': 'l_bck_bp_jnt',
# 	'r_bck': 'r_bck_bp_jnt',
# 	'r_fnt': 'r_fnt_bp_jnt',
# 	'l_side': 'l_side_bp_jnt',
# 	'r_side': 'r_side_bp_jnt',
# 	'fnt' : 'fnt_bp_jnt',
# 	'bck' : 'bck_bp_jnt'
# }

# skirt_rig = skr.SkirtRig( name = 'skirt',
# 						rotate_axis = 'x',
# 						aim_axis = 'y',
# 						limit_angle = -110,

# 						# Configurations defaults
# 						ctrl_shape = 'cube',
# 						ctrl_color = 'grp',
# 						scale = 0.1,
# 						amplifier = 1	
# 					)
# skirt_rig.build( bottom_crv='skirt_bottom_crv', 
# 				driver_jnts = ['l_up_leg_bnd', 'r_up_leg_bnd'], 
# 				end_jnts=['lowLegLFT_bnd', 'lowLegRGT_bnd'], 
# 				skirt_joints_dict = character_skirt_joints
# 				)


# from bbTools.core import skirt_rig as skr
# reload(skr)

# # 1. Define the scene data at the execution level
# character_skirt_joints = {
#     'l_fnt': 'l_fnt_bp_jnt',
#     'l_bck': 'l_bck_bp_jnt',
#     'r_bck': 'r_bck_bp_jnt',
#     'r_fnt': 'r_fnt_bp_jnt',
#     'l_side': 'l_side_bp_jnt',
#     'r_side': 'r_side_bp_jnt',
#     'fnt' : 'fnt_bp_jnt',
#     'bck' : 'bck_bp_jnt'
# }

# # 2. Instantiate and run the rig pipeline cleanly
# skirt_rig = skr.SkirtRig( name = 'skirt',
# 						rotate_axis = 'x',
# 						aim_axis = 'y',
# 						limit_angle = -110,

# 						# Configurations defaults
# 						ctrl_shape = 'cube',
# 						ctrl_color = 'grp',
# 						scale = 0.1,
# 						amplifier = 1	
# 					)
# skirt_rig.build( bottom_crv='skirt_bottom_crv', 
# 				driver_jnts = ['l_up_leg_bnd', 'r_up_leg_bnd'], 
# 				end_jnts=['lowLegLFT_bnd', 'lowLegRGT_bnd'], 
# 				skirt_joints_dict = character_skirt_joints
# 				)