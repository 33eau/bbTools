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
	'move': [0, 0, 0],
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
	'chin_bp_jnt': {
		'move': [0, -4.2, 11.5],
		'rotate': [-45, 0, 0],
		'scale': 0.1,
		'shape': 'squareRound',
		'parent': 'jaw_bp_jnt'
		},
	# LIP
	'upper_lip_bp_jnt': {
		'move': [0, 0, 1.13],
		'rotate': [0, 0, 0],
		'scale': 1,
		'shape': 'lipUpper',
		'parent': 'jaw_bp_jnt'
		},
	'lower_lip_bp_jnt': {
		'move': [0, 0, 1.5],
		'rotate': [0, 0, 0],
		'scale': 1,
		'shape': 'lipLower',
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