#import maya.cmds as cmds
from importlib import reload
import maya.cmds as cmds
import maya.OpenMaya as om

from ..controllers import shape_color 
from ..data import constants as constants
from ..naming import namer_factory as naming 
from ..naming import parser
from ..naming import templates
from ..naming import current_project

reload(constants)
reload(naming)


NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

CONSTRAINT_TYPES = constants.CONSTRAINT_TYPES
AXIS_MAP = constants.AXIS_MAP
COLORS = shape_color.COLORS

# -----------------------------------------------------------11--------
# Naming helpers, Fundamental helpers
# -------------------------------------------------------------------

def create_node(node_type='', base='', elements=None, number=None, side=None, namer = NAMER, **kwargs):
	if elements is None:
		elements = []

	suffix = templates.TYPE_SUFFIX.get(node_type)
	if suffix is None:
		suffix = node_type
		print(f"Warning: No standard suffix found for node type: {node_type}. Using node_type as suffix'.")

	node_name = NAMER.format(
							base	 = base,
							element = elements,
							number	 = number,
							side	 = side,
							suffix	 = suffix
							)

	if node_type == 'locator':
		named_node = cmds.spaceLocator(n=node_name, **kwargs)[0]
	elif node_type == 'follicle':
		follicle_shp = cmds.createNode('follicle')
		follicle = cmds.listRelatives(follicle_shp, p=True)[0]
		named_node = cmds.rename(follicle, node_name)
	elif node_type == 'group':
		named_node = cmds.group(empty=True, n=node_name, **kwargs)
	elif node_type == 'joint':
		cmds.select(cl=True)
		named_node = cmds.joint(n=node_name, **kwargs)
	else:
		named_node = cmds.createNode(node_type, n=node_name, **kwargs)
	#print(f'created {node_name}')
	return named_node

# def get_side(object, krt=False):
# 	name = str(object)
# 	for side_key, (tokens, short_name) in SIDE_MAP.items():
# 		for token in tokens:
# 			if token in name:
# 				return tokens[1] if krt else tokens[0]
# 	return "m" if krt else ""

# def get_name(object):
# 	full_name = object.split("_")[0]
# 	side = get_side(full_name)
# 	if side:
# 		base_name = full_name.replace(side, "")
# 	else:
# 		base_name = full_name
# 	return base_name

def normalize_axis(axis):
	if isinstance(axis, tuple):
		for ax, val in AXIS_MAP.items():
			if axis == val[0]:
				result = ax
	if isinstance(axis, str):
		if axis not in AXIS_MAP:
			raise ValueError(f"Invalid axis string: {axis}")
		result = axis
	if isinstance(axis, int):
		for ax, val in AXIS_MAP.items():
			if axis == val[1]:
				result = ax
	return result

def axis_convert(axis = None, return_type = ''):
	"""
	:param axis: input axis
	:param return_type: index, letter, absolute_letter, vector, ik_twist_index, ik_twist_up_index
	"""

	formatted_axis = normalize_axis(axis)
	if return_type == 'letter':
		result = formatted_axis

	elif return_type == 'absolute_letter':
		result = formatted_axis.strip('-')

	elif return_type == 'index':
		result = AXIS_MAP[formatted_axis][1]

	elif return_type == 'vector':
		result = AXIS_MAP[formatted_axis][0]

	elif return_type == 'ik_twist_index':
		result = AXIS_MAP[formatted_axis][2]

	elif return_type == 'ik_twist_up_index':
		result = AXIS_MAP[formatted_axis][3]
		
	return  result

# def get_name_type(object):
# 	return str(object).split("_")[-1]

def get_node_type(obj):
	shapes = cmds.listRelatives(obj, s=True)
	return cmds.objectType(shapes[0] if shapes else obj)

def node_object_type(node):
	try:
		shape = cmds.listRelatives(node, s=True, fullPath=True)[0]
		return cmds.objectType(shape)
	except Exception:
		# fallback: maybe the node itself is shape
		return cmds.objectType(node)

def get_constrain_node(constraint_type='constraint', objects=[]):
	'''
		constraint_type: 'constraint', 'parentConstraint', 'pointConstraint', 'orientConstraint', 'scaleConstraint', 'parent_obj'
	'''
	objects = cmds.ls(sl=True) or []
	if not isinstance(objects, list):
		objects = list(objects)

	if constraint_type == 'parent_obj':
		return cmds.parentConstraint(objects[0], q=True, tl=True) or [] if objects else []
	
	constraint_nodes = []
	for obj in objects:
		for node in cmds.listRelatives(obj, c=True):
			if cmds.ls(node, type=constraint_type):
				constraint_nodes.append(node)
	
	return constraint_nodes

def get_orig_shape(objects=None, delete_unused=True):
	objects = objects or cmds.ls(sl=True) or []
	if not isinstance(objects, list):
		objects = [objects]
	
	orig_shapes = []
	
	for obj in objects:
		for shape in cmds.listRelatives(obj, shapes=True):
			inputs = cmds.listConnections(f"{shape}.inMesh", plugs=True) or []
			outputs = (cmds.listConnections(f"{shape}.outMesh", plugs=True) or []
					+ cmds.listConnections(f"{shape}.worldMesh", plugs=True) or [])
			
			if not inputs and outputs:
				orig_shapes.append(shape)
			elif not inputs and not outputs and delete_unused:
				cmds.setAttr(f"{shape}.intermediateObject", 0)
				cmds.delete(shape)
				print("Delete unused orig shape: {shape}")
	
	return orig_shapes[0] if orig_shapes else None

def freeze(object, t=True, r=True, s=True):
	cmds.makeIdentity( object, a = True, t=t, r=r, s=s , n = False, pn = True)

# -------------------------------------------------------------------
# Curve / shape helpers
# -------------------------------------------------------------------

def get_cv_count(curve):
	if not curve:
		sel = cmds.ls(sl=True) or []
		if not sel:
			raise ValueError("No curve specified and nothing selected.")
		curve = sel[0]

	shape = f"{curve}Shape"
	i_spans = cmds.getAttr(f"{shape}.spans")
	i_degree = cmds.getAttr(f"{shape}.degree")
	return int(i_spans + i_degree - 1)

def get_curve_info(curve):
	i_cv = get_cv_count(curve)
	shape = f"{curve}Shape"
	i_spans = int(cmds.getAttr(f"{shape}.spans"))
	i_degree = int(cmds.getAttr(f"{shape}.degree"))
	return i_cv, i_spans, i_degree

def rebuild_curve_to_match(source, target):
	_, i_span, i_degree = get_curve_info(source)
	try:
		cmds.rebuildCurve(target, d=i_degree, s=i_span, rpo=True, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, tol=0.01)
	except Exception as e:
		LOGGER.warning("rebuild_curve_to_match failed: %s", e)

def create_joint_on_curve(curve='', joint_num=20, fk=True, aim_axis='', up_axis='', world_up_axis='', negative_dir = False, ikSpline=False):
	curve_lenght = cmds.arclen(curve)
	name = get_name(curve)
	side = get_side(curve)
	rad = 1
	result = []

	cmds.select(cl=True)
	for i in range(joint_num +1):
		joint = cmds.joint(n=f'{name}{i+1:02d}{side}_jnt', p = (curve_lenght/joint_num * i, 0, 0), rad = rad)
		result.append(joint)

	ikh = cmds.ikHandle(sol='ikSplineSolver', sj=result[0], ee=result[-1], c=curve, pcv=False, ccv=False)

	cmds.makeIdentity(result, apply=True, t=1, r=1, s=1, n=0, pn=1)
	ALL_AXES = ['x', 'y', 'z']
	used_axis = [aim_axis, up_axis]
	cross_axis = set(ALL_AXES) - set(used_axis)
	aim_str = ''.join([aim_axis, up_axis, list(cross_axis)[0]])
	direction = 'down' if negative_dir else 'up'
	world_up_str = world_up_axis + direction
	cmds.joint(result[0], e=True, oj=aim_str, sao=world_up_str, aos=True, ch=True)
	print('finish AIMING joints')

	if not ikSpline:
		cmds.delete(ikh)
	else:
		fk=True
		cmds.rename(ikh[0], f'{name}IkSpline{side}_ikh')
		cmds.rename(ikh[1], f'{name}IkSpline{side}_eff')
	if not fk:
		cmds.parent(result, w=True)

	return result

def create_curve_from_joints(top_joint='', name='', degree=3):

	base, element, number, side, suffix = NAMER.extract(side = top_joint[0])
	positions=[]
	joint_chain = cmds.listRelatives(top_joint, ad=True, type='joint')
	joint_chain.append(top_joint)
	joint_chain.reverse()

	for jnt in joint_chain:
		position = cmds.xform(jnt, q=True, ws=True, t=True)
		positions.append(position)
	curve_name = NAMER.format(name, element, number, side, 'crv')
	curve = cmds.curve(p=positions, d=degree)
	curve = cmds.rename(curve, curve_name)
	return curve

# -------------------------------------------------------------------
# Groups / constraints / parenting helpers
# -------------------------------------------------------------------

def create_group(name='', children=None, parent_heirarchy='', parent_constrain='',  constrain_type =''):

	try:
		group = cmds.group(n=f'{name}_grp', empty=True)
	except Exception as e:
		cmds.error(f'Failed to create group "{name}_grp": {e}')

	if children:
		cmds.parent(children, group)

	if parent_heirarchy:
		try:
			cmds.parent(group, parent_heirarchy)
		except Exception as e:
			cmds.warning(f'Failed to parent {group} under {parent_heirarchy}: {e}')

	if parent_constrain:
		try:
			constrain_type = constrain_type or 'psc'
			create_constrain(constrain_type, parent_constrain, group)
		except Exception as e:
			cmds.warning(f'Fail to create Constrain from {parent_constrain} to {group}: {e}')

	return group
	
def _normalize_constraint_type(type):
	if not type:
		return ""
	for name, keyword in CONSTRAINT_TYPES.items():
		if type in keyword:
			return name
	return type	

def create_constrain( parents=[], target=None, type="pac", maintain_offset=True, snap=False):
	type = _normalize_constraint_type(type)
	parents = parents if parents else(cmds.ls(sl=True)[:-1] or [])
	target = target or (cmds.ls(sl=True) or [])[-1]
	if not parents or not target:
		raise ValueError("create_constrain requires parents and target.")
	
	node_suffix = CONSTRAINT_TYPES.get(type, [""])[0]

	base, element, number, side, suffix = NAMER.extract(target)
	constrain_node_name = NAMER.format(base, element , number, side, node_suffix)
	objects = parents + [target]

	change_interp_type = False
	if len(parents) > 1:
		change_interp_type = True
		if type == 'point':
			change_interp_type = False

	if snap:
		temp_constraint = getattr(cmds, f"{type}Constraint")(parents, target, mo = False)
		cmds.delete(temp_constraint)
	
	if type == "parentScale":
		pac_name = NAMER.format(base, element , number, side, 'pac')
		scc_name = NAMER.format(base, element , number, side, 'scc')
		pac_node = cmds.parentConstraint(objects, mo = maintain_offset, n = pac_name)
		scc_node = cmds.scaleConstraint(objects, mo = maintain_offset, n = scc_name)
		if change_interp_type:
			cmds.setAttr( f'{pac_node[0]}.interpType', 2)
			cmds.setAttr( f'{scc_node[0]}.interpType', 2)
		return [pac_node, scc_node]
	
	if type in ["point", "parent", "orient", "scale"]:
		constrain_node = getattr(cmds, f"{type}Constraint")(parents, target, mo = maintain_offset, n = constrain_node_name)
		if change_interp_type:
			cmds.setAttr( f'{constrain_node[0]}.interpType', 2)
		return [constrain_node]

	raise ValueError(f"Invalid constraint type: {type}")

# -------------------------------------------------------------------
# General tools
# -------------------------------------------------------------------

def sel():
	sel = cmds.ls(sl=True)
	return sel

def snap(parents=[], target=None):
	if not target:
		target = cmds.ls(sl=True)[-1]
		parents = cmds.ls(sl=True)[:-1]
	cmds.matchTransform(target, parents)

def get_center_position(components):
	x, y, z = [], [], []
	for c in components:
		position = cmds.xform( c, q = True, ws = True, t = True )
		x.append(position[0])
		y.append(position[1])
		z.append(position[2])
	min_x, min_y, min_z = min(x), min(y), min(z)
	max_x, max_y, max_z = max(x), max(y), max(z)
	center_position = [((max_x-min_x)*0.5)+min_x, ((max_y-min_y)*0.5)+min_y, ((max_z-min_z)*0.5)+min_z]
	return center_position

def snap_to_component(create_joint=False ):
	selection = cmds.ls(sl=True)
	# List of selection mask flags for different component types
	# 31: Edge, 32: Vertex, 34: Face
	COMPONENT_MASKS = [31, 32, 34]
	components = cmds.filterExpand(sm=COMPONENT_MASKS, expand=True)
	items = components if components else selection
	items = cmds.ls(sl=True, fl=True)
	center_position = get_center_position(items)
	if create_joint:
		result = cmds.joint(n='centerPosition_jnt')
	else:
		result = cmds.spaceLocator(n='centerPosition_loc')[0]
	cmds.xform(result, t=center_position, a=True, ws=True)
	return result

def create_offset_group(objects=None, offset_names=["Zro"]): 
	objects = objects or cmds.ls(sl=True) or []
	if not isinstance(objects, list):
		objects = [objects]
	
	result = {}
	for obj in objects:
		obj_hierarchy = cmds.listRelatives(obj, ap=True, f=True)
		obj_child = cmds.listRelatives(obj, c=True)
		try:
			obj_shape = cmds.listRelatives(obj, s=True)[0]
			obj_child.remove(obj_shape)
		except:
			pass

		base, element, number, side, suffix = NAMER.extract(obj)
		if element:
			element = element.lower()
			for token in templates.STRIP_TOKENS:
				if token in element:
					element.remove(token)
		element = element if element else []
		offset_groups = []
		for i, offset_name in enumerate(offset_names):
			new_group = create_node(node_type='group', base=base, elements=element + [ offset_name], number=number, side=side)
			snap([obj],new_group)
			if i > 0 :
				cmds.parent(new_group, offset_groups[-1])
			offset_groups.append(new_group)

		if obj_hierarchy:
			cmds.parent(offset_groups[0], obj_hierarchy)

		cmds.parent(obj, offset_groups[-1])

		result[obj] = offset_groups
	
	return result

def set_color(objects=[], color='red', viewport=True, outliner=False, *args):
	objects = objects or cmds.ls(sl=True) or []
	rgb = COLORS[color]
	for obj in objects:
		if viewport:
			try:
				shape = cmds.listRelatives(obj, s=True)[0]
				cmds.setAttr(f'{shape}.ove',1)
				cmds.setAttr(f'{shape}.overrideRGBColors',1)
				cmds.setAttr(f'{shape}.overrideColorRGB', *rgb)

			except:
				cmds.setAttr(f'{obj}.ove',1)
				cmds.setAttr(f'{obj}.overrideRGBColors',1)
				cmds.setAttr(f'{obj}.overrideColorRGB', *rgb)
		if outliner:
			cmds.setAttr(f'{obj}.useOutlinerColor', 1)
			cmds.setAttr(f'{obj}.outlinerColor', *rgb)

def reset_color(objects=[], viewport=True, outliner=True, reset_all=False, *args):
	if reset_all:
		objects = cmds.ls(type='transform')
	else:
		objects = cmds.ls(sl=True)

	for obj in objects:
		if viewport:
			if cmds.attributeQuery('overrideEnabled', node=obj, exists=True):
				cmds.setAttr(f'{obj}.overrideEnabled', 0)
		if outliner:
			if cmds.attributeQuery('useOutlinerColor', node=obj, exists=True):
				cmds.setAttr(f'{obj}.useOutlinerColor', 0)

def duplicate_joint_chain(top_joint='', add_elements=[], remove_element='', radius = 1.0, color = None):
	top_joint = top_joint or cmds.ls(sl=True)[0]
	selected_chain = cmds.listRelatives(top_joint, ad=True)
	selected_chain.append(top_joint)
	selected_chain.reverse()
	
	pair_dict = {}
	parent_dict = {}
	joints_dict = {}
	for elem in add_elements:
		joints_dict[elem] = []
		for i, jnt in enumerate(selected_chain):
			base, element, number, side, suffix = NAMER.extract(jnt)
			joint_name = NAMER.format(base, [elem], number, side, suffix)
			if remove_element in joint_name:
				joint_name = parser.clean_name(joint_name, remove_element)
			cmds.select(cl=True)
			new_joint = cmds.joint(n=joint_name, rad = radius)
			cmds.delete(cmds.parentConstraint(jnt, new_joint, mo=False))
			freeze(new_joint)
			
			pair_dict[jnt] = new_joint
			parent = cmds.listRelatives(jnt, p=True)
			#parent = parent[0] if parent else ''
			if parent:
				parent = parent[0]
				parent_dict[jnt] = parent
				if parent in pair_dict.keys():
					cmds.parent(new_joint, pair_dict[parent])
				else:
					try:
						cmds.parent(new_joint, w=True)
					except:
						pass
			else:
				parent_dict[jnt] = ''

			joints_dict[elem].append(new_joint)

			if color:
				set_color([new_joint], color)

	return joints_dict
		
def scale_shape(object, scale=1.0):
	shape = cmds.listRelatives(object, s=True, f=True)[0]
	node_type = cmds.nodeType(shape)
	try:
		if node_type == 'mesh':
			vtx_count = cmds.polyEvaluate(shape, v=True)
			cmds.scale(scale, scale, scale, f'{shape}.vtx[0:{vtx_count-1}]')
		
		elif node_type in ['nurbsCurve', 'nurbsSurface']:
			spans = cmds.getAttr(f'{shape}.spans')
			cmds.scale(scale, scale, scale, f'{shape}.cv[0:{spans}]')
		
		else:
			cmds.warning(f'Unsupported node type "{node_type}" on {shape}. Skipping.')
	except Exception as e:
		cmds.warning(f'Failed to scale {object}: {e}')
	
	cmds.select(cl=True)

def rotate_curve(curve, rotation=[]):
	cv_count = get_cv_count(curve)
	cmds.rotate( *rotation, f'{curve}.cv[0:{cv_count}]', r = True, objectCenterPivot = True, objectSpace = True, forceOrderXYZ = True)

def matrix_constrain(parent='', target='', type='point'): #25Oct26
	name = get_name(target)
	side = get_side(target)
	if type in ['point', 'parent']:
		pass
	else:
		cmds.error(f'Matrix constrain type: "{type}". Must be either "point" or "parent"')
		return

	# offset value
	offset_mmt = cmds.createNode('multMatrix', n=f'{name}OffsetMtxCnn{side}_mmt')
	cmds.connectAttr(f'{target}.worldMatrix', f'{offset_mmt}.matrixIn[0]')
	cmds.connectAttr(f'{parent}.worldInverseMatrix', f'{offset_mmt}.matrixIn[1]')
	offset_mtx = cmds.getAttr(f'{offset_mmt}.matrixSum')

	# mtx connect
	mtx_connect_mmt = cmds.createNode('multMatrix', n=f'{name}MtxCnn{side}_mmt')
	if type == 'point':
		cmds.connectAttr(f'{parent}.worldMatrix', f'{mtx_connect_mmt}.matrixIn[0]')
		cmds.setAttr(f'{mtx_connect_mmt}.matrixIn[1]', offset_mtx, type='matrix')
	elif type == 'parent':
		cmds.setAttr(f'{mtx_connect_mmt}.matrixIn[0]', offset_mtx, type='matrix')
		cmds.connectAttr(f'{parent}.worldMatrix', f'{mtx_connect_mmt}.matrixIn[1]')
	cmds.connectAttr(f'{target}.parentInverseMatrix', f'{mtx_connect_mmt}.matrixIn[2]')

	# decompose mtx
	mtx_connect_dcm = cmds.createNode('decomposeMatrix', n=f'{name}MtxCnn{side}_dcm')
	cmds.connectAttr(f'{mtx_connect_mmt}.matrixSum', f'{mtx_connect_dcm}.inputMatrix')

	# RESULT
	cmds.connectAttr(f'{mtx_connect_dcm}.outputTranslate', f'{target}.t')
	cmds.connectAttr(f'{mtx_connect_dcm}.outputRotate', f'{target}.r')
	cmds.connectAttr(f'{mtx_connect_dcm}.outputScale', f'{target}.s')

	# Clean up
	cmds.delete(offset_mmt)

def direct_connect(parents=None, targets =None):
	parents = parents or cmds.ls(sl=True)[-1] or []
	targets = targets or cmds.ls(sl=True)[:-1] or []
	try:
		if len(parents) != len(targets):
			for target in targets:
				cmds.connectAttr(f'{parents}.t', f'{target}.t')
				cmds.connectAttr(f'{parents}.r', f'{target}.r')
				cmds.connectAttr(f'{parents}.s', f'{target}.s')
		else:
			for parent, target in zip(parents, targets):
				cmds.connectAttr(f'{parent}.t', f'{target}.t')
				cmds.connectAttr(f'{parent}.r', f'{target}.r')
				cmds.connectAttr(f'{parent}.s', f'{target}.s')
	except Exception as e:
		print(f'Failed to connect: {e}')

def obj_rename(): #23Jun21
	try:
		obj = cmds.ls(sl=True)[0]
		result = cmds.promptDialog(
				title='Rename Object',
				message = 'Enter the new name:',
				text= obj ,
				button=['OK', 'Cancel'],
				defaultButton='OK',
				cancelButton='Cancel',
				dismissString='Cancel'
				)
		
		if result == 'OK':
			newName = cmds.promptDialog(query=True, text=True)
			cmds.rename( obj, newName )
			print ('done done <3')
	except:
		pass

def reset_value(all=True, attrs = []): #25Nov18
	objects = cmds.ls(sl=True)
	zero_default_attrs = [  'translateX', 'translateY', 'translateZ',
							'rotateX', 'rotateY', 'rotateZ',]
	one_default_attrs = [ 'scaleX', 'scaleY', 'scaleZ', 'visibility' ]

	for obj in objects:
		if all:
			for attr in zero_default_attrs:
				try:
					cmds.setAttr(f'{obj}.{attr}', 0)
				except:
					print(f'{obj}.{attr}: cannot be reset. Skipped')
			for attr in one_default_attrs:
				try:
					cmds.setAttr(f'{obj}.{attr}', 1)
				except:
					print(f'{obj}.{attr}: cannot be reset. Skipped')
		else:
			for attr in attrs:
				try:
					cmds.setAttr( f'{obj}.{attr}', 0 )
				except:
					print(f'{obj}.{attr}: cannot be reset. Skipped')

def space_switch(parentA = 'top_ctrl', parentB = 'base_ctrl', attr = 'followPosition', target_grp = '', follow_type = 'point', ctrl = 'mid_ctrl'):

	if not target_grp:
		target_grp = create_offset_group([ctrl], offset_names=['Space'])
		target_grp = target_grp[ctrl][0]

	base, element, number, side, suffix = NAMER.extract(target_grp)
	element = element if element else []

	world_grp = create_node('group', base, element + [follow_type, 'wor'], number, side, suffix)
	local_grp = create_node('group', base, element + [follow_type, 'loc'], number, side, suffix)
	cmds.matchTransform(world_grp, target_grp)
	cmds.matchTransform(local_grp, target_grp)
	create_constrain([parentA], local_grp)
	create_constrain([parentB], world_grp)

	cons = create_constrain( parents=[local_grp, world_grp], target=target_grp, type=follow_type, maintain_offset=True)[0][0]

	if not cmds.attributeQuery(attr, node=ctrl, exists=True):
		cmds.addAttr( ctrl, ln = attr, at = 'float', min = 0, max = 1, dv = 0, k = True )

	switch_rev = create_node('reverse', base, ['space'], None, side)
	cmds.connectAttr(f'{ctrl}.{attr}', f'{switch_rev}.ix')
	cmds.connectAttr(f'{switch_rev}.ox', f'{cons}.{local_grp}W0')
	cmds.connectAttr(f'{ctrl}.{attr}', f'{cons}.{world_grp}W1')

	return local_grp, world_grp

def fkIk_switch(
	parents_fk = ['l_shoulder_fk_jnt', 'l_elbow_fk_jnt', 'l_wrist_fk_jnt', 'l_wrist_tip_fk_jnt'],
	parents_ik = ['l_shoulder_ik_jnt', 'l_elbow_ik_jnt', 'l_wrist_ik_jnt', 'l_wrist_tip_ik_jnt'],
	targets = ['l_shoulder_bnd_jnt', 'l_elbow_bnd_jnt', 'l_wrist_bnd_jnt', 'l_wrist_tip_bnd_jnt'],
	attr_name = 'fkIk',
	features = ['translation', 'rotation', 'scale'],
	ctrl = 'l_arm_setting_ctl',
	ik_ctrl_grp = 'l_arm_ik_ctrl_grp',
	fk_ctrl_grp = 'l_arm_fk_ctrl_grp',
	setup_name = 'arm',
	default_value = 1
	):

	attr_exist = cmds.attributeQuery(attr_name, ln=True, node=ctrl, exists=True)
	if not attr_exist:
		cmds.addAttr( ctrl, ln = attr_name, at = 'float', min = 0, max = 1, dv = default_value, k = True )

	for feat in features:
		for i, target in enumerate(targets):
			base, element, number, side, suffix = NAMER.extract(target) 
			element = [attr_name, feat]
			bcl_name = NAMER.format(base, element, number, side, 'bcl')

			if not cmds.objExists(bcl_name):
				switch = cmds.createNode('blendColors', n = bcl_name )
				cmds.connectAttr(f'{ctrl}.{attr_name}', f'{switch}.blender')
			else:
				switch = bcl_name	
			cmds.connectAttr(f'{parents_ik[i]}.{feat[0]}', f'{switch}.c1')
			cmds.connectAttr(f'{parents_fk[i]}.{feat[0]}', f'{switch}.c2')
			cmds.connectAttr(f'{switch}.op', f'{target}.{feat[0]}')

	side = parser.find_element(ctrl, 'sides')
	rev_name = NAMER.format(setup_name, [attr_name], '', side, 'rev')
	cmds.connectAttr(f'{ctrl}.{attr_name}', f'{ik_ctrl_grp}.v')
	rev = cmds.createNode('reverse', n = rev_name)
	cmds.connectAttr(f'{ctrl}.{attr_name}', f'{rev}.ix')
	cmds.connectAttr(f'{rev}.ox', f'{fk_ctrl_grp}.v')

def create_guide_curve(ctrl = '', target = '', parent = ''): #25Dec01
	if not sParent:
		sParent = ctrl
	base, element, number, side, suffix = NAMER.extract(target)
	curve_name = NAMER.format(base, element , number, side, 'crv')
	element.append('guide')

	guide_crv = cmds.curve( d = 1 , p = [ ( 0 , 0 , 0 ) , ( 0 , 0 , 0 ) ], n = curve_name ) 
	attrs = ['tx', 'ty', 'tz','rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']
	for attr in attrs:
		cmds.setAttr( f'{guide_crv}.{attr}', k = False )
		cmds.setAttr( f'{guide_crv}.{attr}', l = True )

	base, element, number, side, suffix = NAMER.extract(ctrl) 
	ctrl_clt_name = NAMER.format(base, element , number, side, '_clt')
	target_clt_name = NAMER.format(base, element , number, side, '_clt')
	clt_a = cmds.cluster( '{0}.cv[0]'.format( guide_crv ) , wn = ( ctrl , ctrl ), n = ctrl_clt_name )[ 0 ] 
	clt_b = cmds.cluster( '{0}.cv[1]'.format( guide_crv ) , wn = ( target , target ), n = target_clt_name )[ 0 ] 
	cmds.select( cl = True )

	cmds.setAttr( '{0}.ove'.format( guide_crv ), 1)
	cmds.setAttr( '{0}.overrideRGBColors'.format( guide_crv ), 1)
	cmds.setAttr( '{0}.overrideColorRGB'.format( guide_crv ), 0.14,0.14,0.14)
	cmds.setAttr( '{0}.overrideDisplayType'.format( guide_crv ), 1 )
	cmds.setAttr( '{0}.inheritsTransform'.format( guide_crv ), 0 )
	cmds.parent( guide_crv, sParent )
	cmds.select( cl = True )

	return guide_crv

def set_driven_key(main_ctrl='', attr = '', driven = '', values = {0:0,	180:-50,-180:50}):
	driver = f'{main_ctrl}.{attr}'
	len_keys = len(values.keys())
	i = 0
	for driver_value, driven_value in values.items():
		if i == 0:
			tangent_in = 'clamped'
			tangent_out = 'linear'
		elif i == len_keys-1:
			tangent_in = 'linear'
			tangent_out = 'clamped'
		else: 
			tangent_in = 'linear'
			tangent_out = 'linear'
		cmds.setDrivenKeyframe(f'{driven}', cd=f'{driver}', itt = tangent_in, ott = tangent_out, dv=driver_value, v=driven_value )
		cmds.setAttr( f'{driver}', 0)
		key = cmds.listConnections(f'{driven}', type='animCurve')[0]
		cmds.setAttr( f'{key}.preInfinity', 1)
		cmds.setAttr( f'{key}.postInfinity', 1)
		# print( f'key {i} :::: {tangent_in} , {tangent_out}')
		# print( f'{driver} ——— {driver_value}')
		# print( f'{driven} ——— {driven_value}')
		# print('===========================================================')
		# print('===========================================================')
		i+=1

def pole_vector_position(joints, offset = 5, create_locator=True):
	base_position = cmds.xform( joints[0], q = True, t = True, ws = True ) 
	mid_position = cmds.xform( joints[1], q = True, t = True, ws = True ) 
	end_position = cmds.xform( joints[2], q = True, t = True, ws = True )

	base_vector = om.MVector( base_position[0], base_position[1], base_position[2] )
	mid_vector = om.MVector( mid_position[0], mid_position[1], mid_position[2] )
	end_vector = om.MVector( end_position[0], end_position[1], end_position[2] )

	vector_line = ( end_vector - base_vector )
	vector_point = ( mid_vector - base_vector )

	scalar_vector = ( vector_line * vector_point ) / ( vector_line * vector_line )
	project_vector = ( vector_line * scalar_vector ) + base_vector

	base_mid_len = ( mid_vector - base_vector).length()
	mid_end_len = ( end_vector - mid_vector).length()
	total_len = base_mid_len + mid_end_len

	pv_posi_vector = ( mid_vector - project_vector ).normal() * total_len * offset + mid_vector

	if create_locator:
		locator = cmds.spaceLocator()[0]
		cmds.move( pv_posi_vector[0], pv_posi_vector[1], pv_posi_vector[2], locator, r = True  )
		return locator
	return [pv_posi_vector[0], pv_posi_vector[1], pv_posi_vector[2]]

def attr_separator(ctrl, ln='extra', enum_name = '—————'):
	cmds.addAttr( ctrl, ln = ln, at = 'enum', en = enum_name , k = True )
	cmds.setAttr( f'{ctrl}.{ln}', l=True )

def add_enum_space_switch( parent_spaces = ['r_pelvis_ctl'],
							world_space = 'r_global_gimbal_space_grp',
							attr_name = 'follow',
							spaces_name = ['local', 'world'],
							target = 'r_thigh_fk_offset_grp',
							ctrl = 'r_thigh_fk_ctl',
							type = 'orient',
							default_index = 1
						):#25Dec09

	target_name, target_element, target_number, target_side, suffix = NAMER.extract(target) 
	parents = parent_spaces

	if world_space:
		base, element, number, side, suffix = NAMER.extract(world_space) 
		space_grp = NAMER.format(base, ['space'], number, target_side, 'grp' )
		if not cmds.objExists(space_grp):
			space_grp = create_node('group', base, ['space'], number, target_side )
			cmds.matchTransform(space_grp, world_space)

			target_side = parser.find_element(target, 'sides')
			format_side = parser.format_side(target_side, 'upper')
			if format_side == 'R':
				inv_sx_mtx = [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0,0, 0, 0, 1]
				cmds.setAttr(f'{space_grp}.offsetParentMatrix', inv_sx_mtx, type='matrix')
			cmds.parent(space_grp, world_space)
		world_space = space_grp
		parents.insert(0, world_space)

	parent_con = create_constrain(parents, target, type=type, maintain_offset=True)[0][0]
	cmds.setAttr(f'{parent_con}.interpType', 2)

	enum_names = ':'.join(spaces_name)
	cmds.addAttr(ctrl, ln = attr_name, at='enum', en=enum_names, dv=default_index, k=True )
	
	if len(spaces_name) > 2:
		for i, name in enumerate(spaces_name):
			space_cdt = create_node(node_type='condition', base=target_name, elements=target_element+[name], number=target_number, side=target_side )
			cmds.setAttr( f'{space_cdt}.st', i)
			cmds.setAttr( f'{space_cdt}.ctr', 1)
			cmds.setAttr( f'{space_cdt}.cfr', 0)
			cmds.connectAttr(f'{ctrl}.{attr_name}', f'{space_cdt}.ft')
			cmds.connectAttr(f'{space_cdt}.ocr', f'{parent_con}.{parents[i]}W{i}')
	else:
		cmds.connectAttr(f'{ctrl}.{attr_name}', f'{parent_con}.{parents[1]}W1')
		space_switch_rev = create_node(node_type='reverse', base=target_name, elements=target_element+[attr_name], number=target_number, side=target_side )
		cmds.connectAttr(f'{ctrl}.{attr_name}', f'{space_switch_rev}.ix')
		cmds.connectAttr(f'{space_switch_rev}.ox', f'{parent_con}.{parents[0]}W0')
		
########################################################
# OLD VERSION

def jointLabel(bSepSide = False, bSepType = False, bKrt = False, bCustom = True ): #23May17
	typeDict = {  
				'none':0,  
				'root':1,  
				'hip':2,  
				'knee':3,  
				'foot':4,  
				'ankle':4,
				'ball':4,
				'toe':5,  
				'spine':6,   
				'neck':7,   
				'head':8,   
				'collar':9,   
				'clavicle': 9,

				'shoulder':10,  
				'elbow':11,  
				'hand':12,  
				'finger':13,  
				'thumb':14,  
				'propA':15,  
				'propB':16,  
				'propC':17,  
				'other':18,  
				'Index Finger':19,  
				'index':19,
				'Middle Finger':20, 
				'middle':20, 
				'Ring Finger':21,  
				'ring':21,
				'Pinky Finger':22,  
				'pinky':22,
				'Extra Finger':23,
				'fngr':23,
				'Big Toe':24,  
				'toeBig':24,
				'Index Toe':25,  
				'toeInd':25,
				'Middle Toe':26,
				'toeMid':26,  
				'Ring Toe':27,
				'toeRing' : 27,  
				'Pinky Toe':28,
				'toePinky' :28,  
				'Extra Toe':29, 
				'toeXta':29 
				}  
	sideDict = {  
				'Mid':0,   
				'LFT':1,   
				'RGT':2,  
				'':3  
				}  
	sJnts = cmds.ls( sl = True )
	for sJnt in sJnts:
		bStage = cmds.getAttr( '{0}.drawLabel'.format( sJnt ))
		if bStage:
			iVal = 0
		else:
			iVal = 1
		cmds.setAttr( '{0}.drawLabel'.format( sJnt ), iVal )
		if bCustom:
			cmds.setAttr( '{}.type'.format( sJnt ), 18 )
			cmds.setAttr( '{}.otherType'.format( sJnt ),  sJnt , type = 'string' )
			continue
		if bKrt:
			sJntName = sJnt.split('_')[-1]
			sJntSide = sJnt.split('_')[1]
		else:
			sJntName = getName( sJnt )
			sJntSide = getSide( sJnt )
		if bSepSide:
			iSide = sideDict[sJntSide]
		else:
			iSide = 0
		cmds.setAttr( '{}.side'.format( sJnt ), iSide )

		if bSepType:
			try:
				iTyp = typeDict[sJntName]
			except:
				iTyp = 18
			cmds.setAttr( '{}.type'.format( sJnt ), iTyp )
		else:
			cmds.setAttr( '{}.type'.format( sJnt ), 18 )
			cmds.setAttr( '{}.otherType'.format( sJnt ), '{0}{1}'.format( sJntName, sJntSide ), type = 'string' )

def object_rename(): #23Jun21
	try:
		sel = cmds.ls(sl=True)[0]
		result = cmds.promptDialog(
				title='Rename Object',
				message = 'Enter new name:',
				text= sel ,
				button=['OK', 'Cancel'],
				defaultButton='OK',
				cancelButton='Cancel',
				dismissString='Cancel')
		
		if result == 'OK':
			newName = cmds.promptDialog(query=True, text=True)
			cmds.rename( sel, newName )
			print ('done done <3')
	except:
		pass


