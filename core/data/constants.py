AXIS_MAP = {
	"x":  [(1.0, 0.0, 0.0), 0, 0, 6],
	"-x": [(-1.0, 0.0, 0.0),0, 1, 7],
	"y":  [(0.0, 1.0, 0.0), 1, 2, 0],
	"-y": [(0.0, -1.0, 0.0),1, 3, 1],
	"z":  [(0.0, 0.0, 1.0), 2, 4, 3],
	"-z": [(0.0, 0.0, -1.0),2, 5, 4]
}
# AXIS_MAP value: [(vector), attr index, ikTwist axis Order, ikTwist up axis Order]

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

