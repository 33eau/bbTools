import maya.cmds as cmds
from bbTools import bbRigUtils as bb
from bbTools.bbShapeLib import ctrl_shapes as SHAPES
from bbTools import constants

from functools import partial

COLORS = constants.COLORS

class Controller:
	def __init__(self, 
					objects = None,
					main_ctrl_grp = '',
					name = '',
					Side = '',
					offset_names = None,
					shape = 'crossCircle',
					color = 'red',
					scale = 1.0,
					line_width = 1.0,           
					gimbal = False,
					connection_type = 'parentScale',
					rotate_order = 'zyx',
					lock_attrs = None,
					shape_rotation = None, 
					temp = False,
					fk_chain = False ,      
					**kwargs 
					):
		
		self.objects = objects or cmds.ls(sl=True) or []
		self.offset_names = offset_names or ['Zro']
		self.lock_attrs = lock_attrs or []
		self.shape_rotation = shape_rotation or [0.0, 0.0, 0.0]

	def _build_curve(self, shape, scale, line_width, gimbal):
		for obj in self.objects:
			name = name or bb.get_name(obj)
			side = side or bb.get_side(obj)

			curve = cmds.curve(p=SHAPES[shape], d=1, n=f'{name}{side}_ctrl')
			shape = cmds.listRelative(curve, s=True)
			shape = cmds.rename(shape, f'{name}{side}_ctrlShape')
			set_color(curve, self.color)
			cmds.setAttr(f'{shape}.lineWidth', line_width)
			bb.scale_shape(obj, scale)

			if gimbal:
				pass

	def create_gimbal_ctrl(self, ctrl):
		name = bb.get_name(ctrl)
		side = bb.get_side(ctrl)

		gimbal_ctrl = cmds.duplicate(ctrl, n = f'{name}Gimbal{side}_ctrl')
		bb.scale_shape(gimbal_ctrl, 0.75)
		set_color(gimbal_ctrl, 'white')
		gimbal_shape = cmds.listRelatives(gimbal_ctrl, s=True, f=True)[0]
		ctrl_shape = cmds.listRelatives(ctrl, s=True, f=True)[0]
		cmds.addAttr( ctrl_shape, ln = 'gimbal', at = 'double', min = 0, max = 1, dv = 1 )
		cmds.connectAttr(f'{ctrl_shape}.gimbal', f'{gimbal_shape}.v')
		cmds.parent(gimbal_ctrl, ctrl)

		return gimbal_ctrl


def set_color(ctrls, color):
	ctrls = ctrls or cmds.ls(sl=True) or []
	rgb = COLORS[color]
	for ctrl in ctrls:
		shape = cmds.listRelatives(ctrl, s=True, f=True)
		cmds.setAttr(f'{shape}.ove',1)
		cmds.setAttr(f'{shape}.overrideRGBColors',1)
		cmds.setAttr(f'{shape}.overrideColorRGB', *rgb)

		cmds.setAttr(f'{ctrl}.ove',1)
		cmds.setAttr(f'{ctrl}.overrideRGBColors',1)
		cmds.setAttr(f'{ctrl}.overrideColorRGB', *rgb)

def colorUI():
	window = cmds.window( title="bbColorPalette", iconName='Short Name', w = 448, h = 96 )
	cmds.gridLayout( h = 13, w = 13, nr = 3, nc = 14)
	for col in COLORS.keys():
		cmds.button( label='', bgc = COLORS[col], c = partial( set_color, color = col ), al = col )
		print( col )
	cmds.showWindow( window )
		
		
		