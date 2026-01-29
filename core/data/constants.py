import numpy as np

AXIS_MAP = {
	"x":  [(1, 0, 0), 0, 0, 6],
	"-x": [(-1, 0, 0),0, 1, 7],
	"y":  [(0, 1, 0), 1, 2, 0],
	"-y": [(0, -1, 0),1, 3, 1],
	"z":  [(0, 0, 1), 2, 4, 3],
	"-z": [(0, 0, -1),2, 5, 4]
}
# index, letter, absolute_letter, vector, ik_twist_index, ik_twist_up_index, cross_vector, cross_letter
# AXIS_MAP value: [(vector), attr index, ikTwist axis Order, ikTwist up axis Order]
AXIS_NP = {
    'x':  np.array([1, 0, 0]),
    '-x': np.array([-1, 0, 0]),
    'y':  np.array([0, 1, 0]),
    '-y': np.array([0, -1, 0]),
    'z':  np.array([0, 0, 1]),
    '-z': np.array([0, 0, -1])
}
ROTATE_ORDERS = { 'xyz' : 0,
				'yzx' : 1,
				'zxy' : 2,
				'xzy' : 3,
				'yxz' : 4,
				'zyx' : 5}

CONSTRAINT_TYPES = {
	"point": ["ptc", "point"],
	"parent": ["pac", "parent"],
	"orient": ["orc", "orient"],
	"scale": ["scc", "scale"],
	"parentScale": ["psc", "parentScale"]
}

