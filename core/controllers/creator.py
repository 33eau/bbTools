#25Oct27
from importlib import reload
import maya.cmds as cmds # type: ignore
from . import shape_library
from . import shape_color 

from ..utils import rig_utils as util
from ..data import constants as constants
from ..naming import namer_factory as naming
from ..naming import parser
from ..naming import current_project

reload(util)
reload(shape_library)
reload(constants)
reload(naming)
reload(parser)
reload(current_project)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

ROTATE_ORDERS = constants.ROTATE_ORDERS
SHAPES = shape_library.SHAPES
COLOR = shape_color.COLORS

#Controller(objects = [], main_ctrl_grp = '', name = '', side = '', offset_names = None, shape = 'crossCircle', color = 'red', scale = 1.0, line_width = 1.0, gimbal = False, connection_type = 'parentScale', rotate_order = 'zyx', lock_attrs = None, shape_rotation = None, temp = False, fk_chain = False , bind_jnt = False, bind_grp = '')
class Controller:
	def __init__(self, 
					objects = [],
					main_ctrl_grp = '',
					name = '',
					side = '',
					offset_names = None,
					shape = 'crossCircle',
					color = 'red',
					scale = 1.0,
					line_width = 1.0,           
					gimbal = False,
					connection_type = 'parentScale',
					rotate_order = 'zyx',
					lock_attrs = ['v'],
					shape_rotation = None, 
					temp = False,
					fk_chain = False , 
					bind_jnt = False,   
					bind_grp = '',
					**kwargs 
					):
		
		self.objects = objects or cmds.ls(sl=True)
		self.main_ctrl_grp = main_ctrl_grp
		self.name = name
		self.side = side
		self.offset_names = offset_names or ['Zro']
		self.shape = shape
		self.color = color
		self.scale = scale
		self.line_width = line_width
		self.gimbal = gimbal
		self.connection_type = connection_type
		self.rotate_order = rotate_order
		self.lock_attrs = lock_attrs or []
		self.shape_rotation = shape_rotation or [0, 0, 0]
		self.temp = temp
		self.fk_chain = fk_chain
			
		ctrls = []
		top_grps = []
		bind_jnts = []
		if self.temp:
			self.objects = cmds.spaceLocator(n='temp_loc')

		for i, obj in enumerate(self.objects):
			if self.name:
				self.side = self.side or ''
				num = f'{i+1:02d}' if len(self.objects) > 1 else ''
				base = parser.get_base_name(self.name)
				element = parser.find_element(self.name) or []
				number = num
				side = self.side
			else:
				base, element, number, side, suffix = NAMER.extract(obj)

			suffix = 'ctl' if NAME_TEMPLATE == 'hatrig' else 'ctrl'
			ctrl_name = NAMER.format(base, element, number, side, suffix)
			#print(ctrl_name)
			
			ctrl = self.create_curve(
								ctrl_name = ctrl_name, 
								shape = self.shape, 
								color=self.color, 
								line_width=self.line_width, 
								scale=self.scale, 
								shape_rotation=self.shape_rotation, 
								rotate_order=self.rotate_order
								)
			ctrls.append(ctrl)

			offset_grps = util.create_offset_group(ctrl, self.offset_names)
			util.snap([obj], offset_grps[ctrl][0])
			top_grps.append(offset_grps[ctrl])

			if self.gimbal:
				gimbal_ctrl = self.create_gimbal_ctrl(ctrl)
				ctrls.append(gimbal_ctrl)
				self.create_connection(obj, gimbal_ctrl)
			else:
				self.create_connection(obj, ctrl)

			for attr in self.lock_attrs:
				cmds.setAttr(f'{ctrl}.{attr}', l=False, k=False)
			
			if self.main_ctrl_grp:
				cmds.parent(offset_grps[ctrl][0], self.main_ctrl_grp)

				
		if self.fk_chain:
			self._connect_fk_chain(ctrls, top_grps)		

		if self.temp:
			cmds.delete(self.objects)
		
		self.ctrls = ctrls
		self.top_grps = top_grps

	def _connect_fk_chain(self, ctrls, top_grps):
		if not self.fk_chain or len(self.objects) <= 1:
			return
		for i in range(0, len(top_grps)-1):
			if self.gimbal:
				parent_ctrl = ctrls[(i*2)+1]
			else:
				parent_ctrl = ctrls[i]
			child_top_grp = top_grps[i+1][0]
			cmds.parent(child_top_grp, parent_ctrl)

	@staticmethod
	def create_curve(ctrl_name='', shape='crossCircle', color='red', line_width=1.0, scale=1.0, shape_rotation=None, rotate_order='zyx'):
		shape_rotation = shape_rotation or [0, 0, 0]
		cv_count = len(SHAPES[shape])
		curve = cmds.curve(p=SHAPES[shape], d=1, n=f'{ctrl_name}')
		#cmds.closeCurve(curve, ch=False, ps=False, rpo=True)
		shape_node = cmds.listRelatives(curve, s=True)[0]
		shape_node = cmds.rename(shape_node, f'{ctrl_name}Shape')
		util.set_color([curve], color)
		cmds.setAttr(f'{shape_node}.lineWidth', line_width)
		util.scale_shape(curve, scale)
		util.rotate_curve(curve, rotation=shape_rotation)
		cmds.setAttr(f'{curve}.ro', ROTATE_ORDERS[rotate_order] )
		return curve
	
	@staticmethod
	def create_gimbal_ctrl(ctrl):
		name = util.get_name(ctrl)
		side = util.get_side(ctrl)
		gimbal_ctrl = cmds.duplicate(ctrl, n = f'{name}Gimbal{side}_ctrl')[0]
		util.scale_shape(gimbal_ctrl, 0.75)
		util.set_color([gimbal_ctrl], 'white')
		gimbal_shape = cmds.listRelatives(gimbal_ctrl, s=True)[0]
		ctrl_shape = cmds.listRelatives(ctrl, s=True, f=True)[0]
		cmds.addAttr( ctrl_shape, ln='gimbal', at='long', min=0, max=1, dv=0, k=True)
		cmds.connectAttr(f'{ctrl_shape}.gimbal', f'{gimbal_shape}.v')
		cmds.parent(gimbal_ctrl, ctrl)

		cmds.addAttr( gimbal_shape, ln = 'rotateOrder', at = 'enum', en = 'xyz:yzx:zxy:xzy:yxz:zyx' , k = True )
		cmds.connectAttr(f'{gimbal_shape}.rotateOrder', f'{gimbal_ctrl}.rotateOrder')

		return gimbal_ctrl

	def create_connection(self, object, ctrl):
		if self.connection_type in ('point', 'parent', 'orient', 'scale', 'parentScale'):
			util.create_constrain(parents=[ctrl], target=object, type=self.connection_type)
		elif self.connection_type == 'direct':
			if self.gimbal:
				cmds.warning(f'Direct Connection works only when moving Gimbal Control: {self.gimbal_ctrl}')
				util.direct_connect([self.gimbal_ctrl], [object])
			else:
				util.direct_connect([ctrl], [object])
		elif self.connection_type == 'matrix_parent':
			util.matrix_constrain(ctrl, object, 'parent')
		elif self.connection_type == 'matrix_point':
			util.matrix_constrain(ctrl, object, 'point')
		elif self.connection_type == 'None':
			pass
		else:
			cmds.warning(f'Unknown connection type: {self.connection_type}')

class SuperRoot:
	super_shape = 'directionalSquare'
	placement_shape = 'arrowOneDir'
	ctrl_color = 'yellow'
		
	def __init__(self, super_root_name='SuperRoot', placement_name='Placement', ctrl_scale=8, line_width =2.0, NAME_TEMPLATE = 'default'):
		self.line_width = line_width
		controllerGrp_name = 'Controllers'
		modulesGrp_name = 'Modules'
		bindGrp_name = 'BindJoints'

		if cmds.objExists(f'{super_root_name}_grp'):
			cmds.warning(f'{super_root_name}_grp already exists.')
			return
		suffix = 'ctl' if NAME_TEMPLATE == 'hatrig' else 'ctrl'
		super_ctrl = self.create_controller(name=super_root_name + '_' + suffix, shape=self.super_shape, scale=ctrl_scale )
		placement_ctrl = self.create_controller(name=placement_name + '_' + suffix, shape=self.placement_shape, scale=ctrl_scale*0.6 )

		super_grp = util.create_group(name=super_root_name, children=[super_ctrl])
		placement_grp = util.create_group(name=placement_name, children=[placement_ctrl], parent_heirarchy = super_ctrl)
		
		controllers_grp = util.create_group(name=controllerGrp_name, parent_heirarchy=super_grp)
		modules_grp = util.create_group(name=modulesGrp_name, parent_heirarchy=super_grp)
		bind_grp = util.create_group(name=bindGrp_name, parent_heirarchy=super_grp)

		util.create_constrain(parents=[placement_ctrl], target=controllers_grp, type='psc')

		self.ctrlGrp = controllers_grp
		self.modGrp = modules_grp
		self.bindGrp = bind_grp
		self.superRootGrp = super_grp

	def create_controller(self, name='', shape='', scale = 1.0):
		ctrl = Controller.create_curve(
				ctrl_name=name, 
				shape=shape,
				color=self.ctrl_color, 
				line_width=self.line_width, 
				scale=scale, 
				shape_rotation=[0, 0, 0], 
				rotate_order='zyx'
				)
		return ctrl
	










