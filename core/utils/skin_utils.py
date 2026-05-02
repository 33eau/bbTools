import os
from importlib import reload
import maya.cmds as cmds
import maya.mel as mel

from maya.api import OpenMaya as om
from maya.api import OpenMayaAnim as oma

from . import io_utils as io
from ..naming import namer_factory as naming 
from ..naming import current_project
from ..naming import parser
from ..naming import templates

reload(io)
reload(naming)
reload(current_project)
reload(parser)
reload(templates)

FOLDER_NAME = 'data'

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

def get_skin_cluster_name(object, log=False):
	shape = cmds.listRelatives( object, s=True, f=True)[0]
	history = cmds.listHistory(shape, lv=3)
	skin_cluster_nodes = cmds.ls(history, typ = 'skinCluster')
	if log:
		if not skin_cluster_nodes:
			cmds.warning(f"{object} has not been skinned.")
		return None
	return skin_cluster_nodes

def export_skin_weight(objects=None, log=False, skc = None):
	export_path = io.define_path(FOLDER_NAME)
	replace_list = []
	no_data_list = []

	if objects is None:
		objects = cmds.ls(sl=True)

	for obj in objects:
		if ':' in obj:
			obj = obj.split(':')[-1]
		
		skin_weight_dict = {}

		file_name = f'skc_{obj}.weight' 	
		shape = cmds.listRelatives(obj, s=True, f=True)[0]
		obj_type = cmds.objectType(shape)
		skin_weight_dict['type'] = obj_type
		skin_weight_dict['name'] = []

		skin_cluster = skc if skc else get_skin_cluster_name(obj)
		if skin_cluster:
			for skin in skin_cluster:
				skin_weight_dict['name'].append(skin)
				skin_weight_dict[skin] = {}
				envelope = cmds.getAttr( f'{skin}.envelope')
				skinningMethod = cmds.getAttr( f'{skin}.skinningMethod')
				useComponents = cmds.getAttr( f'{skin}.useComponents')
				normalizeWeights = cmds.getAttr( f'{skin}.normalizeWeights')
				deformUserNormals = cmds.getAttr( f'{skin}.deformUserNormals')
				influences = cmds.skinCluster( skin, q = True, inf = True )
				
				skin_weight_dict[skin]['envelope'] = envelope
				skin_weight_dict[skin]['skinningMethod'] = skinningMethod
				skin_weight_dict[skin]['useComponents'] = useComponents
				skin_weight_dict[skin]['normalizeWeights'] = normalizeWeights
				skin_weight_dict[skin]['deformUserNormals'] = deformUserNormals
				skin_weight_dict[skin]['influences'] = influences
				skin_weight_dict[skin]['weight_data'] = {}

				if obj_type == 'mesh':		
					for i in range(0, cmds.polyEvaluate( obj , v = True )) :
						skin_value = cmds.skinPercent( skin , f'{obj}.vtx[{i}]' , q = True , v = True )
						skin_weight_dict[skin]['weight_data'][i] = skin_value
						
				elif obj_type == 'nurbsSurface':
					spans_uv = cmds.getAttr(f'{obj}.spansUV')[0]
					degree_uv = max(cmds.getAttr(f'{obj}.degreeUV')[0])
					total_cv = max(spans_uv) + (degree_uv-1)
					for iCv in range(0, total_cv):
						for iSub in range(0, degree_uv+1):
							skin_value = cmds.skinPercent( skin , f'{obj}.cv[{iCv}][{iSub}]' , q = True , v = True )
							skin_weight_dict[skin]['weight_data'][f'[{iCv}]:[{iSub}]'] = skin_value
			file_path = os.path.join(export_path, file_name)
			if os.path.isdir( file_path ):
				replace_list.append(obj)
			io.export_data(file_name=file_name, data=skin_weight_dict, path=export_path, log = log)
		else:
			no_data_list.append(obj)
	if replace_list:
		print(f'REPLACED weights: {replace_list}')
	if no_data_list:
		print(f'no data objects: {no_data_list}')
	
def import_skin_weight(objects=None, search_for=None, replace_with=None, prefix='', suffix='', name_space=None, create_missing_joints = False, path=None, log = False):
	if path:
		import_path = path
	else:
		import_path = io.define_path(FOLDER_NAME)
	
	if objects is None:
		objects = cmds.ls(sl=True)

	no_data_list = []
	skin_nodes = []

	for obj in objects:
		file_name = f'skc_{obj}.weight'
		file_path = os.path.join(import_path, file_name)
		if not os.path.exists( file_path ):
			no_data_list.append(obj)
			print(f'{file_path} DOESNT EXIST.')
			continue

		shape = cmds.listRelatives(obj, s=True, f=True)[0]
		obj_type = cmds.objectType(shape)

		skin_weight_dict = io.import_data(file_name=file_name, folder_name=FOLDER_NAME, path=import_path)
		expected_type = skin_weight_dict['type']

		for skin in skin_weight_dict['name']:
			envelope = skin_weight_dict[skin]['envelope']
			skinningMethod = skin_weight_dict[skin]['skinningMethod']
			useComponents = skin_weight_dict[skin]['useComponents']
			normalizeWeights = skin_weight_dict[skin]['normalizeWeights']
			deformUserNormals = skin_weight_dict[skin]['deformUserNormals']
			influences = skin_weight_dict[skin]['influences']
			weight_data = skin_weight_dict[skin]['weight_data']


			if obj_type != expected_type:
				cmds.warning(f'Different object type {obj}: {obj_type}, expected {expected_type}.')		

			
			missing_list = []
			for i, jnt in enumerate(influences):
				if name_space:
					jnt = name_space + ':' + jnt
					influences[i] = jnt
				if search_for:
					jnt = jnt.replace(search_for, replace_with)
					jnt = f'{prefix}{jnt}{suffix}'
					influences[i] = jnt

				if not cmds.objExists(jnt):
					missing_list.append(jnt)
					if create_missing_joints:
						cmds.joint(n=jnt)
					else:
						cmds.warning(f'Missing joint: {jnt} \t\t\t for {obj} —— {skin}')
			
			old_skc = get_skin_cluster_name(obj)
			if old_skc:
				cmds.skinCluster( old_skc, e = True, ub = True )
			
			skin_node = cmds.skinCluster( influences, obj, tsb = True, n = skin )[0]
			skin_nodes.append(skin_node)
			cmds.setAttr( f'{skin_node}.envelope', envelope )
			cmds.setAttr( f'{skin_node}.skinningMethod', skinningMethod )
			cmds.setAttr( f'{skin_node}.useComponents', useComponents )
			cmds.setAttr( f'{skin_node}.deformUserNormals', deformUserNormals )
			# cmds.setAttr( f'{skin_node}.normalizeWeights', False )
			# cmds.skinPercent( skin_node, obj, nrm = False, prw = 100 )
			cmds.setAttr( f'{skin_node}.normalizeWeights', normalizeWeights )

			if obj_type == 'mesh':
				total_vertex = cmds.polyEvaluate( obj, v = True )
				for iVtx in range( 0, total_vertex ):
					sVtx = str(iVtx)
					if len(influences) == 1:
						return
					for i, jnt in enumerate( influences ):
						value = weight_data[sVtx][i]
						target_vtx = f'{obj}.vtx[{iVtx}]'
						cmds.skinPercent( skin_node, target_vtx, transformValue=[(jnt, value)] )

			elif obj_type == 'nurbsSurface':
				spans_uv = cmds.getAttr(f'{obj}.spansUV')[0]
				degree_uv = max(cmds.getAttr(f'{obj}.degreeUV')[0])
				total_cv = max(spans_uv) + (degree_uv-1)
				for iCv in range(0, total_cv):
					for iSub in range(0, degree_uv+1):
						for i, jnt in enumerate( influences ):
							working_vtx = f'[{iCv}]:[{iSub}]'
							cmds.skinPercent( skin_node , f'{obj}.cv[{iCv}][{iSub}]' , tv = [(jnt, weight_data[working_vtx][i])])

	if no_data_list:
		print( f'noDataObjs : {no_data_list}')
	if log:
		print(f'{len(skin_nodes)} has been imported.')



def bind_skin(jnts, target_obj, **kwargs):
	"""
	This function accepts kwargs.
	:param jnts: bind joints
	:param target_obj: target object
	:param return_type: named skinCluster
	"""
	skin = cmds.skinCluster(jnts, target_obj, tsb=True, mi=2, dr=2, rui=False, nw=1, bindMethod=0, **kwargs)
	named_skin = name_it([target_obj])
	return named_skin

def name_it(objects=''):
	if not objects:
		objects = cmds.ls(sl=True)
	for obj in objects:
		if not cmds.objectType(obj) == 'skinCluster':
			skc = get_skin_cluster_name(obj)
		else:
			skc = obj
			obj = cmds.listConnections(f'{skc}.input[0].inputGeometry')[0]
		base, element, number, side, suffix = NAMER.extract(obj) 
		element.append(suffix)
		node_name = NAMER.format(base, element, number, side, templates.TYPE_SUFFIX['skinCluster'])
		skc = cmds.rename(skc, f'{obj}_skc')
	return skc

def unbind_skin(obj = ''):
	skin_cluster_nodes = get_skin_cluster_name(obj)
	orig_nodes = []
	for skin_node in skin_cluster_nodes:
		connections = cmds.listConnections(skin_node, c=True)
		for node in connections:
			if 'originalGeometry' in node:
				print(node)
				orig_node = cmds.listConnections(node, p=True)[0]
				orig_node = orig_node.split('.')[0]
				orig_nodes.append(orig_node)

	for skin in skin_cluster_nodes:
		cmds.skinCluster(skin, e = True, ub=True)
		#print(f'Unbind {skin} successfully.')
	cmds.delete(orig_nodes)
	return None

def get_api_info(obj):
	"""Returns (MDagPath, MFnSkinCluster, MObject components)"""
	sel = om.MSelectionList()
	sel.add(obj)
	dag_path = sel.getDagPath(0)

	sc_names = get_skin_cluster_name(obj)
	if not sc_names: return None

	sel.add(sc_names[0])
	sc_obj = sel.getDependNode(1)
	fn_skin = oma.MFnSkinCluster(sc_obj)

	# Determine Component Type
	shape = cmds.listRelatives(obj, s=True, f=True)[0]
	obj_type = cmds.objectType(shape)

	comp_fn = om.MFnSingleIndexedComponent()
	if obj_type == 'mesh':
		comp_obj = comp_fn.create(om.MFn.kMeshVertComponent)
		type_id = 0
	else: # nurbsSurface
		comp_obj = comp_fn.create(om.MFn.kNurbsSurfaceCVComponent)
		type_id = 1
	
	return dag_path, fn_skin, comp_obj, type_id

def export_skin(obj, path=None):
	if path is None:
		work_path = cmds.workspace(q=1, rd=1)
		data_path = work_path + FOLDER_NAME
		path = os.path.join(data_path, f"{obj}.skinweight")
	else:
		path = os.path.join(path, f"{obj}.skinweight")

	dag_path, fn_skin, comp_obj, type_id = get_api_info(obj)

	# Get all influence objects (joints)
	inf_dags = fn_skin.influenceObjects()
	inf_names = [inf.partialPathName() for inf in inf_dags]

	# GET ALL WEIGHTS AT ONCE
	weights, _ = fn_skin.getWeights(dag_path, comp_obj)

	work_path = cmds.workspace(q=1, rd=1)
	data_path = work_path + FOLDER_NAME
	path = os.path.join(data_path, f"{obj}.skinweight")
	io.export_binary_data(path, inf_names, list(weights), type_id)
	print(f"Exported {obj} weights.")

def import_skin(obj, path = None, search_for=None, replace_with=None, name_space=None):
	if path is None:
		work_path = cmds.workspace(q=1, rd=1)
		data_path = work_path + FOLDER_NAME
		path = os.path.join(data_path, f"{obj}.skinweight")
	else:
		path = os.path.join(path, f"{obj}.skinweight")

	# 1. Load Data
	saved_type, saved_infs, saved_weights = io.import_binary_data(path)

	# 2. Get API objects for target
	dag_path, fn_skin, comp_obj, current_type = get_api_info(obj)
	
	processed_infs = []
	for jnt in saved_infs:
		if name_space:
			jnt = f"{name_space}:{jnt}"
		if search_for and replace_with:
			jnt = jnt.replace(search_for, replace_with)
		processed_infs.append(jnt)

	inf_indices = om.MIntArray()
	for name in processed_infs:
		if cmds.objExists(name):
			inf_sel = om.MSelectionList()
			inf_sel.add(name)
			inf_indices.append(fn_skin.indexForInfluenceObject(inf_sel.getDagPath(0)))
		else:
			cmds.warning(f"Joint {name} not found in scene!")
	bind_skin(processed_infs, obj)
	fn_skin.setWeights(dag_path, comp_obj, inf_indices, om.MDoubleArray(saved_weights))

def mirror_skinweight():
	sel = cmds.ls(sl=True)[0]
	skin_cluster = get_skin_cluster_name(sel)[0]
	infs = cmds.skinCluster(skin_cluster, q=True, inf=True)
	for inf in infs:
		side = parser.find_element(inf, 'sides')
		op_side = 'r_' if side == 'l_' else 'l_'
		if side:
			opposite_inf = inf.replace(side, op_side, 1)
			if cmds.objExists(opposite_inf):
				try:
					cmds.skinCluster(skin_cluster, ai=opposite_inf, e=True, dr=2, lw=True, wt=0)
				except:pass
			else:
				print(f'ERROR: {opposite_inf} no exist')
	cmds.copySkinWeights(ss=skin_cluster, ds=skin_cluster, mirrorMode='YZ', surfaceAssociation='closestPoint', influenceAssociation='oneToOne', mirrorInverse = False)
	print(f'Mirrored {skin_cluster} completed')

def copy_skin(objs):
	if not objs:
		selection = cmds.ls(sl=True)
		source = selection[-1]
		targets = selection[:-1]
	else:
		source = objs[-1]
		targets = objs[:-1]

	source_skc= get_skin_cluster_name(source)[0]
	infs = cmds.skinCluster(source_skc, inf=True, q=True)

	for tgt in targets:
		target_skc = get_skin_cluster_name(tgt)
		if target_skc:
			target_skc = target_skc[0]
			try:
				cmds.skinCluster(target_skc, ai=infs, e=True, dr=2, lw=True, wt=0)
			except:pass
		else:
			target_skc = bind_skin(infs, tgt)
		cmds.copySkinWeights(ss=source_skc, ds=target_skc, noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='oneToOne')
	cmds.select(cl=True)





