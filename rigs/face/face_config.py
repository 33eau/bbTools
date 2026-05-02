'''
26Feb18
Face Rig Configuration Data
Centralized dictionary for basic joints, shape and transform data.
'''
FACE_CTRL_GRP = 'face_ctrl_grp'

# Default value to fall back on if no custom data needed.
DEFAULT_SETTINGS = {
	'shape': 'crossCircle',
	'scale': 0.1,
	'rotate': [90, 0, 0],
	'move': [0, 0, 0.5],
	'parent': FACE_CTRL_GRP
}

# Key: Blueprint Joint Name
# Value: Dictionary of custom data
BASIC_BONES = {
	'skull_bp_jnt': {
		'move': [0, 0, 0],
		'rotate': [0, 0, 0],
		'scale': 2,
		'shape': 'squareRound',
		'parent': FACE_CTRL_GRP
		},
	'jaw_bp_jnt': {
		'move': [0, -4.5, 11.25],
		'rotate': [-20, 0, 0],
		'scale': 0.75,
		'shape': 'chin',
		'parent': FACE_CTRL_GRP
		},
	'eyebrow_mid_bp_jnt': {
		'move': [0, 0, 0.1],
		'rotate': [90, 0, -45],
		'scale': 0.1,
		'shape': 'squareRound',
		'parent': 'skull_bp_jnt'
		},
	'chin_bp_jnt': {
		'move': [0, -4.2, 11.5],
		'rotate': [-45, 0, 0],
		'scale': 0.1,
		'shape': 'squareRound',
		'parent': 'jaw_bp_jnt'
		},
	#NOSE
	'nosebridge_bp_jnt': {
		'move': [0, 0, 0.75],
		'rotate': [0, 0, 0],
		'scale': 0.07,
		'shape': 'bridge',
		'parent': 'skull_bp_jnt'
		},
	'nose_base_bp_jnt': {
		'move': [0, 0, 2.2],
		'rotate': [0, 27, 90],
		'scale': 0.2,
		'shape': 'triangleRound',
		'parent': 'skull_bp_jnt'
		},
	'l_nostril_bp_jnt': {
		'move': [0.5, 0, 0],
		'rotate': [0, 0, 90],
		'scale': 0.1,
		'shape': 'crossCircle',
		'parent': 'nose_base_bp_jnt'
		},
	'r_nostril_bp_jnt': {
		'move': [0.5, 0, 0],
		'rotate': [0, 0, 90],
		'scale': 0.1,
		'shape': 'crossCircle',
		'parent': 'nose_base_bp_jnt'
		},
	# UPPER CHEEK
	'l_upper_cheek_in_bp_jnt': {
		'move': [0, 0, 0],
		'rotate': [90, 0, 0],
		'scale': 0.1,
		'shape': 'crossCircle',
		'parent': 'skull_bp_jnt'
		},
	'l_upper_cheek_mid_bp_jnt': {
		'move': [0, 0, 0],
		'rotate': [90, 0, 0],
		'scale': 0.1,
		'shape': 'crossCircle',
		'parent': 'skull_bp_jnt'
		},
	'l_upper_cheek_out_bp_jnt': {
		'move': [0, 0, 0],
		'rotate': [90, 0, 0],
		'scale': 0.1,
		'shape': 'crossCircle',
		'parent': 'skull_bp_jnt'
		},
	'r_upper_cheek_in_bp_jnt': {
		'move': [0, 0, 0],
		'rotate': [90, 0, 0],
		'scale': 0.1,
		'shape': 'crossCircle',
		'parent': 'skull_bp_jnt'
		},
	'r_upper_cheek_mid_bp_jnt': {
		'move': [0, 0, 0],
		'rotate': [90, 0, 0],
		'scale': 0.1,
		'shape': 'crossCircle',
		'parent': 'skull_bp_jnt'
		},
	'r_upper_cheek_out_bp_jnt': {
		'move': [0, 0, 0],
		'rotate': [90, 0, 0],
		'scale': 0.1,
		'shape': 'crossCircle',
		'parent': 'skull_bp_jnt'
		},
	# CHEEK
	'l_cheek_bp_jnt': {
		'move': [0, 0, 3.3],
		'rotate': [0, 0, 0],
		'scale': 0.1,
		'shape': 'sphere',
		'parent': 'both'
		},
	'r_cheek_bp_jnt': {
		'move': [0, 0, 3.3],
		'rotate': [0, 0, 0],
		'scale': 0.1,
		'shape': 'sphere',
		'parent': 'both'
		},
	# JAWLINE
	'l_jawline_bp_jnt': {
		'move': [0, 0, 0.5],
		'rotate': [0, 0, 90],
		'scale': 0.2,
		'shape': 'triangleRound',
		'parent': 'jaw_bp_jnt'
		},
	'r_jawline_bp_jnt': {
		'move': [0, 0, 0.5],
		'rotate': [0, 0, 90],
		'scale': 0.2,
		'shape': 'triangleRound',
		'parent': 'jaw_bp_jnt'
		}
} 

LIP_SETTINGS = {
	'shape': 'squareRound',
	'scale': 0.2,
	'rotate': [90, 0, 45],
	'move': [0, 0, 0.5],
	'main_upper_move': [0, 0, 0.95],
	'main_lower_move': [0, 0, 1.3],
	'upper_shape': 'lipUpper',
	'upper_move': [0, 0.5, 0.75],
	'upper_rotate': [90, 0, 0] ,
	'lower_shape': 'lipLower',
	'lower_move': [0, -0.2, 0.75],
	'lower_rotate': [90, 0, 0],
}

EYEBROWS_SETTINGS={
	'ctrl_rotate': [90, 0, 0],
	'part': ['in', 'mid', 'out'],
	'default_values': [0.5, 0.8, 0.5],
	'mid_ctrl_shape' : 'squareRound'
}

EYELIDS_SETTINGS = {
	'corners_elem': ['crnr_in', 'crnr_out'],
	'corner_move': [[-0.25, 0, 0.25], [0.25, 0, 0.5]],
	'main_tweakers_move': [[0, 0.25, 0.75], [0, 0.25, 0.25]],
	'lid_ctrl_shape': 'circleHalfRound',
	'lid_ctrl_scale': 0.03,
	'follow_dv' : [0.85, 0.9]

}