import os
import json
import struct
from importlib import reload
import maya.cmds as cmds
from . import rig_utils as util

reload(util)

def define_path(folder_name = 'data' ):
	file_path = cmds.file ( q = True, loc = True  )
	file_path = file_path.split( '/' )
	file_path[-2] = folder_name
	data_path = file_path[:-1] 
	data_path = '\\'.join( data_path )
	if not os.path.isdir( data_path ):
		cmds.sysFile(data_path, makeDir = True)
		print ( 'Data Folder has been created.')
	return data_path

def export_data(file_name = None, data = None, path = None, indent = 4, mode = 'overwrite', log = True):
	'''
	Export data to specific path as 'filename.type'
	:param file_name: output file name, must include file type ("file.type")
	:param mode: export mode (overwrite, append)
	'''
	full_path = os.path.join(path, file_name)
	try:

		if mode == 'overwrite':
			with open(full_path, 'w') as file:
				json.dump(data, file, indent = indent)
			if log:
				print(f"{file_name} exported: {path}")

		elif mode == 'append':
			with open(full_path) as existed_file:
				append_file = json.load(existed_file)
			append_file.update(data)
			with open(full_path, 'w') as file:
				json.dump(append_file, file, indent = indent)

	except Exception as e:
		print(f"An error occurred: {e}")

def import_data(file_name=None, folder_name=None, path=None):
	if path:
		path = path
	else:
		path = define_path(folder_name)
	full_path = os.path.join(path, file_name)
	try:
		with open(full_path, 'r', encoding='utf-8') as file:
			imported_data = json.load(file)
		return imported_data
	except FileNotFoundError:
		print("The file was not found.")
	except json.JSONDecodeError:
		print("Error decoding JSON. Check for invalid syntax.")

def export_binary_data(file_path, influence_names, weights, obj_type_int):#26Jan15
	'''	
		Saves skin weights in a flat binary format.
		Format: [Header: InfCount(i), VertCount(i)] -> [Names] -> [Weights(f...)]
	'''
	inf_string = ",".join(influence_names).encode('utf-8')
	inf_string_len = len(inf_string)

	with open(file_path, 'wb') as file:
		# Header: Type(i), InfCount(i), NameStrLen(i)
		file.write(struct.pack('iii', obj_type_int,  len(influence_names), inf_string_len))

		file.write(inf_string)

		# Write all weights as a flat list of floats ('f')
		# use '*' to unpack the list into the pack functio
		fmt = f'{len(weights)}f'
		file.write(struct.pack(fmt, *weights))

def import_binary_data(file_path):
	with open(file_path, 'rb') as file:
		header = file.read(12) # 3 integers = 12 bytes
		obj_type_int, num_inf, inf_string_len = struct.unpack('iii', header)
		inf_names = file.read(inf_string_len).decode('utf-8').split(',')

		# Read Weights
		weight_bytes = file.read()
		num_weights = len(weight_bytes) // 4 # 4 bytes per float
		weights = struct.unpack(f'{num_weights}f', weight_bytes)
	
	return obj_type_int, inf_names, weights






