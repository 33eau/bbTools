import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as openMaya
import maya.api.OpenMayaAnim as openMayaAnim
import os
import time
import numpy as np

from . import io_utils as io
from . import skin_utils as sk

FOLDER_NAME = 'skinweights'

def export_skinweight(dir_path = None, log = False):
	skin_io = SkinClusterData()
	objects = cmds.ls(sl=True)
	
	start_time = time.time()
	if dir_path is None:
		dir_path = io.define_path(FOLDER_NAME)

	for obj in objects:
		skin_io.export_data(obj, dir_path = dir_path, log = log)

	time_end = time.time()
	time_elapsed = time_end - start_time	

	print(f' 🚀 EXPORT SkinWeight: {len(objects)} object(s). At {dir_path}')
	print(f'Total time {time_elapsed}')
	cmds.select(cl=True)

	return True


def import_skinweight(objects=None, dir_path = None, log = False, search_for=None, replace_with=None, prefix=None, name_space=None):
	skin_io = SkinClusterData()
	if objects is None:
		objects = cmds.ls(sl=True)
	
	start_time = time.time()

	if dir_path is None:
		dir_path = io.define_path(FOLDER_NAME)

	for obj in objects:
		importted = skin_io.import_data(obj, dir_path = dir_path, log = False, search_for=search_for, replace_with=replace_with, prefix=prefix, name_space=name_space)

	time_end = time.time()
	time_elapsed = time_end - start_time	
	if importted:
		print(f' ✨ IMPORT SkinWeight: {len(objects)} object(s).')
	print(f'Total time {time_elapsed}')
	cmds.select(objects)

	return True


class SkinClusterData(object):
	'''
	Class for export and import skinCluster using Maya API 2.0
	'''

	def __init__(self):
		# ...class init
		self.data_io = DataIO()

		# ...vars
		self.name = ''
		self.type = 'skinCluster'
		self.weights_non_zero = []
		self.influence_map = []
		self.vert_split = []
		self.influence_names = []
		self.skinning_method = 1
		self.normalize_weights = 1
		self.geometry = None
		self.obj_type = None
		self.is_u_dominant = None
		self.blend_weights = []
		self.vertex_count = 0
		self.envelope = 1
		self.use_components = 0
		self.deform_user_normals = 1
		self.obj_type = ''
		self.is_u_dominant = None

	def get_data(self, skin_cluster):
		'''
		Collect skinCluster data
		
		:param skin_cluster (str): Name of the skinCluster node.
		'''

		# Selection list to handle Maya objects
		selection_list = openMaya.MGlobal.getSelectionListByName(skin_cluster)

		# Get the MObejct for the skin cluster node
		cluster_node = selection_list.getDependNode(0)

		# Function set for the skin cluster
		skin_fn = openMayaAnim.MFnSkinCluster(cluster_node)
		dag_path = skin_fn.getPathAtIndex(0)
		components = skin_fn.getComponentAtIndex(0)

		# Get geometry name
		geometry  = cmds.skinCluster(skin_cluster, q=True, geometry=True)[0]
		
		# Geometry node
		obj_selection = openMaya.MGlobal.getSelectionListByName(geometry)
		obj_path = obj_selection.getDagPath(0)
		obj = obj_path.node()

		# Check Type
		is_u_dominant = False
		if obj.hasFn(openMaya.MFn.kMesh):
			obj_type = 'mesh'
			mesh_fn = openMaya.MFnMesh(obj)
			num_verts = mesh_fn.numVertices
			vertex_ids = list(range(num_verts))
			# Create vertex components to query weights
			vtx_comp_fn = openMaya.MFnSingleIndexedComponent()
			vtx_components = vtx_comp_fn.create(openMaya.MFn.kCurveCVComponent)
			vtx_comp_fn.addElements(vertex_ids)

		elif obj.hasFn(openMaya.MFn.kNurbsCurve):
			obj_type = 'nurbsCurve'
			curve_fn = openMaya.MFnNurbsCurve(obj)
			num_verts = curve_fn.numCVs
			vertex_ids = list(range(num_verts))
			# Create vertex components to query weights
			vtx_comp_fn = openMaya.MFnSingleIndexedComponent()
			vtx_components = vtx_comp_fn.create(openMaya.MFn.kCurveCVComponent)
			vtx_comp_fn.addElements(vertex_ids)


		elif obj.hasFn(openMaya.MFn.kNurbsSurface):
			obj_type = 'nurbsSurface'
			surf_fn = openMaya.MFnNurbsSurface(obj)
			# Create vertex components to query weights
			vtx_comp_fn = openMaya.MFnDoubleIndexedComponent()
			vtx_components = vtx_comp_fn.create(openMaya.MFn.kSurfaceCVComponent)
			for u in range(surf_fn.numCVsInU):
				for v in range(surf_fn.numCVsInV):
					vtx_comp_fn.addElement(u, v)

		# Query weights and influence count
		weight_m_array, inf_count = skin_fn.getWeights(obj_path, vtx_components)

		# Convert MDoubleArray to numpy for performance
		weight_array = np.array(list(weight_m_array), dtype='float64')

		# Get influence joints as partial paths
		influence_objects = skin_fn.influenceObjects()
		influence_names = [ dp.partialPathName() for dp in influence_objects ]

		# Compress weight data (removes zeros)
		weights_non_zero, influence_map, vert_split = self.compress_weight_data(weight_array, inf_count)

		# Gather blend weights
		blend_weight_m_array = skin_fn.getBlendWeights(dag_path, components)

		# Set data to instance variables
		self.name = skin_cluster
		self.weights_non_zero = np.array(weights_non_zero)
		self.influence_map = influence_map
		self.vert_split = vert_split
		self.influence_names = np.array(influence_names)
		self.geometry = geometry
		self.obj_type = obj_type
		self.is_u_dominant = is_u_dominant
		self.blend_weights = np.array(blend_weight_m_array)
		self.vertex_count = len(vert_split) - 1

		# Get attributs using cmds
		self.envelope = cmds.getAttr(f'{skin_cluster}.envelope')
		self.skinning_method = cmds.getAttr(f'{skin_cluster}.skinningMethod')
		self.use_components = cmds.getAttr(f'{skin_cluster}.useComponents')
		self.normalize_weights = cmds.getAttr(f'{skin_cluster}.normalizeWeights')
		self.deform_user_normals = cmds.getAttr(f'{skin_cluster}.deformUserNormals')

		return True
	
	def export_data(self, node=None, dir_path=None, log=False):
		'''
		Export skin weight data to a .npy file

		:param node: Skinned object
		:param dir_path: Destination folder to keep the skin data
		'''
		if node is None:
			selection = cmds.ls(sl=True)
			if not selection:
				print('🚨 ERROR: Please Select Something 🚨')
				return False
			node = selection[0]
		
		sk.name_it([node])
		
		skin_cluster = mel.eval(f'findRelatedSkinCluster {node}')
		if not cmds.objExists(skin_cluster):
			print(f'🚨 ERROR: NO Skin Cluster on {node} 🚨')
			return False

		if dir_path is None:
			start_dir = cmds.workspace(q=True, rootDirectory = True)
			dir_path = cmds.fileDialog2(caption='Save Skinweights', dialogStyle=2, fileMode=3, startingDirectory=start_dir, fileFilter='*.npy', okCaption='Select')

			if not dir_path:
				return False
			dir_path = dir_path[0]

		#folder_path = os.path.join(dir_path, FOLDER_NAME)
		file_name = f'skincluster__{node}.npy'
		#file_path = os.path.join(folder_path, file_name)
		file_path = os.path.join(dir_path, file_name)

		#timing
		# start_time = time.time()

		self.get_data(skin_cluster)

		# time_elapsed = time.time() - start_time
		# print(f'Get Data Elapsed: {time_elapsed}')

		# ...construct data_array
		legend = (
		'legend', 'weights_non_zero', 'vert_split', 'influence_map',
		'influence_names', 'geometry', 'obj_type', 'is_u_dominant', 'blend_weights', 'vertex_count',
		'name', 'envelope', 'skinning_method', 'use_components',
		'normalize_weights', 'deform_user_normals', 'type'
		)

		data = [
		legend, self.weights_non_zero, self.vert_split, self.influence_map,
		self.influence_names, self.geometry, self.obj_type, self.is_u_dominant, self.blend_weights, self.vertex_count,
		self.name, self.envelope, self.skinning_method, self.use_components,
		self.normalize_weights, self.deform_user_normals, self.type
		]

		# #timing
		# start_time = time.time()
		if log:
			print(data)
		np.save(file_path, np.array(data, dtype=object), allow_pickle=True)

		# time_elapsed = time.time() - start_time
		# print(f'Save Data Elapsed: {time_elapsed}')

		return True

	def set_data(self, skin_cluster):
		selection_list = openMaya.MGlobal.getSelectionListByName(skin_cluster)
		cluster_node = selection_list.getDependNode(0)

		skin_fn = openMayaAnim.MFnSkinCluster(cluster_node)
		dag_path = skin_fn.getPathAtIndex(0)
		components = skin_fn.getComponentAtIndex(0)

		influence_paths = skin_fn.influenceObjects()
		influence_count = len(influence_paths)

		influence_indices = openMaya.MIntArray(range(influence_count))
		weight_list = []
		vert_split_len = len(self.vert_split)

		for vtx_id, split_start in enumerate(self.vert_split):
			if vtx_id < vert_split_len - 1:
				vert_chunk = [0.0] * influence_count
				split_end = self.vert_split[vtx_id + 1]

				for i in range(split_start, split_end):
					inf_idx = self.influence_map[i]
					val = self.weights_non_zero[i]
					vert_chunk[inf_idx] = val
				
				weight_list.extend(vert_chunk)
			
		weight_m_array = openMaya.MDoubleArray(weight_list)
		blend_weights_array = openMaya.MDoubleArray(self.blend_weights.tolist())

		# Apply weights to the skinCluster
		# API 2.0 setWeights signature: (dagPath, components, influenceIndices, weights, normalize=True)
		skin_fn.setWeights(dag_path, components, influence_indices, weight_m_array, False)

		skin_fn.setBlendWeights(dag_path, components, blend_weights_array)

		cmds.setAttr(f'{skin_cluster}.envelope', self.envelope)
		cmds.setAttr(f'{skin_cluster}.skinningMethod', self.skinning_method)
		cmds.setAttr(f'{skin_cluster}.useComponents', self.use_components)
		cmds.setAttr(f'{skin_cluster}.normalizeWeights', self.normalize_weights)
		cmds.setAttr(f'{skin_cluster}.deformUserNormals', self.deform_user_normals)

		cmds.rename(skin_cluster, self.name)
		
	def import_data(self, node=None, dir_path=None, log=False, search_for=None, replace_with=None, prefix=None, name_space=None):
		# if node is None:
		# 	selection = cmds.ls(sl=True)
		# 	if not selection:
		# 		print('🚨 ERROR: Please Select Something 🚨')
		# 		return False
		# 	node = selection[0]

		if dir_path is None:
			start_dir = cmds.workspace(q=True, rootDirectory=True)
			dir_path = cmds.fileDialog2(caption='Load Skinweights', dialogStyle=2, fileMode=1, startingDirectory=start_dir, fileFilter='*.npy', olCaption='Select')

			if not dir_path:
				return False
			dir_path = dir_path[0]

		#folder_path = os.path.join(dir_path, FOLDER_NAME)
		file_name = f'skincluster__{node}.npy'
		file_path = os.path.join(dir_path, file_name)
		
		if not os.path.exists(file_path):
			print(f'🚨 ERROR: SkinCluster for node "{node}" not found on disk at {file_path}')
			return False
		
		skinned = sk.get_skin_cluster_name(node)
		if skinned:
			sk.unbind_skin(obj=node)
		
		# time start
		start_time = time.time()
		data = np.load(file_path, allow_pickle = True)

		if log:
			print(data)

		# time_elapsed = time.time() - start_time
		# print(f'ReadData Elapsed: {time_elapsed}')

		# get item data from numpy array
		legend_array = self.data_io.get_legend_array_from_data(data)
		self.weights_non_zero = self.data_io.get_data_item(data, 'weights_non_zero', legend_array)
		self.influence_map = self.data_io.get_data_item(data, 'influence_map', legend_array)
		self.vert_split = self.data_io.get_data_item(data, 'vert_split', legend_array)
		self.influence_names = self.data_io.get_data_item(data, 'influence_names', legend_array)
		self.blend_weights = self.data_io.get_data_item(data, 'blend_weights', legend_array)
		self.vertex_count = self.data_io.get_data_item(data, 'vertex_count', legend_array)
		self.geometry = self.data_io.get_data_item(data, 'geometry', legend_array)
		self.name = self.data_io.get_data_item(data, 'name', legend_array)
		self.obj_type = self.data_io.get_data_item(data, 'obj_type', legend_array)
		self.is_u_dominant = self.data_io.get_data_item(data, 'is_u_dominant', legend_array)
		self.envelope = self.data_io.get_data_item(data, 'envelope', legend_array)
		self.skinning_method = self.data_io.get_data_item(data, 'skinning_method', legend_array)
		self.use_components = self.data_io.get_data_item(data, 'use_components', legend_array)
		self.normalize_weights = self.data_io.get_data_item(data, 'normalize_weights', legend_array)
		self.deform_user_normals = self.data_io.get_data_item(data, 'deform_user_normals', legend_array)

		#Bind skin
		for i, inf in enumerate(self.influence_names):
			if name_space is not None:
				inf = f'{name_space}:{inf}'
			if search_for is not None:
				inf = inf.replace(search_for, replace_with)
			if prefix is not None:
				inf = f'{prefix}{inf}'
			if not cmds.objExists(inf):
				print(f'⚠️ {inf} does not exist')
				cmds.select(cl=True)
				inf = cmds.joint(n=inf)
			self.influence_names[i] = inf


		new_skin_cluster = f'skinCluster_{node}'
		new_skin_cluster = cmds.skinCluster(self.influence_names.tolist(), node, n=new_skin_cluster, tsb=True)[0]

		time_start = time.time()

		self.set_data(new_skin_cluster)

		# time_elapsed = time.time() - time_start
		# print(f'SetData Elapsed: {time_elapsed}')

		return True

	def compress_weight_data(self, weights_array, influence_count):
		weights_non_zero = []
		influence_counter = 0
		inf_map_chunk = []
		inf_map_chunk_count = 0
		vert_split = [inf_map_chunk_count]
		influence_map = []

		for w in weights_array:
			if w != 0.0:
				weights_non_zero.append(w)
				inf_map_chunk.append(influence_counter)

			influence_counter += 1
			if influence_counter == influence_count:
				influence_counter = 0

				influence_map.extend(inf_map_chunk)
				inf_map_chunk_count = len(inf_map_chunk) + inf_map_chunk_count
				vert_split.append(inf_map_chunk_count)
				inf_map_chunk = []
		
		return weights_non_zero, influence_map, vert_split

class DataIO(object):
	"""
	Utility class for handling data input/output, specifically for numpy structured data.
	"""
	def __init__(self):
		pass

	@staticmethod
	def get_legend_array_from_data(data):
		return data[0]
	
	@staticmethod
	def get_data_item(data, item, legend_array=None):
		if item not in data[0]:
			print(f'ERROR: "{item}" Not Found in Data 🚨')
			return False
		if legend_array is None:
			legend_array = list(data[0])
		return data[legend_array.index(item)]


	def set_data(self, skin_cluster):

		# Selection list to handle API object
		selection_list = openMaya.MGlobal.getSelectionListByName(skin_cluster)

		# Get the MObject for the skinCluster node
		cluster_node = selection_list.getDependNode(0)

		# Function set for the skin cluster
		skin_fn = openMayaAnim.MFnSkinCluster(cluster_node)

		# Get dag path and components
		dag_path = skin_fn.getPathAtIndex(0)
		components = skin_fn.getComponentAtIndex(0)

		# Get influence indices
		influence_paths = skin_fn.influenceObjects()


	
















