import os
import json
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

def export_data(file_name = None, data = None, path = None, indent = 4, mode = 'overwrite'):
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

