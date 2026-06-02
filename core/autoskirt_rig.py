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

CTRL_SHAPE = 'cube'
CTRL_COLOR = 'grp'
SCALE = 0.1
AMP_ATTR = 'amplifier'
AMPLIFIER = 0.6

name = 'skirt'
top_crv = 'skirt_top_crv'
bottom_crv = 'skirt_bottom_crv'
driver_jnts = ['l_up_leg_bnd', 'r_up_leg_bnd']
end_jnts = ['lowLegLFT_bnd', 'lowLegRGT_bnd']
rotate_axis = 'x'
aim_axis = 'y'
limit_angle = -110
rotate_out_degree = 10
bind_parent = ''

def reorder_joints(joint_list):
	for jnt in joint_list:
		side = parser.find_element(jnt, 'sides')
		format_side = parser.format_side(side, style='3upper')
		if format_side == 'LFT':
			left_jnt = jnt
		else:
			right_jnt = jnt
	lr_jnts = [left_jnt, right_jnt]

	return(lr_jnts)

driver_jnts = reorder_joints(driver_jnts)
end_jnts = reorder_joints(end_jnts)

# Axis Convert
aim_letter = bb.axis_convert(axis = aim_axis, return_type = 'absolute_letter')
rot_letter = bb.axis_convert(axis = rotate_axis, return_type = 'absolute_letter')
rot_vector = bb.axis_convert(axis = rotate_axis, return_type = 'vector')
side_axis = bb.axis_convert(axis = rotate_axis, return_type = 'cross_letter', up_axis = aim_axis)


SKIRT_JNTS = {
	'l_fnt': 'l_fnt_bp_jnt',
	'l_bck': 'l_bck_bp_jnt',
	'r_bck': 'r_bck_bp_jnt',
	'r_fnt': 'r_fnt_bp_jnt',
	'l_side': 'l_side_bp_jnt',
	'r_side': 'r_side_bp_jnt',
	'fnt' : 'fnt_bp_jnt',
	'bck' : 'bck_bp_jnt'
}

SIDE_DRIVER = {
	'l' : None,
	'r' : None,
	'c' : 'both'
}

OPERATION_MAP = {
	('l', 'fnt'): 2,
	('l', 'bck'): 4,

	('r', 'fnt'): 2,
	('r', 'bck'): 4,

	('l', 'side'): 2,
	('r', 'side'): 2,

	('c', 'fnt'): 2,
	('c', 'bck'): 4
}
#2 is 'Greater than' for condition node
#4 is 'Less than' for condition node

AXIS_MAP = {
	'fnt' : rotate_axis,
	'bck' : rotate_axis,
	'side' : side_axis
}
base, element, number, side, suffix = NAMER.extract(name)
ctrl_grp = bb.create_node('group', base, ['ctrl'], number, side)
mod_grp = bb.create_node('group', base, ['mod'], number, side)

position_locs = {}

for driver_i, driver_jnt in enumerate(driver_jnts):
	end_jnt =  end_jnts[driver_i]
	base, element, number, side, suffix = NAMER.extract(driver_jnt)
	side = parser.format_side(side, 'lower')
	pos_loc = bb.create_node('locator', name, ['pos'], number, side)

	# Create NPC
	loc_npc = bb.create_node('nearestPointOnCurve', name, ['pos'], number, side)
	cmds.connectAttr(f'{bottom_crv}.worldSpace[0]', f'{loc_npc}.inputCurve')

	# Decompose Mtx for driver_end
	driver_end_dcm = bb.create_node('decomposeMatrix', name, ['end', 'pos'], number, side)
	cmds.connectAttr(f'{end_jnt}.worldMatrix[0]', f'{driver_end_dcm}.inputMatrix')
	cmds.connectAttr(f'{driver_end_dcm}.outputTranslate', f'{loc_npc}.inPosition')
	cmds.connectAttr(f'{loc_npc}.position', f'{pos_loc}.t')

	skirt_main_jnt = bb.create_node('joint', name, ['main'], number, side)
	cmds.matchTransform(skirt_main_jnt, driver_jnt)

	## Create skirt_main_jnt
	# Inverse Matrix to get the actual rotation from current rotation
	skirt_main_ivm = bb.create_node('inverseMatrix', name, ['main', 'inv'], number, side)
	cmds.connectAttr(f'{driver_jnt}.worldMatrix[0]', f'{skirt_main_ivm}.inputMatrix')

	skirt_main_mmt = bb.create_node('multMatrix', name, ['main', 'mul'], number, side)
	skirt_main_mtx_val = cmds.getAttr(f'{driver_jnt}.worldMatrix[0]')
	cmds.setAttr( f'{skirt_main_mmt}.matrixIn[0]', skirt_main_mtx_val, type='matrix')
	cmds.connectAttr(f'{skirt_main_ivm}.outputMatrix', f'{skirt_main_mmt}.matrixIn[1]')

	skirt_inv_ivm = bb.create_node('inverseMatrix', name, ['main'], number, side)
	cmds.connectAttr(f'{skirt_main_mmt}.matrixSum', f'{skirt_inv_ivm}.inputMatrix')

	skirt_main_dcm = bb.create_node('decomposeMatrix', name, ['main'], number, side)
	cmds.connectAttr(f'{skirt_inv_ivm}.outputMatrix', f'{skirt_main_dcm}.inputMatrix')
	cmds.connectAttr(f'{skirt_main_dcm}.outputRotate', f'{skirt_main_jnt}.rotate')

	SIDE_DRIVER[side] = skirt_main_jnt
	print(side)
	print(skirt_main_jnt)

	position_locs[side] = pos_loc
	cmds.parent(pos_loc, mod_grp)

position_locs['c'] = 'both' # maybe change to blendedWeight name?

blendweight_bwts = []
center_auto_grp =[]

for key, jnt in SKIRT_JNTS.items():
	SKIRT_MAP = {}
	parts = key.split('_')

	if len(parts) == 1:
		side = 'c'
		region = parts[0]
		rotate_axis = AXIS_MAP[region.split('_')[-1]]
		skirt_jnt = bb.create_node('joint', name, [region], number, side)
		cmds.matchTransform(skirt_jnt, jnt)
		bb.freeze(skirt_jnt)
		
		blendweight_bwt = bb.create_node('blendWeighted', name, [region], number, side)	
		
		amp_mdl = bb.create_node('multDoubleLinear', name, [region, 'amp'], number, side)
		cmds.connectAttr(f'{blendweight_bwt}.o', f'{amp_mdl}.i1')
		# ⬇️⬇️⬇️⬇️ center joint amp
		#cmds.setAttr( f'{amp_mdl}.i2', 0.5)	
		
		rot_clm = bb.create_node('clamp', name, [region, 'limit'], number, side)
		limit = 'min' if limit_angle < 0 else 'max'
		cmds.setAttr( f'{rot_clm}.{limit}R', limit_angle)
		cmds.connectAttr(f'{amp_mdl}.o', f'{rot_clm}.inputR')
		blendweight_bwts.append(blendweight_bwt)

		skirt_controller = bc.Controller(objects = [skirt_jnt],
							main_ctrl_grp = ctrl_grp,
							offset_names = ['ctrl', 'auto'],
							shape = CTRL_SHAPE,
							color = CTRL_COLOR,
							scale = SCALE,
							line_width = 1.0,
							gimbal = False,
							connection_type = 'parentScale',
							rotate_order = 'yxz',
							lock_attrs = None,
							temp = False,
							fk_chain = False ,
							bind_jnt = False,
							bind_grp = bind_parent,
							deg=1)
	
		skirt_ctrl = skirt_controller.ctrls[0]
		skirt_ctrl_grp = skirt_controller.offset_grps[0][0]
		skirt_auto_grp = skirt_controller.offset_grps[0][1]

		cmds.connectAttr(f'{rot_clm}.opr', f'{skirt_auto_grp}.r{rotate_axis}')
		cmds.addAttr( skirt_ctrl, ln = AMP_ATTR, at = 'float', min = 0.01, dv = AMPLIFIER, k = True )
		cmds.connectAttr(f'{skirt_ctrl}.{AMP_ATTR}', f'{amp_mdl}.i2')
		center_auto_grp.append(skirt_auto_grp)
		continue

	else:
		side, region = parts
	
	SKIRT_MAP[key] = {
		'jnt' : jnt,
		'driver': SIDE_DRIVER[side],
		'direction' : OPERATION_MAP[(side, region)],
		'axis' : AXIS_MAP[region],
		'loc' : position_locs[side]
	}
	#print(SKIRT_MAP)
	
	pos_loc = SKIRT_MAP[key]['loc']
	driver_jnt = SKIRT_MAP[key]['driver']
	rotate_axis = SKIRT_MAP[key]['axis']
	op_val = SKIRT_MAP[key]['direction']

	skirt_jnt = bb.create_node('joint', name, [region], number, side)
	cmds.matchTransform(skirt_jnt, jnt)
	bb.freeze(skirt_jnt)
	
	skirt_controller = bc.Controller(objects = [skirt_jnt],
								main_ctrl_grp = ctrl_grp,
								offset_names = ['ctrl', 'auto'],
								shape = CTRL_SHAPE,
								color = CTRL_COLOR,
								scale = SCALE,
								line_width = 1.0,
								gimbal = False,
								connection_type = 'parentScale',
								rotate_order = 'yxz',
								lock_attrs = None,
								temp = False,
								fk_chain = False ,
								bind_jnt = False,
								bind_grp = '',
								deg=1)
	
	skirt_ctrl = skirt_controller.ctrls[0]
	skirt_ctrl_grp = skirt_controller.offset_grps[0][0]
	skirt_auto_grp = skirt_controller.offset_grps[0][1]

	skirt_jnt_pos_mtx = cmds.getAttr(f'{skirt_jnt}.worldMatrix[0]')
	base_dist_dbt = bb.create_node('distanceBetween', name, [region, 'dist'], number, side)
	cmds.setAttr(f'{base_dist_dbt}.inMatrix1', skirt_jnt_pos_mtx, type='matrix')
	cmds.connectAttr(f'{pos_loc}.worldMatrix[0]', f'{base_dist_dbt}.inMatrix2')

	inv_dir_pma = bb.create_node('plusMinusAverage', name, [region, 'inv', 'dir'], number, side)
	cmds.setAttr(f'{inv_dir_pma}.op', 2 )
	cmds.setAttr( f'{inv_dir_pma}.input1D[0]', 1)
	cmds.connectAttr(f'{base_dist_dbt}.distance', f'{inv_dir_pma}.input1D[1]')
	
	# Normalize the inverse value, less distance-closer:1, more distance-further away:0
	distance_val = cmds.getAttr(f'{base_dist_dbt}.distance')
	normalize_rmv = bb.create_node('remapValue', name, [region, 'normalize'], number, side)
	cmds.connectAttr(f'{inv_dir_pma}.output1D', f'{normalize_rmv}.inputValue')
	cmds.setAttr( f'{normalize_rmv}.inputMin', distance_val * (-1))
	cmds.setAttr( f'{normalize_rmv}.value[0].value_FloatValue', 1)
	cmds.setAttr( f'{normalize_rmv}.value[1].value_FloatValue', 0)

	print('BEFORE CONNECT')
	print(driver_jnt)
	print('===================')
	# Multiply the original rotation from the driver joint
	driver_rot_mdl = bb.create_node('multDoubleLinear', name, [region, 'driver', 'rot'], number, side)
	cmds.connectAttr(f'{driver_jnt}.r{rotate_axis}', f'{driver_rot_mdl}.i1')
	cmds.connectAttr(f'{normalize_rmv}.outValue', f'{driver_rot_mdl}.i2')

	# Amplifier
	amp_mdl = bb.create_node('multDoubleLinear', name, [region, 'amp'], number, side)
	cmds.connectAttr(f'{driver_rot_mdl}.o', f'{amp_mdl}.i1')
	# ⬇️⬇️⬇️ Add Amp Attr here
	#cmds.setAttr( f'{amp_mdl}.i2', 1 * dir_mul_val)

	dir_mul_val = -1 if op_val == 2 else 1
	dir_mdl = bb.create_node('multDoubleLinear', name, [region, 'dir'], number, side)
	cmds.addAttr( skirt_ctrl, ln = AMP_ATTR, at = 'float', min = 0.01, dv = AMPLIFIER, k = True )
	cmds.connectAttr(f'{skirt_ctrl}.{AMP_ATTR}', f'{dir_mdl}.i1')
	cmds.setAttr( f'{dir_mdl}.i2', 1 * dir_mul_val)
	cmds.connectAttr(f'{dir_mdl}.o', f'{amp_mdl}.i2')

	# Direction
	dir_cdt = bb.create_node('condition', name, [region, 'dir'], number, side)
	cmds.setAttr(f'{dir_cdt}.op', op_val )
	cmds.connectAttr(f'{driver_jnt}.r{rotate_axis}', f'{dir_cdt}.ft')
	cmds.connectAttr(f'{amp_mdl}.o', f'{dir_cdt}.ctr')
	cmds.setAttr( f'{dir_cdt}.cfr', 0)

	# THIS CAN GO TO THE SKIRT JOINT NOW.
	cmds.connectAttr(f'{dir_cdt}.ocr', f'{skirt_auto_grp}.r{rot_letter}')


for i, bwt in enumerate(blendweight_bwts):
	region = parser.find_element(bwt, element_list = templates.REGIONS)[0]
	rot_ax = AXIS_MAP[region]
	l_jnt =  NAMER.format(name, [region], number, 'l', 'jnt')
	r_jnt =  NAMER.format(name, [region], number, 'r', 'jnt')
	cmds.connectAttr(f'{l_jnt}.r{rotate_axis}', f'{bwt}.input[0]')
	cmds.connectAttr(f'{r_jnt}.r{rotate_axis}', f'{bwt}.input[1]')

