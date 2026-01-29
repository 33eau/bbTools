NAME_TEMPLATES = {
	'default': '{base}{number}{element}{side}_{suffix}',
	'underscore': '{base}_{number}_{side}_{element}_{suffix}',
	'side_prefix': '{side}_{base}_{number}_{element}_{suffix}',
	# customized
	'hatrig': '{side}_{base}_{number}_{element}_{suffix}',
	'type_prefix' : '{suffix}_{base}_{element}_{number}_{side}'
}

SIDE_GROUPS = {
	'L': ['l', 'L', 'LFT', 'lft', 'Left','l_', '_l_'],
	'R': ['r', 'R', 'RGT', 'rgt', 'Right','r_', '_r_'],
	'M': ['m', 'M', 'MID', 'mid', 'Middle','m_', '_m_']
}

SIDE_OUTPUT = {
	'L': {
		'lower': 'l',
		'upper': 'L',
		'3upper': 'LFT',
		'3lower': 'lft',
		'word': 'Left',
	},
	'R': {
		'lower': 'r',
		'upper': 'R',
		'3upper': 'RGT',
		'3lower': 'rgt',
		'word': 'Right',
	},
	'M': {
		'lower': 'm',
		'upper': 'M',
		'3upper': '',
		'3lower': '',
		'word': 'Middle',
	}
}

STRIP_TOKENS = ['offset', 'zro', 'jnt', 'ctrl', 'space', 'bnd']

ELEMENTS = ['Fk', 'Ik', 'Spline', 'Ribbon', 'Tweaker', 'Space', 'Blueprint']

SIDES = ['l_', 'LFT', 'r_', 'RGT']

TYPE_SUFFIX={
'mesh'              	: 'ply',
'joint'             	: 'jnt',
'controller'        	: 'ctrl',
'nurbsCurve'        	: 'crv',
'nurbsSurface'      	: 'nrb',
'skinCluster'       	: 'skc',
'group'         		: 'grp',
'locator'      			: 'loc',
'ikHandle'				: 'ikh',
'ikRp'					: 'ikh',
'ikSc'					: 'ikh',
'ikSpline'				: 'ikh',
'ikEffector'			: 'eff',

'absolute'				: 'abs',
'addDoubleLinear'   	: 'adl',
'blendColors'       	: 'bcl',
'blendMatrix'			: 'bmt',
'blendTwoAttr'      	: 'bta',
'clamp'             	: 'clm',
'closestPointOnMesh'	: 'cpm',
'closestPointOnSurface'	:'cps',
'condition'         	: 'cdt',
'curveInfo'         	: 'cif',
'decomposeMatrix'   	: 'dcp' ,
'distanceBetween'   	: 'dbt',
'distanceDimension' 	: 'ddm',
'follicle'				: 'fol',
'lattice'				: 'lat',
'multDoubleLinear'  	: 'mdl',
'multiplyDivide'    	: 'mdv',
'multMatrix'    		: 'mmt',
'nearestPointOnCurve'	: 'npc',
'pickMatrix'			: 'pmt',
'plusMinusAverage'  	: 'pma',
'pointOnCurveInfo'		: 'poc',
'pointOnSurfaceInfo'	: 'pos',
'remapValue'        	: 'rvl',
'reverse'           	: 'rev',
'setRange'          	: 'srn',
'surfaceInfo'       	: 'sif',

'addMatrix'         	: 'amt' ,
'angleBetween'      	: 'abt' ,
'arrayMapper'       	: 'arm',
'bump2d'            	: 'btw',
'bump3d'            	: 'bth',
'choice'            	: 'chc',
'chooser'           	: 'chs',
'clearCoat'         	: 'clc',
'colorProfile'      	: 'cpf',
'contrast'          	: 'cnt;',
'doubleSwitch'      	: 'dsw',
'framecache'        	: 'frc',
'gammaCorrect'      	: 'gmc',
'heightField'       	: 'hif',
'hsvtoRgb'          	: 'htr',
'2dPlacement'       	: 'twp',
'3dPlacement'       	: 'thp',
'projection'        	: 'pjt',
'particleSampler'   	: 'psp',
'quadSwitch'        	: 'qsw',
'remapColor'        	: 'rcl',
'remapHSV'          	: 'rhs',
'rgbtoHsv'          	: 'rth',
'samplerInfo'       	: 'sif',
'singleSwitch'      	: 'ssw',
'smear'             	: 'smr',
'stencil'           	: 'stc',
'studioClearCoat'   	: 'scc',
'tripleSwitch'      	: 'tsw',
'unitConversion'    	: 'ucv',
'uvChooser'         	: 'uvc',
'vectorProduct'     	: 'vpd',

}
