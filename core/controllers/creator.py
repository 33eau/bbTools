#25Oct27
from importlib import reload
import maya.cmds as cmds # type: ignore
import maya.mel as mel
import numpy as np
# from . import shape_library
from . import shape_color 

from ..utils import rig_utils as bb
from ..utils import io_utils as io
from ..data import constants as constants
from ..naming import namer_factory as naming
from ..naming import parser
from ..naming import current_project

reload(bb)
reload(io)
#reload(shape_library)
reload(constants)
reload(naming)
reload(parser)
reload(current_project)


SHAPES_PATH = r'W:\RIG\LIB\bbTools\core\controllers'
SHAPE_FILE = 'shape_library.py'
shapes = io.import_data('shape_library.py', None, SHAPES_PATH)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)
SUFFIX = 'ctrl'

CUSTOM_TEMPLATE = 'hatrig'
CUSTOM_SUFFIX = 'ctl'

CTRL_SHAPES = 'ctrl_shapes.ctrlshapes'
FOLDER_NAME = 'data'


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
					move = None,
					temp = False,
					fk_chain = False ,
					upper_driver=None,
					run = True,
					log = False,
					clean_elem = None,
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
		self.move = move or [0, 0, 0]
		self.temp = temp
		self.fk_chain = fk_chain
		self.upper_driver =  upper_driver
		self.clean_elem =  clean_elem

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
				ctrl_name = name_data['ctrl_name']
				if self.clean_elem:
					ctrl_name = parser.clean_name(ctrl_name, self.clean_elem)

				ctrl = self.create_curve(
								ctrl_name = ctrl_name, 
								shape = self.shape, 
								color=self.color, 
								line_width=self.line_width, 
								scale=self.scale, 
								shape_rotation=self.shape_rotation, 
								rotate_order=self.rotate_order,
								move = self.move
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

			if self.upper_driver:
				self.create_connection(self.offset_grps[0][0], self.upper_driver)
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
					shape_rotation=[0, 0, 0], 
					rotate_order='zyx',
					move = [0, 0, 0],
					close_curve = True):

		points = shapes.get(shape, shapes['crossCircle'])
		crv = cmds.curve(p=points, d=1)
		crv = cmds.rename(crv, ctrl_name)
		shp = cmds.listRelatives(crv, s=True)[0]
		if close_curve:
			cmds.closeCurve(shp, ch=False, ps=1, rpo=True, bb=0.5, bki=0, p=0.1)
			bb.rotate_curve(crv, rotation=shape_rotation)
			cmds.setAttr( f'{shp}.lineWidth', line_width)
		bb.set_color([crv], color)
		bb.scale_shape(crv, scale)
		bb.move_shape(crv, move)
		

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
		for ax in 'xyz':
			cmds.connectAttr(self.scale_uniform, f'{self.super_ctrl}.s{ax}')
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
	def __init__(self, target_obj=None, bind_parent=None, ctrl_parent=None, global_scale = None, upper_driver = None, delete_temp = False, color = None, add_element = None,  **kwargs):
		self.target_obj =  target_obj
		self.bind_parent = bind_parent
		self.ctrl_parent =  ctrl_parent
		self.global_scale =  global_scale
		self.upper_driver =  upper_driver
		self.delete_temp =  delete_temp
		self.color = color
		self.add_element =  add_element

		self.side = kwargs.get('side', None)
		self.create_joint = kwargs.get('create_joint', True)

		if not self.side:
			self.side = parser.find_element(self.target_obj, 'sides')

		if self.color is None:
			formatted_side = parser.format_side(self.side, 'upper')
			color = shape_color.CTRL_COLOR.get(formatted_side, 'yellow')
			self.color = color
		else: 
			self.color =  color 

		# Return result
		self.ctrl = None
		self.offset_grps = None
		self.bind_jnt = None

		if target_obj:
			self.build(**kwargs)

	def build(self, **kwargs):
		name_data = get_naming_data(obj=self.target_obj)
		base, element, number, side, suffix = NAMER.extract(self.target_obj)
		drive_target = self.target_obj
	
		if self.create_joint:
			base_name = parser.clean_name(base, ['tmp', 'temp'])
			if self.add_element:
				element.append(self.add_element)
			self.bind_jnt = bb.create_node('joint', base_name, element, number, side)
			if self.bind_parent and cmds.objExists(self.bind_parent):
				cmds.parent(self.bind_jnt, self.bind_parent)
			bb.snap([self.target_obj], self.bind_jnt)
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
		
		# if self.global_scale:
		# 	for ax in 'xyz':
		# 		cmds.connectAttr(f'{self.global_scale}', f'{controller.offset_grps[0][0]}.s{ax}')
		
		if self.delete_temp:
			cmds.delete(self.target_obj)
		
		if self.upper_driver:
			bb.create_constrain([self.upper_driver], controller.offset_grps[0][0], 'parentScale')

		self.ctrl = controller.ctrls[0]
		self.offset_grps = controller.offset_grps

def mirror_ctrl(source = None, target = None, world_space = False, mirror = True, color = False):

	if source is None and target is None:
		selection = cmds.ls(sl=True)
		if len(selection) > 1:
			source = selection[1]
			targets = selection[:-1]
		elif len(selection) == 1:
			source = cmds.ls(sl=True)[0]
			side = parser.find_element(source, 'sides')
			formatted_side=parser.format_side(side, 'upper')
			if formatted_side is not None:
				opposite_side = 'L' if formatted_side == 'R' else 'R'
				base, element, number, side, suffix = NAMER.extract(source)
				target  = NAMER.format(base, element, number, opposite_side, suffix)
				if not cmds.objExists(target):
					print(f'ERROR: "{source}" does not have the opposite side ctrl to mirror to.')
				else:
					targets = [target]
		else:
			print('Please Select Target(s) and Source')
	else:
		targets = [target]

	cv_count, spans_count, degree_count = bb.get_curve_info(source)
	source_position = cmds.xform(f'{source}.cv[0:{cv_count}]', q=True, t=True, ws = world_space, os = not world_space)
	position_array = np.array(source_position, dtype='float64').reshape(-1,3)

	max_value = cmds.getAttr( f'{source}.maxValue' )
	keep_range = 2 if max_value == spans_count else 0 # curve parameter 0-1

	for target in targets:
		cmds.rebuildCurve(target, d = degree_count,ch=True, s = spans_count, rpo = True, end = 1, kr = keep_range, kcp = 0, kep = 1, kt = 0, tol = 0.01)
		cmds.select(target)
		#mel.eval(f'BakeNonDefHistory;')
		mel.eval(f'performBakeNonDefHistory False;')

		inverse_value = -1 if mirror else 1
		for i, position in enumerate(position_array):
			cmds.xform(f'{target}.cv[{i}]', t=(position[0] * inverse_value, position[1], position[2]), ws = world_space, os= not world_space, a=True)

		if color:
			target_shp = cmds.listRelatives(target, s=True)[0]
			line_width = cmds.getAttr( f'{source}Shape.lineWidth')
			rgb_color = cmds.getAttr( f'{source}Shape.overrideColorRGB')

			cmds.setAttr( f'{target_shp}.overrideEnabled', 1)
			cmds.setAttr(f'{target_shp}.overrideRGBColors',1)
			cmds.setAttr( f'{target_shp}.lineWidth', line_width)
			cmds.setAttr( f'{target_shp}.overrideColorRGB', *rgb_color[0])

def export_ctrl_shapes(ctrl_suffix='_ctl', file_name = None, world_space = False):
	file_name = file_name if file_name else CTRL_SHAPES
	path = io.define_path(FOLDER_NAME)
	data = {}
	ctrl_list = cmds.ls(f'*{ctrl_suffix}')
	cha_name = bb.get_cha_name()
	data['character'] = cha_name
	data['legend'] = ['cv', 'spans', 'degree', 'form', 'line_width', 'color', 'position']
	data['ctrl_list'] = []
	for ctrl in ctrl_list:
		data['ctrl_list'].append(ctrl)
		cv, spans, degree = bb.get_curve_info(ctrl)
		shape = cmds.listRelatives( ctrl, s = True )[0]
		form = cmds.getAttr(f'{ctrl}.form')
		line_width = cmds.getAttr(f'{shape}.lineWidth')
		color = cmds.getAttr(f'{shape}.overrideColorRGB')[0]
		cv_position = []
		for i in range(0, cv ):
			position = cmds.xform( f'{ctrl}.cv[{i}]', q = True, t = True, os = not world_space, ws = world_space )
			cv_position.append(tuple(position))
		#cv_position = np.array(list(cv_position), dtype='float64')
		data[ctrl] = [cv, spans, degree, form, line_width, color, cv_position]
	io.export_data(file_name = file_name, data = data, path = path, indent = 4, mode = 'overwrite', log = True)

def import_ctrl_shapes(search_for=None, replace_with=None, prefix=None, suffix=None, namespace = None, file_name=None, world_space = False):
	path = io.define_path(FOLDER_NAME)
	file_name = file_name if file_name else CTRL_SHAPES
	data = io.import_data(file_name = file_name, path = path)


	ctrl_list = data['ctrl_list']
	imported_len = 0
	for i, ctrl in enumerate(ctrl_list):
		if cmds.objExists(ctrl):
			shape = cmds.listRelatives(ctrl, s=True)[0]
			new_ctrl = cmds.rebuildCurve( shape, ch = False, rpo = True, rt = 0, end = True, kr = True, kcp = False, kep = True, kt = False, s = data[ctrl][1], d = data[ctrl][2], tol = 0.01, o=True)[0]
			cmds.setAttr(f'{new_ctrl}.form', data[ctrl][3])
			cmds.setAttr(f'{shape}.lineWidth', data[ctrl][4])
			cmds.setAttr(f'{shape}.overrideColorRGB', data[ctrl][5][0], data[ctrl][5][1], data[ctrl][5][2])
			for i in range( 0, data[ctrl][0] ):
				cmds.xform( f'{new_ctrl}.cv[{i}]', t = data[ctrl][6][i], os = not world_space, ws = world_space )
			imported_len += 1
		else:
			pass
	print(f'🔻 Imported {imported_len} CtrlShapes from : {path}')	

def new_shape():
	obj = cmds.ls(sl=True)[0]
	shape = {}
	coordinates = []
	cv = bb.get_cv_count( obj )

	for i in range( 0, cv):
		coordinate = cmds.xform( f'{obj}Shape.cv[{i}]', ws = True, t = True, q = True )
		coordinates.append(tuple(coordinate))

	coordinates.append(coordinates[0])
	shape[obj] = coordinates
	io.export_data(file_name = SHAPE_FILE, data = shape, path = SHAPES_PATH, indent = 4, mode = 'append', log = True)	


	
		




