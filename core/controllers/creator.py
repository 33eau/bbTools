#25Oct27
from importlib import reload
import maya.cmds as cmds # type: ignore
from . import shape_library
from . import shape_color 

from ..utils import rig_utils as bb
from ..data import constants as constants
from ..naming import namer_factory as naming
from ..naming import parser
from ..naming import current_project

reload(bb)
reload(shape_library)
reload(constants)
reload(naming)
reload(parser)
reload(current_project)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)
SUFFIX = 'ctrl'

CUSTOM_TEMPLATE = 'hatrig'
CUSTOM_SUFFIX = 'ctl'


def get_naming_data(obj=None, name_input=None, side_input =None, index=0, multiple = False, gimbal = False):
	if name_input:
		base = parser.get_base_name(name_input)
		element = parser.find_element(name_input) or []
		number = f'{index+1:02d}' if multiple else None
		side = side_input or None
	else:
		base, element, number, side, suffix = NAMER.extract(obj)

	if gimbal:
		element = element.append('Gimbal')

	suffix = CUSTOM_SUFFIX if NAME_TEMPLATE == CUSTOM_TEMPLATE else SUFFIX
	ctrl_name = NAMER.format(base, element, number, side, suffix)

	return {
	'ctrl_name': ctrl_name,
	'base': base,
	'element': element,
	'side': side,
	'number': number,
	'suffix': suffix
	}

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
					rotate_order = 'xyz',
					lock_attrs = None,
					shape_rotation = None, 
					temp = False,
					fk_chain = False ,
					run = True,
					log = False,
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
		self.shape_rotation = shape_rotation or [0, 0, 0]
		self.temp = temp
		self.fk_chain = fk_chain

		self.lock_attrs = lock_attrs + ['v'] if lock_attrs else ['v']

		self.ctrls = []
		self.offset_grps = []

		if run:
			self.build()
			if log:
				print( f'CTRL: {self.ctrls}')
				print( f'GRPS: {self.offset_grps}')

	def build(self):
		cmds.undoInfo(openChunk=True, chunkName="CreateController")
		targets = self.objects
		try:
			if self.temp:
				targets = cmds.spaceLocator(n='temp_loc_01')

			for i, target in enumerate(targets):
				multiple = len(self.objects) > 1
				name_data = get_naming_data(target, self.name, self.side, i, multiple)
				ctrl = self.create_curve(
								ctrl_name = name_data['ctrl_name'], 
								shape = self.shape, 
								color=self.color, 
								line_width=self.line_width, 
								scale=self.scale, 
								shape_rotation=self.shape_rotation, 
								rotate_order=self.rotate_order
								)
				self.ctrls.append(ctrl)

				offset_groups = bb.create_offset_group(ctrl, self.offset_names)
				top_grp = offset_groups[ctrl][0]
				self.offset_grps.append(offset_groups[ctrl])
				bb.snap([target], top_grp)

				active_ctrl = ctrl
				if self.gimbal:
					active_ctrl = self.create_gimbal_ctrl(ctrl)
					self.ctrls.append(active_ctrl)
				
				self.create_connection(target, active_ctrl)
				
				for attr in self.lock_attrs:
					cmds.setAttr(f'{ctrl}.{attr}', l=False, k=False)

				if self.main_ctrl_grp and cmds.objExists(self.main_ctrl_grp):
					cmds.parent(top_grp, self.main_ctrl_grp)

			if self.fk_chain:
				self._connect_fk_chain()
			
			if self.temp:
				cmds.delete(targets)
		finally:
			cmds.undoInfo(closeChunk=True)
		return self.ctrls

	def _connect_fk_chain(self):
		if len(self.objects) <= 1:
			return
		step = 2 if self.gimbal else 1
		for i in range(0, len(self.offset_grps) - 1):
			parent_ctrl = self.ctrls[(i * step) + (step - 1)]
			child_grp = self.offset_grps[i + 1][0]
			cmds.parent(child_grp, parent_ctrl)

	@staticmethod
	def create_curve(ctrl_name='', 
					shape='crossCircle', 
					color='red', 
					line_width=1.0, 
					scale=1.0, 
					shape_rotation=None, 
					rotate_order='zyx'):
		
		points = shape_library.SHAPES.get(shape, shape_library.SHAPES['crossCircle'])
		crv = cmds.curve(p=points, d=1)
		crv = cmds.rename(crv, ctrl_name)
		shp = cmds.listRelatives(crv, s=True)[0]

		bb.set_color([crv], color)
		bb.scale_shape(crv, scale)
		bb.rotate_curve(crv, rotation=shape_rotation)
		cmds.setAttr( f'{shp}.lineWidth', line_width)

		ro_value = bb.constants.ROTATE_ORDERS.get(rotate_order, 0)
		cmds.setAttr(f'{crv}.rotateOrder', ro_value)

		return crv

	def create_gimbal_ctrl(self, ctrl, name_data):
		if not name_data:
			name_data = self.get_naming_data(obj=ctrl, gimbal=True)
		gimbal_name = name_data['ctrl_name']
		gimbal = cmds.duplicate(ctrl)[0]
		gimbal = cmds.rename(gimbal, gimbal_name)

		bb.scale_shape(gimbal, 0.75)
		bb.set_color([gimbal], 'white')

		# Setup Visibility Switch
		main_shp = cmds.listRelatives(ctrl, s=True)[0]
		gim_shp = cmds.listRelatives(gimbal, s=True)[0]
		
		if not cmds.attributeQuery('gimbal', n=main_shp, ex=True):
			cmds.addAttr(main_shp, ln='gimbal', at='long', min=0, max=1, dv=0, k=True)
		
		cmds.connectAttr(f'{main_shp}.gimbal', f'{gim_shp}.v')
		cmds.parent(gimbal, ctrl)
		return gimbal	

	def create_connection(self, object, ctrl):
		if self.connection_type == 'None':
			return
		
		if self.connection_type in ('point', 'parent', 'orient', 'scale', 'parentScale'):
			bb.create_constrain(parents=[ctrl], target=object, type=self.connection_type)
		elif self.connection_type == 'direct':
			if self.gimbal:
				cmds.warning(f'Direct Connection works only when moving Gimbal Control: {self.gimbal_ctrl}')
				bb.direct_connect([self.gimbal_ctrl], [object])
			else:
				bb.direct_connect([ctrl], [object])
		elif 'matrix' in self.connection_type:
			mtx_type = self.connection_type.split('_')[-1]
			bb.matrix_constrain(ctrl, object, mtx_type)
		else:
			cmds.warning(f'Unknown connection type: {self.connection_type}')

class SuperRoot:
	def __init__(self, super_name='SuperRoot', placement_name='Placement', ctrl_scale=8, line_width = 2.0, **kwargs):
		
		self.super_name = super_name
		self.placement_name =  placement_name
		self.ctrl_scale =  ctrl_scale * 4
		self.line_width = line_width

		self.super_shape = kwargs.get('super_shape', 'directionalSquare')
		self.placement_shape = kwargs.get('placement_shape', 'arrow1dir')
		self.ctrl_color = kwargs.get('ctrl_color', 'yellow')

		self.super_group_name = kwargs.get('super_group_name', 'Rig')
		self.controller_group_name = kwargs.get('controller_group_name', 'Controllers')
		self.modules_group_name = kwargs.get('modules_group_name', 'Modules')
		self.bind_group_name = kwargs.get('bind_group_name', 'BindJoints')
		self.scale_attr = kwargs.get('scale_attr', 'scale_uniform')

		self.super_grp = None
		self.placement_grp = None
		self.ctrl_grp = None
		self.mod_grp = None
		self.bind_grp = None

		self.super_ctrl = None
		self.placement_ctrl = None
		self.scale_uniform = None

		self.build()

	def build(self):
		top_grp_name = NAMER.format(self.super_group_name, None, None, None, 'grp')
		if cmds.objExists(top_grp_name):
			cmds.warning(f'{top_grp_name} already exists.')
			return
		
		self.super_grp = bb.create_node('group', self.super_group_name)
		self.super_ctrl = self._create_master_controler(self.super_name, self.super_shape, self.ctrl_scale)
		cmds.parent(self.super_ctrl, self.super_grp)
		
		self.placement_grp = bb.create_node('group', self.placement_name, p = self.super_ctrl)
		self.placement_ctrl = self._create_master_controler(self.placement_name, self.placement_shape, self.ctrl_scale * 0.6)
		cmds.parent(self.placement_ctrl, self.placement_grp)

		self.ctrl_grp = bb.create_group(name=self.controller_group_name, parent_heirarchy=self.super_grp)
		self.mod_grp = bb.create_group(name=self.modules_group_name, parent_heirarchy=self.super_grp)
		self.bind_grp = bb.create_group(name=self.bind_group_name, parent_heirarchy=self.super_grp)

		cmds.addAttr( self.super_ctrl, ln = self.scale_attr, at = 'float', dv = 1, k = True )
		self.scale_uniform = f'{self.super_ctrl}.{self.scale_attr}'
		bb.matrix_constrain(parent=self.placement_ctrl, target=self.ctrl_grp, type='parent')

	def _create_master_controler(self, base_name = None, shape = None, scale = 1.0):
		name_data = get_naming_data(name_input=base_name)
		ctrl = Controller.create_curve(
						ctrl_name=name_data['ctrl_name'], 
						shape=shape,
						color=self.ctrl_color, 
						line_width=self.line_width, 
						scale=scale, 
						shape_rotation=[0, 0, 0], 
						rotate_order='zxy'
						)
		# lock scale
		lock_attrs = ['sx','sy','sz','v']
		for attr in lock_attrs:
			cmds.setAttr(f'{ctrl}.{attr}', l=False, k=False)
		return ctrl
	
class SingleControl:
	def __init__(self, target_obj=None, bind_parent='', ctrl_parent='', global_scale = '', upper_driver = '', delete_temp = False, color = '',  **kwargs):
		self.target_obj =  target_obj
		self.bind_parent = bind_parent
		self.ctrl_parent =  ctrl_parent
		self.global_scale =  global_scale
		self.upper_driver =  upper_driver
		self.delete_temp =  delete_temp
		self.color = color

		self.side = kwargs.get('side', None)
		self.create_joint = kwargs.get('create_joint', True)

		if not self.side:
			self.side = parser.find_element(self.target_obj, 'sides')
			if self.side:
				if not self.color:
					formatted_side = parser.format_side(self.side, 'upper')
					default_color = shape_color.CTRL_COLOR[formatted_side]
			else:
				if not self.color:
					default_color = 'yellow'
				else:
					default_color = self.color

		self.color = kwargs.get('color', default_color)
		
		# Return result
		self.single_ctrl = None
		self.offset_grps = None
		self.bind_jnt = None

		if target_obj:
			self.build(**kwargs)

	def build(self, **kwargs):
		name_data = get_naming_data(obj=self.target_obj)
		base, element, number, side, suffix = NAMER.extract(self.target_obj)
		element = element if element else []
		drive_target = self.target_obj

		if self.create_joint:
			base_name = parser.clean_name(base, ['tmp', 'temp'])
			self.bind_jnt = bb.create_node('joint', base_name, element+['Bnd'], number, side)
			bb.snap([self.target_obj], self.bind_jnt)
			if self.bind_parent and cmds.objExists(self.bind_parent):
				cmds.parent(self.bind_jnt, self.bind_parent)
			drive_target = self.bind_jnt

		base_name = NAMER.format(base, element, number, None, None)
		controller = Controller(
							objects=[drive_target],
							name = base_name,
							side = side,
							main_ctrl_grp=self.ctrl_parent,
							color = self.color,
							**kwargs
						)
		
		if self.global_scale:
			for ax in 'xyz':
				cmds.connectAttr(f'{self.global_scale}', f'{controller.offset_grps[0][0]}.s{ax}')
		
		if self.delete_temp:
			cmds.delete(self.target_obj)
		
		if self.upper_driver:
			bb.create_constrain([self.upper_driver], controller.offset_grps[0][0])

		self.single_ctrl = controller.ctrls[0]
		self.offset_grps = controller.offset_grps




