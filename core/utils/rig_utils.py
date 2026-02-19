#import maya.cmds as cmds
from importlib import reload
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om
import numpy as np
import re

from ..controllers import creator as bc 
from ..controllers import shape_color 
from ..data import constants as constants
from ..naming import namer_factory as naming 
from ..naming import parser
from ..naming import templates
from ..naming import current_project

reload(bc)
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
		print(f"Warning: No standard suffix found for node type: '{node_type}'. Using '{node_type}' as suffix'.")

	node_name = NAMER.format(
							base	 = base,
							element  = elements,
							number	 = number,
							side	 = side,
							suffix	 = suffix
							)
	
	clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}

	if node_type == 'locator':
		named_node = cmds.spaceLocator(n=node_name, **clean_kwargs)[0]
	elif node_type == 'follicle':
		follicle_shp = cmds.createNode('follicle')
		follicle = cmds.listRelatives(follicle_shp, p=True)[0]
		named_node = cmds.rename(follicle, node_name)
	elif node_type == 'group':
		named_node = cmds.group(empty=True, n=node_name, **clean_kwargs)
	elif node_type == 'joint':
		cmds.select(cl=True)
		named_node = cmds.joint(n=node_name, **clean_kwargs)
	elif node_type == 'ikRp':
		ikh, eff = cmds.ikHandle(n = node_name, sol='ikRPsolver', **clean_kwargs)
		eff_name = NAMER.format(base, elements, number, side, 'eff')
		eff = cmds.rename(eff, eff_name)
		named_node = [ikh, eff]
	elif node_type == 'ikSc':
		ikh, eff = cmds.ikHandle(n = node_name, sol='ikSCsolver', **clean_kwargs)
		eff_name = NAMER.format(base, elements, number, side, 'eff')
		eff = cmds.rename(eff, eff_name)
		named_node = [ikh, eff]
	elif node_type == 'ikSpline':
		ikh, eff = cmds.ikHandle(n = node_name, sol='ikSplineSolver', **clean_kwargs)
		eff_name = NAMER.format(base, elements, number, side, 'eff')
		eff = cmds.rename(eff, eff_name)
		named_node = [ikh, eff]
	else:
		named_node = cmds.createNode(node_type, n=node_name, **clean_kwargs)
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

def axis_convert(axis = None, return_type = '', up_axis = None):
	"""
	:param axis: input axis
	:param return_type: index, letter, absolute_letter, vector, ik_twist_index, ik_twist_up_index, cross_vector, cross_letter
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

	elif return_type == 'cross_vector':
		axis_np = constants.AXIS_NPelement
		up_axis_np = constants.AXIS_NP[up_axis]
		result = np.cross(axis_np, up_axis_np).tolist()

	elif return_type == 'cross_letter':
		axis_np = constants.AXIS_NP[axis]
		up_axis_np = constants.AXIS_NP[up_axis]
		cross_axis = tuple(np.cross(axis_np, up_axis_np).tolist())
		result = normalize_axis(cross_axis)

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

def get_cha_name(working_folder = 'scenes'):
	file_path = (cmds.file ( q = True, loc = True  )).split('/')
	work_folder_index = file_path.index(working_folder)
	cha_name = file_path[work_folder_index-1]
	return cha_name

# -------------------------------------------------------------------
# Curve / shape helpers
# -------------------------------------------------------------------

def get_cv_count(curve):
	if not curve:
		sel = cmds.ls(sl=True) or []
		if not sel:
			raise ValueError("No curve specified and nothing selected.")
		curve = sel[0]

	shape = cmds.listRelatives(curve, s=True)[0]
	i_spans = cmds.getAttr(f"{shape}.spans")
	i_degree = cmds.getAttr(f"{shape}.degree")
	return int(i_spans + i_degree - 1)

def get_curve_info(curve):
	i_cv = get_cv_count(curve)
	shape = f"{curve}Shape"
	i_spans = int(cmds.getAttr(f"{shape}.spans"))
	i_degree = int(cmds.getAttr(f"{shape}.degree"))
	return i_cv, i_spans, i_degree

def get_nurb_info(nurb = None, num_vtx = False):
	if cmds.objectType(nurb)=='transfrom':
		shape = cmds.listRelatives(nurb, s=True)[0]
	else:
		shape = nurb
	spans_u, spans_v = list(cmds.getAttr(f'{shape}.spansUV')[0])
	degree_u, degree_v = list(cmds.getAttr(f'{shape}.degreeUV')[0])

	num_cv_u = spans_u + degree_u
	num_cv_v = spans_v + degree_v
	
	if num_vtx:
		num_vtx = num_cv_u * num_cv_v
		return num_vtx
		
	return num_cv_u, num_cv_v

def rebuild_curve_to_match(source, target):
	_, i_span, i_degree = get_curve_info(source)
	try:
		cmds.rebuildCurve(target, d=i_degree, s=i_span, rpo=True, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, tol=0.01)
	except Exception as e:
		LOGGER.warning("rebuild_curve_to_match failed: %s", e)

def create_joint_on_curve(curve='', joint_num=20, fk=True, aim_axis='', up_axis='', world_up_axis='', negative_dir = False, ikSpline=False):
	curve_lenght = cmds.arclen(curve)
	rad = 1
	result = []
	base, element, number, side, suffix = NAMER.extract(curve)

	for i in range(joint_num):
		posi = cmds.xform( f'{curve}.cv[{i}]', ws=True, t=True, q=True )
		joint = create_node('joint', base, element, f'{i+1:02d}', side, p =posi, rad = rad)
		if fk:
			if len(result) > 0:
				cmds.parent(joint, result[-1])
		result.append(joint)
	return
	#ikh = cmds.ikHandle(sol='ikSplineSolver', sj=result[0], ee=result[-1], c=curve, pcv=False, ccv=False)
	ikh = create_node('ikSpline', base, element, number, side, sj=result[0], ee=result[-1], c=curve, pcv=False, ccv=False)

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
		# cmds.rename(ikh[0], f'{name}IkSpline{side}_ikh')
		# cmds.rename(ikh[1], f'{name}IkSpline{side}_eff')
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

def create_constrain( parents=[], target=None, type="pac", maintain_offset=True):
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
# BSH tools
# -------------------------------------------------------------------

def inverse_blendshape_weight(bsh_node = None, target_index = 'weight[1]', geo_index = 0, just_log=False):
	target = cmds.listAttr(f'{bsh_node}.{target_index}', m=True)[0]
	if just_log:
		print(f'{bsh_node} : {target}')
		return
	base_object = cmds.blendShape(bsh_node, query=True, geometry=True)[0]
	
	geo_type = cmds.objectType(base_object)
	
	if geo_type == 'nurbsSurface':
		num_vtx = get_nurb_info(base_object, num_vtx=True)
	elif geo_type == 'mesh':
		num_vtx = cmds.polyEvaluate(base_object, vertex=True)
	else:
		print('Dunno the type of selected obj. Function accepts only a NURBS or a MESH')
		return False
	target_int = re.findall(r'\d+', target_index)[0]
	for i in range(0, num_vtx):
		attr_path = f'{bsh_node}.inputTarget[{geo_index}].inputTargetGroup[{target_int}].targetWeights[{i}]'
		current_value = cmds.getAttr(attr_path)
		new_value = 1 - current_value
		cmds.setAttr(attr_path, new_value)
		
	mel.eval("ArtPaintBlendShapeWeightsToolOptions;")
	print(f"Done: Inverted '{target}' weights on {bsh_node}")
			

def inverse_after_duplicate(bsh_node = 'blendshape__face_local'):
	targets = cmds.aliasAttr(f'{bsh_node}.w[]', q=True)
	for target in targets:
		if target.endswith('_Copy'):
			copied_index = targets.index(target) + 1
		
	new_target_index = targets[copied_index]
	copied_name = cmds.listAttr(f'{bsh_node}.{new_target_index}', m=True)[0]
	source_name = copied_name.replace('_Copy', '')
	base, element, number, side, direction = NAMER.extract(source_name)
	opp_side = 'l' if side == 'r' else 'r'
	target_name =  NAMER.format(base, element, number, opp_side, direction)

	targets = cmds.aliasAttr(f'{bsh_node}.w[]', q=True)
	if target_name in targets:
		print('meep')
		old_target_index = targets.index(target_name)
		old_target_index = targets[old_target_index+1]
		plugged_inputs = cmds.listConnections(f'{bsh_node}.{old_target_index}', d=False, s=True)
		for input_node in plugged_inputs:
			cmds.disconnectAttr(f'{input_node}.o', f'{bsh_node}.{old_target_index}')
			cmds.connectAttr(f'{input_node}.o', f'{bsh_node}.{new_target_index}')
		cmds.aliasAttr('old_' + target_name, f'{bsh_node}.{old_target_index}')
		cmds.removeMultiInstance(f'{bsh_node}.{old_target_index}', b=True)
		
	cmds.aliasAttr(target_name, f'{bsh_node}.{new_target_index}')
	inverse_blendshape_weight(bsh_node = bsh_node, target_index = new_target_index, geo_index = 0, just_log=False)




# -------------------------------------------------------------------
# General tools
# -------------------------------------------------------------------

def sel():
	sel = cmds.ls(sl=True)
	return sel

def snap(parents=[], target=None, type = 'parent'):
	if not target:
		target = cmds.ls(sl=True)[-1]
		parents = cmds.ls(sl=True)[:-1]
	node = create_constrain(parents, target, type=type, maintain_offset = False)[0]
	cmds.delete(node)

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
		result = cmds.joint(rad = 0.4)
		result = cmds.rename(result, 'center_jnt')
	else:
		result = cmds.spaceLocator()[0]
		result = cmds.rename(result, 'center_loc')
	cmds.xform(result, t=center_position, a=True, ws=True)
	cmds.parent(result, world=True)
	return result

def create_offset_group(objects=None, offset_names=['Zro'], remove_elem = ['tmp'], add_type=False): 
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
			for i, elem in enumerate(element):
				elem = elem.lower()
				for token in templates.STRIP_TOKENS:
					if token in elem:
						elem = elem.remove(token)
						element[i] = elem
		element = element if element else []
		offset_groups = []
		if add_type:
			offset_names.insert(0, suffix)
		for i, offset_name in enumerate(offset_names):
			group_name = NAMER.format(base, element + [offset_name], number, side, 'grp')
			group_name = parser.clean_name(group_name, remove_elem)
			new_group = cmds.group(empty=True, n = group_name)
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

def duplicate_joint_chain(joints = None, remove_element = None, add_elements = None, ignore_jnts = None):
	'''
	Duplicate joint chain
	
	:param joints: List of joint names to duplicate.
	:param remove_element: list of strings to remove from the original name.
	:param add_elements: list of strings to add to the new joint names.
	:param ignore_jnts: List of joints to skip.
	:return: A dictionary with the elements as its keys. 
			Example: {'fk': ['joint_01_fk_jnt', 'joint_02_fk_jnt']}
	'''
	joint = joints or []
	remove_element = remove_element or 'tmp'
	add_elements = add_elements or ['_']
	ignore_jnts = ignore_jnts or []
	
	joint_dict= {}

	input_jnts = [jnt for jnt in joints if jnt not in ignore_jnts]

	parent_dict = {}
	for jnt in input_jnts:
		parent = cmds.listRelatives(jnt, p = True)
		if parent:
			if parent[0] in joints:
				parent_dict[jnt] = parent[0]	
	
	for elem in add_elements:
		joint_dict[elem] = []
		pair_dict = {}
		for jnt in input_jnts:
			if remove_element:
				orig_jnt = parser.clean_name(jnt, remove_element)
									
			base, element, number, side, _ = NAMER.extract(orig_jnt)
			element.append(elem)
			new_jnt = create_node('joint', base, element, number, side)
			
			cmds.delete(cmds.parentConstraint(jnt, new_jnt, mo=False))
			cmds.makeIdentity( new_jnt, a = True, t=True, r=True, s=True , n = False, pn = True)
			for ax in 'XYZ':
				attr = f'preferredAngle{ax}'
				val = cmds.getAttr(f'{jnt}.{attr}')
				cmds.setAttr(f'{new_jnt}.{attr}', val)
				
			pair_dict[jnt] = new_jnt

			if jnt in parent_dict.keys():
				old_parent = parent_dict[jnt]
				new_parent = pair_dict[old_parent]
				cmds.parent(new_jnt, new_parent)
		
			joint_dict[elem].append(new_jnt)
			
			
	return joint_dict

def scale_shape(object, scale=1.0):
	shape = cmds.listRelatives(object, s=True, f=True)[0]
	node_type = cmds.nodeType(shape)
	try:
		scale_value = scale if isinstance(scale, list) else [scale, scale, scale]

		if node_type == 'mesh':
			vtx_count = cmds.polyEvaluate(shape, v=True)
			cmds.scale(scale_value[0], scale_value[1], scale_value[2], f'{shape}.vtx[0:{vtx_count-1}]', r=True)
		
		elif node_type in ['nurbsCurve', 'nurbsSurface']:
			spans = cmds.getAttr(f'{shape}.spans')
			cmds.scale(scale_value[0], scale_value[1], scale_value[2], f'{shape}.cv[0:{spans}]', r=True)
		
		else:
			cmds.warning(f'Unsupported node type "{node_type}" on {shape}. Skipping.')
	except Exception as e:
		cmds.warning(f'Failed to scale {object}: {e}')
	cmds.select(cl=True)

def move_shape(object, value=[]):
	shape = cmds.listRelatives(object, s=True, f=True)[0]
	node_type = cmds.nodeType(shape)
	try:
		if node_type == 'mesh':
			vtx_count = cmds.polyEvaluate(shape, v=True)
			#cmds.move(value[0], value[1], value[2], f'{shape}.vtx[0:{vtx_count-1}]', r=True, cs=False)
			cmds.xform(f'{shape}.vtx[0:{vtx_count-1}]', ws=True, t=value, r=True)
	
		
		elif node_type in ['nurbsCurve', 'nurbsSurface']:
			spans = cmds.getAttr(f'{shape}.spans')
			#cmds.move(value[0], value[1], value[2], f'{shape}.cv[0:{spans}]', r=True, cs=False)
			#cmds.xform(f'{shape}.cv[0:{spans}]', ws=True, t=value, r=True)
			cmds.move(*value, f'{shape}.cv[0:{spans}]', r=True, wd=True )
	
		
		else:
			cmds.warning(f'Unsupported node type "{node_type}" on {shape}. Skipping.')
	except Exception as e:
		cmds.warning(f'Failed to move {object}: {e}')
	
	cmds.select(cl=True)

def rotate_curve(curve, rotation=[]):
	cv_count = get_cv_count(curve)
	#cmds.rotate( rotation[0], rotation[1], rotation[2], f'{curve}.cv[0:{cv_count}]', cs= False, forceOrderXYZ = True)
	cmds.xform(f'{curve}.cv[0:{cv_count}]', ro=rotation, os=True, r=True)
	
# ——————————————————————————————————————————————————————————————————————
# Matrix
# ——————————————————————————————————————————————————————————————————————
def matrix_constrain(parent, target, type='parent', store_orig = False, channels = ['translate', 'rotate', 'scale']):
	elem_name = ['mtxCons']
	if not parent and not target:
		sel =  cmds.ls(sl=True)
		if len(sel) != 2:
			cmds.warning('Please select PARENT object and TARGET object.')
			return
		parent = sel[0]
		target = sel[-1]

	base, element, number, side, suffix = NAMER.extract(target)
	target_parent = cmds.listRelatives(target, p=True)[0]

	# Use openMaya matrix to check if two objects are in the exactly same position
	parent_mtx = om.MMatrix(cmds.getAttr(f'{parent}.worldMatrix[0]'))
	target_mtx = om.MMatrix(cmds.getAttr(f'{target}.worldMatrix[0]'))

	# List of nodes that will be connected to multMatrix respectively. different Type -> different Order
	matrix_stack = []
	mtx_cons_mmt = create_node('multMatrix', base, element + elem_name , number, side)

	# Check for equality with a small tolerance
	offset = not (target_mtx.isEquivalent(parent_mtx, 1e-10))
	if offset:
		offset_matrix = target_mtx * parent_mtx.inverse()
		matrix_stack.append(list(offset_matrix))

	if type == 'point':
		matrix_stack.insert(0, f'{parent}.worldMatrix[0]')
	elif type == 'parent':
		matrix_stack.append(f'{parent}.worldMatrix[0]')
	else:
		cmds.warning(f'Incorrect type: {type}. Please choose either point or parent.')
		return

	for i, node in enumerate(matrix_stack):
		if isinstance(node, list):
			cmds.setAttr(f'{mtx_cons_mmt}.matrixIn[{i}]', node, type = 'matrix')
		else:
			cmds.connectAttr(node, f'{mtx_cons_mmt}.matrixIn[{i}]')

	cmds.connectAttr(f'{target_parent}.worldInverseMatrix[0]', f'{mtx_cons_mmt}.matrixIn[{len(matrix_stack)}]')
	#cmds.connectAttr(f'{mtx_cons_mmt}.matrixSum', f'{target}.offsetParentMatrix')	

	type_selection_pmt = create_node('pickMatrix', base,  element + elem_name + ['pick'], number, side)
	off_types = ['translate', 'rotate', 'scale']
	off_types = [type for type in off_types if type not in channels]

	for type in off_types:
		cmds.setAttr(f'{type_selection_pmt}.use{type.capitalize()}', 0)

	cmds.connectAttr(f'{mtx_cons_mmt}.matrixSum', f'{type_selection_pmt}.inputMatrix')
	cmds.connectAttr(f'{type_selection_pmt}.outputMatrix', f'{target}.offsetParentMatrix')

	# ———————————————— store Orginal Values —————————————————
	# -------- For reconnecting purpose in the future -------
	if store_orig:
		attr_name = 'originalMatrix'
		if not cmds.attributeQuery(attr_name, node = target):
			cmds.addAttr(target, ln = attr_name, at='matrix')
		orig_mtx = cmds.getAttr(f'{target}.worldMatrix[0]')
		cmds.setAttr(f'{target}.{attr_name}', orig_mtx, type='matrix')

	if cmds.objectType(target) == 'joint':
		if store_orig:
			joint_orient_val = cmds.joint(target, o=True, q=True)
			attr_name = 'originalOrientation'
			if not cmds.attributeQuery(attr_name, node = target):
				cmds.addAttr(target, ln = attr_name, at='double3')
			for ax in 'XYZ':
				cmds.addAttr( target, ln =f'{attr_name}{ax}', at = 'double', p = attr_name )
				
			cmds.setAttr(f'{target}.{attr_name}', *joint_orient_val)
		cmds.setAttr(f'{target}.jo', *[0,0,0])

	cmds.setAttr(f'{target}.rotate', *[0,0,0])
	cmds.setAttr(f'{target}.t', *[0,0,0])


def create_local_world(local=None, world=None, target=None, types=['rotate'], attr_name='worldOrient', ctrl=None, dv=0.0):
	'''
	create local world space switch using matrix
	:param target (str): target object, use 'upper' for creating locwor group above ctrl
	:param types (str list): translate, rotate, scale, shear
	:param dv (float): default value. 0.0=local, 1.0=world
	'''
		
	elem_name = ['locwor']

	if target == 'upper':
		group = create_offset_group([ctrl], elem_name)
		target = group[ctrl][0]

	base, element, number, side, suffix = NAMER.extract(target)

	target_parent = cmds.listRelatives(target, p=True)[0]

	local_mtx = om.MMatrix(cmds.getAttr(f'{local}.worldMatrix[0]'))
	world_mtx = om.MMatrix(cmds.getAttr(f'{world}.worldMatrix[0]'))

	target_mtx = om.MMatrix(cmds.getAttr(f'{target}.worldMatrix[0]'))

	# —————— LOCAL ——————

	local_mtx_cons_mmt = create_node('multMatrix', base, element + ['local'] , number, side)
	offset = not (target_mtx.isEquivalent(local_mtx, 1e-10))
	mtx_channel = 0
	if offset:
		offset_matrix = target_mtx * local_mtx.inverse()
		cmds.setAttr( f'{local_mtx_cons_mmt}.matrixIn[{mtx_channel}]', offset_matrix, type='matrix')
		mtx_channel += 1

	cmds.connectAttr(f'{local}.worldMatrix[0]', f'{local_mtx_cons_mmt}.matrixIn[{mtx_channel}]')
	cmds.connectAttr(f'{target_parent}.worldInverseMatrix[0]', f'{local_mtx_cons_mmt}.matrixIn[{mtx_channel+1}]')

	# —————— WORLD ——————
	world_mtx_cons_mmt = create_node('multMatrix', base, element + ['world'] , number, side)
	offset_matrix = target_mtx * world_mtx.inverse()
	cmds.setAttr( f'{world_mtx_cons_mmt}.matrixIn[0]', offset_matrix, type='matrix')
	cmds.connectAttr(f'{world}.worldMatrix[0]', f'{world_mtx_cons_mmt}.matrixIn[{mtx_channel}]')
	cmds.connectAttr(f'{target_parent}.worldInverseMatrix[0]', f'{world_mtx_cons_mmt}.matrixIn[{mtx_channel+1}]')

	blend_bmt = create_node('blendMatrix', base, element + ['locwor', 'blend'], number, side)

	cmds.connectAttr(f'{local_mtx_cons_mmt}.matrixSum', f'{blend_bmt}.inputMatrix')
	cmds.connectAttr(f'{world_mtx_cons_mmt}.matrixSum', f'{blend_bmt}.target[0].targetMatrix')

	type_selection_pmt = create_node('pickMatrix', base,  element + ['locwor', 'pick'], number, side)

	off_types = ['translate', 'rotate', 'scale', 'shear']
	off_types = [type for type in off_types if type not in types]

	for type in off_types:
		cmds.setAttr(f'{type_selection_pmt}.use{type.capitalize()}', 0)

	cmds.connectAttr(f'{blend_bmt}.outputMatrix', f'{type_selection_pmt}.inputMatrix')
	cmds.connectAttr(f'{type_selection_pmt}.outputMatrix', f'{target}.offsetParentMatrix')

	cmds.setAttr(f'{target}.rotate', *[0,0,0])
	cmds.setAttr(f'{target}.t', *[0,0,0])

	cmds.addAttr( ctrl, ln = attr_name, at = 'float', min = 0, max = 1, dv = dv, k = True )
	cmds.connectAttr(f'{ctrl}.{attr_name}', f'{blend_bmt}.target[0].weight')


# ——————————————————————————————————————————————————————————————————————

def direct_connect(parents=None, targets =None, channels = ['t', 'r', 's']):
	parents = parents or cmds.ls(sl=True)[-1] 
	targets = targets or cmds.ls(sl=True)[:-1] 
	try:
		if len(parents) != len(targets):
			for target in targets:
				for channel in channels:
					cmds.connectAttr(f'{parents}.{channel}', f'{target}.{channel}')
		else:
			for parent, target in zip(parents, targets):
				for channel in channels:
					cmds.connectAttr(f'{parent}.{channel}', f'{target}.{channel}')
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

def constrain_switch(parent_a='', parent_b='', target='', attr_name='', follow_type='parent', ctrl='', multiply = True, dv=0, min=0, max=1):
	cmds.addAttr( ctrl, ln = attr_name, at = 'float', min = 0, max = 1, dv = dv, k = True )
	cons_node = create_constrain([parent_a, parent_b], target, follow_type)[0][0]
	base, element, number, corner_side, suffix = NAMER.extract(ctrl)
	if multiply:
		val_mul_mdl = create_node('multDoubleLinear', base, element, number, corner_side)
		cmds.setAttr( f'{val_mul_mdl}.i2', 0.1)
		cmds.connectAttr(f'{ctrl}.{attr_name}', f'{val_mul_mdl}.i1')
		output = f'{val_mul_mdl}.o'
	else:
		output = f'{ctrl}.{attr_name}'
	cmds.connectAttr(output, f'{cons_node}.{parent_b}W1')
	space_switch_rev = create_node('reverse', base, element, number, corner_side)
	cmds.connectAttr(output, f'{space_switch_rev}.ix')
	cmds.connectAttr(f'{space_switch_rev}.ox', f'{cons_node}.{parent_a}W0')
	output_attr = f'{ctrl}.{attr_name}'
	return output_attr

def space_switch(parentA = 'top_ctrl', parentB = 'base_ctrl', attr = 'followPosition', target_grp = '', follow_type = 'point', ctrl = 'mid_ctrl', dv = 0 ):

	if not target_grp:
		target_grp = create_offset_group([ctrl], offset_names=['Space'])
		target_grp = target_grp[ctrl][0]

	base, element, number, side, suffix = NAMER.extract(target_grp)
	element = element if element else []

	world_grp = create_node('group', base, element + [follow_type, 'wor'], number, side, suffix)
	local_grp = create_node('group', base, element + [follow_type, 'loc'], number, side, suffix)
	cmds.matchTransform(world_grp, target_grp)
	cmds.matchTransform(local_grp, target_grp)
	# create_constrain([parentA], local_grp)
	# create_constrain([parentB], world_grp)
	cmds.parent(local_grp, parentA)
	cmds.parent(world_grp, parentB)

	cons = create_constrain( parents=[local_grp, world_grp], target=target_grp, type=follow_type, maintain_offset=True)[0][0]

	if not cmds.attributeQuery(attr, node=ctrl, exists=True):
		cmds.addAttr( ctrl, ln = attr, at = 'float', min = 0, max = 1, dv = dv, k = True )

	switch_rev = create_node('reverse', base, ['space'], None, side)
	cmds.connectAttr(f'{ctrl}.{attr}', f'{switch_rev}.ix')
	cmds.connectAttr(f'{switch_rev}.ox', f'{cons}.{local_grp}W0')
	cmds.connectAttr(f'{ctrl}.{attr}', f'{cons}.{world_grp}W1')

	return local_grp, world_grp

def fk_ik_switch(
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
			element = element if element else []
			element = element + [attr_name, feat]
			bcl_name = NAMER.format(base, element, number, side, 'bcl')

			if not cmds.objExists(bcl_name):
				switch = create_node('blendColors', base, element, number, side)
				cmds.connectAttr(f'{ctrl}.{attr_name}', f'{switch}.blender')
			else:
				switch = bcl_name	
			cmds.connectAttr(f'{parents_ik[i]}.{feat[0]}', f'{switch}.c1')
			cmds.connectAttr(f'{parents_fk[i]}.{feat[0]}', f'{switch}.c2')
			cmds.connectAttr(f'{switch}.op', f'{target}.{feat[0]}')

	if ik_ctrl_grp:
		side = parser.find_element(ctrl, 'sides')
		rev_name = NAMER.format(setup_name, [attr_name], '', side, 'rev')
		cmds.connectAttr(f'{ctrl}.{attr_name}', f'{ik_ctrl_grp}.v')
		rev = cmds.createNode('reverse', n = rev_name)
		cmds.connectAttr(f'{ctrl}.{attr_name}', f'{rev}.ix')
		cmds.connectAttr(f'{rev}.ox', f'{fk_ctrl_grp}.v')

def add_follow_attr(parents = [], target = '', attr_name = 'follow', ctrl = '', min=0, max=1, dv=0.5, multiply=False, connect_type = 'parent'):

	cmds.addAttr( ctrl, ln=attr_name, at='float', min=min, max=max, dv=dv, k=True )
	cons_node = create_constrain(parents, target, connect_type, maintain_offset=True)[0][0]
	#cmds.setAttr(f'{cons_node}.interpType', 2)
	output = f'{ctrl}.{attr_name}'

	base, element, number, corner_side, suffix = NAMER.extract(ctrl)
	if multiply:
		val_mul_mdl = create_node('multDoubleLinear', base, element, number, corner_side)
		cmds.setAttr( f'{val_mul_mdl}.i2', 0.1)
		cmds.connectAttr(f'{ctrl}.{attr_name}', f'{val_mul_mdl}.i1')
		output = f'{val_mul_mdl}.o'

	cmds.connectAttr(output, f'{cons_node}.{parents[1]}W1')

	space_switch_rev = create_node('reverse', base, element, number, corner_side)
	cmds.connectAttr(output, f'{space_switch_rev}.ix')
	cmds.connectAttr(f'{space_switch_rev}.ox', f'{cons_node}.{parents[0]}W0')

def create_guide_curve(ctrl = '', target = '', parent = '', curve_elem = 'guide'): #25Dec01
	if not parent:
		parent = ctrl
	base, element, number, side, _ = NAMER.extract(target)
	element = element + [curve_elem] if element else [curve_elem]
	curve_name = NAMER.format(base, element , number, side, 'crv')

	guide_crv = cmds.curve( d = 1 , p = [ ( 0 , 0 , 0 ) , ( 0 , 0 , 0 ) ]) 
	guide_crv = cmds.rename(guide_crv, curve_name)
	attrs = ['tx', 'ty', 'tz','rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']
	for attr in attrs:
		cmds.setAttr( f'{guide_crv}.{attr}', k = False )
		cmds.setAttr( f'{guide_crv}.{attr}', l = True )

	ctrl_base, ctrl_element, ctrl_number, ctrl_side, _ = NAMER.extract(ctrl) 
	ctrl_clt_name = NAMER.format(ctrl_base, ctrl_element, ctrl_number, ctrl_side, '_clt')
	target_clt_name = NAMER.format(base, element, number, side, '_clt')
	clt_a = cmds.cluster( '{0}.cv[0]'.format( guide_crv ) , wn = ( ctrl , ctrl ))[ 0 ] 
	clt_a = cmds.rename(clt_a, ctrl_clt_name)
	clt_b = cmds.cluster( '{0}.cv[1]'.format( guide_crv ) , wn = ( target , target ))[ 0 ] 
	clt_b = cmds.rename(clt_b, target_clt_name)
	cmds.select( cl = True )

	cmds.setAttr( '{0}.ove'.format( guide_crv ), 1)
	cmds.setAttr( '{0}.overrideRGBColors'.format( guide_crv ), 1)
	cmds.setAttr( '{0}.overrideColorRGB'.format( guide_crv ), 0.14,0.14,0.14)
	cmds.setAttr( '{0}.overrideDisplayType'.format( guide_crv ), 1 )
	cmds.setAttr( '{0}.inheritsTransform'.format( guide_crv ), 0 )
	cmds.parent( guide_crv, parent )
	cmds.select( cl = True )

	return guide_crv

def set_driven_key(main_ctrl='', attr = '', driven = '', values = {0:0, 180:-50,-180:50}, limit = True):
	
	if not cmds.attributeQuery(attr, node=main_ctrl, exists=True):
		if limit:
			min_val = min(values.keys())
			max_val = max(values.keys())
			cmds.addAttr( main_ctrl, ln = attr, at = 'float', min = min_val, max = max_val, dv = 0, k = True )
		else:
			cmds.addAttr( main_ctrl, ln = attr, at = 'float', dv = 0, k = True )

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
		i+=1
	return key

def pole_vector_position(joints, offset = 1, create_output='joint', name = None):
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

	side = parser.find_element(joints[0], 'sides')
	elem = 'pv' if name else 'position'
	name = name if name else 'pv'
	if create_output:
		output_obj = create_node(create_output, name, [elem], None, side)
		cmds.move( pv_posi_vector[0], pv_posi_vector[1], pv_posi_vector[2], output_obj, r = True  )
		return output_obj
	return [pv_posi_vector[0], pv_posi_vector[1], pv_posi_vector[2]]

def attr_separator(ctrl, ln='extra', enum_name = '—————'):
	ln = '_____' + ln
	cmds.addAttr( ctrl, ln = ln, at = 'enum', en = enum_name , k = True )
	cmds.setAttr( f'{ctrl}.{ln}', l=True )
	#cmds.setAttr( f'{ctrl}.{ln}', k=False )

def add_enum_space_switch( parent_spaces = ['r_pelvis_ctl'],
							world_space = 'r_global_gimbal_space_grp',
							attr_name = 'follow',
							spaces_name = ['local', 'world'],
							target = 'r_thigh_fk_offset_grp',
							ctrl = 'r_thigh_fk_ctl',
							type = 'orient',
							default_index = 1,
							#mod_grp = None
						):

	# if not cmds.objExists('spaces_grp'):
	# 	spaces_grp = create_node('group', 'spaces', None, None, None)
	# 	if mod_grp:
	# 		cmds.parent(spaces_grp, mod_grp)
	# else:
	# 	spaces_grp = 'spaces_grp'
		
	if world_space:
		parent_spaces = [world_space] + parent_spaces 

	enum_names = ':'.join(spaces_name)
	cmds.addAttr(ctrl, ln = attr_name, at='enum', en=enum_names, dv=default_index, k=True )

	target_name, target_element, target_number, target_side, suffix = NAMER.extract(target) 
	target_base_name = parser.get_base_name(target_name, first_name=True)
	target_element = target_element if target_element else []

	parent_con = create_constrain(parent_spaces, target, type=type, maintain_offset=True)[0][0]

	try:
		cmds.setAttr(f'{parent_con}.interpType', 2)
	except:pass
	
	if len(spaces_name) > 2:
		for i, name in enumerate(spaces_name):
			space_cdt = create_node(node_type='condition', base=target_name, elements=target_element+[name], number=target_number, side=target_side )
			cmds.setAttr( f'{space_cdt}.st', i)
			cmds.setAttr( f'{space_cdt}.ctr', 1)
			cmds.setAttr( f'{space_cdt}.cfr', 0)
			cmds.connectAttr(f'{ctrl}.{attr_name}', f'{space_cdt}.ft')
			cmds.connectAttr(f'{space_cdt}.ocr', f'{parent_con}.{parent_spaces[i]}W{i}')
	else:
		cmds.connectAttr(f'{ctrl}.{attr_name}', f'{parent_con}.{parent_spaces[1]}W1')
		space_switch_rev = create_node(node_type='reverse', base=target_name, elements=target_element+[attr_name], number=target_number, side=target_side )
		cmds.connectAttr(f'{ctrl}.{attr_name}', f'{space_switch_rev}.ix')
		cmds.connectAttr(f'{space_switch_rev}.ox', f'{parent_con}.{parent_spaces[0]}W0')

def over_and_out(module_name = '', output_name = ''):
	cmds.select(cl=True)
	output_name = output_name.replace('None', '')
	print(f'Created\t{module_name}:\t\t{output_name}')

def aim_follow(parent=None, upper_parent = None, target=None, aim='x', up='y', attr_name = None, ctrl = None, dv = 1):
	elem_name = [attr_name] or ['follow']

	if target == 'upper':
		group = create_offset_group([ctrl], elem_name)
		target = group[ctrl][0]

	base, element, number, side, suffix = NAMER.extract(target)

	locator = create_node('locator', base, element + elem_name, number, side)
	cmds.matchTransform(locator, upper_parent)
	aim_vector = axis_convert(aim, 'vector')
	up_vector = axis_convert(up, 'vector')
	up_str = axis_convert(up, 'absolute_letter')
	create_constrain([upper_parent], locator, 'point')
	
	cmds.delete(cmds.aimConstraint(parent, locator, aimVector = aim_vector, upVector = up_vector, wut = 'objectrotation', wu = up_vector, wuo = parent, mo = False))
	skip_axes = 'xyz'.replace(up_str,'')
	skip_axes = [ax for ax in skip_axes]
	cmds.aimConstraint(parent, locator, aimVector = aim_vector, upVector = up_vector, wut = 'objectrotation', wu = up_vector, wuo = parent, mo = False)#, skip = skip_axes)

	create_local_world(local=locator, world=upper_parent, target=target, types=['translate', 'rotate'], attr_name=attr_name, ctrl=ctrl, dv=dv)

	return locator

def joint_label(remove = None, remove_from_last = 2, force_on=False):
	selection = cmds.ls(sl=True)
	current = cmds.getAttr( f'{selection[0]}.drawLabel')
	stage_val = 1 if current == 0 else 0
	stage_val = stage_val if not force_on else 1

	for jnt in selection:
		if cmds.objectType(jnt) != 'joint':
			continue
		else:
			cmds.setAttr( f'{jnt}.drawLabel', stage_val)
		full_name = jnt
		if remove:
			full_name = jnt.replace(remove, '')
		if remove_from_last:
			full_name = full_name.split('_')[:-remove_from_last]
			full_name = '_'.join(full_name)

		cmds.setAttr( f'{jnt}.type', 18 )
		cmds.setAttr( f'{jnt}.otherType',  full_name , type = 'string' )
	return None

def lock_attrs(obj='', attrs = ['t', 'r', 's'], unlock = False):
	if not obj:
		obj = cmds.ls(sl=True)[0]
	for attr in attrs:
		for ax in 'xyz':
			try:
				cmds.setAttr(f'{obj}.{attr}{ax}', l = not unlock)
				#cmds.setAttr(f'{obj}.{attr}{ax}', cb = not unlock)
			except:pass

def delete_orig():
	orig_nodes=[]
	selection = cmds.ls(sl=True)
	for sel in selection:
		shapes = cmds.listRelatives(sel, s=True)
		for shape in shapes:
			if 'Orig' in shape:
				orig_nodes.append(shape)
	cmds.delete(orig_nodes)

def create_connection(parent, target, connection_type='None'):
	if connection_type == 'None':
		return
	if connection_type in ('point', 'parent', 'orient', 'scale', 'parentScale'):
		create_constrain(parents=[parent], target=target, type=connection_type)
	elif connection_type == 'direct':
		direct_connect([parent], [target])
	elif 'matrix' in connection_type:
		mtx_type = connection_type.split('_')[-1]
		matrix_constrain(parent, target, mtx_type)
	else:
		cmds.warning(f'Unknown connection type: {connection_type}')

def create_xyz(objs=None, connection_type=None, scale=1, bp_jnt=False,):
	temp_loc = False
	if not objs:
		if cmds.ls(sl=True):
			objs = cmds.ls(sl=True)
		else:
			objs = cmds.spaceLocator(n='temp_xyz_loc')
			temp_loc = True
		
	colors = ['red', 'mayaGreen', 'blue']
	for obj in objs:
		axis_crvs = []
		axis_shapes = []
		base, element, number, side, suffix = NAMER.extract(obj)
		element = element if element else []
		for i, axis in enumerate('xyz'):
			crv_name = NAMER.format(base, element + [axis], number, side, 'ctrl')
			ax_crv = bc.Controller.create_curve(ctrl_name=crv_name, 
								shape=f'text_{axis}', 
								color=colors[i], 
								line_width=scale, 
								scale=scale, 
								close_curve = False)
			axis_crvs.append(ax_crv)
			shape = cmds.listRelatives(ax_crv, s=True)[0]
			axis_shapes.append(shape)
		crv_name = NAMER.format(base, element, number, side, 'ctrl')
		axis_ctrl = bc.Controller.create_curve(ctrl_name=crv_name, 
								shape='axis', 
								color='white', 
								line_width=scale*3.0, 
								scale=scale*10)

		cmds.parent(axis_shapes, axis_ctrl, r=True, s=True)
		grp = create_offset_group(axis_ctrl)
		grp = grp[axis_ctrl][0]
		snap([obj], grp)
		cmds.delete(axis_crvs)
		if not bp_jnt:
			create_connection(axis_ctrl, obj, connection_type)
			if temp_loc:
				cmds.delete(objs)
			return grp, axis_ctrl
		else:
			return grp, axis_ctrl


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


