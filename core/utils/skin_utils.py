import os
from importlib import reload
import maya.cmds as cmds
from . import io_utils as io
from ..naming import namer_factory as naming 
from ..naming import current_project
from ..naming import templates

reload(io)
reload(naming)
reload(current_project)
reload(templates)

FOLDER_NAME = 'data'

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

def get_skin_cluster_name(object):
	shape = cmds.listRelatives( object, s=True, f=True)[0]
	history = cmds.listHistory(shape)
	skin_cluster_nodes = cmds.ls(history, typ = 'skinCluster')
	if not skin_cluster_nodes:
		cmds.warning(f"{object} has not been skinned.")
		return
	return skin_cluster_nodes

def export_skin_weight(objects=None):
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

		skin_cluster = get_skin_cluster_name(obj)
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
			io.export_data(file_name=file_name, data=skin_weight_dict, path=export_path)
		else:
			no_data_list.append(obj)
	if replace_list:
		print(f'replaced weights: {replace_list}')
	if no_data_list:
		print(f'no data objects: {no_data_list}')
	
def import_skin_weight(objects=None, search_for=None, replace_with=None, prefix='', suffix='', name_space=None, create_missing_joints = False, path=None):
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
			cmds.setAttr( f'{skin_node}.skinningMethod', envelope )
			cmds.setAttr( f'{skin_node}.skinningMethod', skinningMethod )
			cmds.setAttr( f'{skin_node}.skinningMethod', useComponents )
			cmds.setAttr( f'{skin_node}.skinningMethod', deformUserNormals )
			cmds.setAttr( f'{skin_node}.normalizeWeights', False )
			cmds.skinPercent( skin_node, obj, nrm = False, prw = 100 )
			cmds.setAttr( f'{skin_node}.normalizeWeights', normalizeWeights )

			if obj_type == 'mesh':
				total_vertex = cmds.polyEvaluate( obj, v = True )
				for iVtx in range( 0, total_vertex ):
					sVtx = str(iVtx)
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
		skc = cmds.rename(skc, node_name)
	return skc





