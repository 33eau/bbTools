AXIS_MAP = {
	"x": (1.0, 0.0, 0.0),
	"-x": (-1.0, 0.0, 0.0),
	"y": (0.0, 1.0, 0.0),
	"-y": (0.0, -1.0, 0.0),
	"z": (0.0, 0.0, 1.0),
	"-z": (0.0, 0.0, -1.0)
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

