#cmds.file("W:/RIG/PROJ/MAYA_PROJ/JINXIE/scenes/RIG_JINXIE_finger.ma", o=True, f=True )
from importlib import reload
import maya.cmds as cmds
import os
from pprint import pprint
import maya.cmds as cmds
from ..core.utils import rig_utils as bb
from ..core.utils import io_utils as io
from ..core.controllers import creator as bc
from ..core.controllers import shape_color
from ..core.naming import namer_factory as naming
from ..core.naming import current_project
from ..core.naming import parser
from . import fk_rig as fk
from . import ik_rig as ik
from . import fkIk_rig as fkIk

reload(bb)
reload(io)
reload(bc)
reload(fk)
reload(ik)
reload(fkIk)


FK_CTRL_SHAPE = 'crossCircle'
FK_BASE_CTRL_SHAPE = 'miniRectangle'
IK_CTRL_SHAPE = 'cube'
IK_PV_CTRL_SHAPE = 'diamond'
IK_END_CTRL_SHAPE = 'cube'

POSE_FOLDER = 'data'
POSE_FILE = 'fingers.pose'

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

# Finger pose dictionary json generator
def finger_pose_data(
		pose = 'fist',
		finger_ctrls = ['l_pinky_tmp_01_ctl', 'l_ring_tmp_04_ctl', 'l_index_tmp_02_ctl', 'l_ring_tmp_01_ctl', 'l_index_tmp_03_ctl', 'l_middle_tmp_03_ctl', 'l_pinky_tmp_02_ctl', 'l_thumb_tmp_01_ctl', 'l_pinky_tmp_03_ctl', 'l_middle_tmp_04_ctl', 'l_middle_tmp_01_ctl', 'l_thumb_tmp_03_ctl', 'l_index_tmp_01_ctl', 'l_middle_tmp_02_ctl', 'l_pinky_tmp_04_ctl', 'l_thumb_tmp_02_ctl', 'l_ring_tmp_02_ctl', 'l_index_tmp_04_ctl', 'l_ring_tmp_03_ctl'],
		log = False,
		export = True
	): #26Jan04

	hand_poses_dict = None
	pose_dict = {}
	for ctrl in finger_ctrls:
		pose_dict[ctrl] = []
		for move in ['t', 'r']:
			for ax in 'xyz':
				posi_value = cmds.getAttr(f'{ctrl}.{move}{ax}')
				if posi_value != 0:
					pose_dict[ctrl].append([[f'{move}{ax}'], [posi_value]])
		if len(pose_dict[ctrl]) == 0:
			pose_dict.pop(ctrl)
			
	hand_poses_dict = {pose:pose_dict}
	if log:
		pprint(hand_poses_dict)
	if export:
		try:
			path = io.define_path(POSE_FOLDER)
			full_path = os.path.join(path, POSE_FILE)
			if not os.path.isdir( full_path ):
				writing_mode = 'overwrite'
			else:
				writing_mode = 'append'
			io.export_data(file_name = POSE_FILE, path = path, data = hand_poses_dict, indent = 1, mode = writing_mode)

		except Exception as e:
			print(f"An error occurred: {e}")

	return hand_poses_dict

class FingerRig:
	def __init__(self,
				joint_list = None,
				finger_names = [],
				pv_jnt_list = None, 
				setting_obj = None,
				rig_name = None,
				side = None,
				aim_axis = 'x',
				up_axis = 'z',
				rotate_order = 'xyz',
				connection_type = 'parent',
				scale = 1,
				feature = 'fk',
				stretch = True,
				squash = True,
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				global_scale = '',
				base_orient_loc = '',
				end_orient_loc = '',
				world_space = None,
				ctrl_parent =None,
				mod_parent = None,
				bind_parent ='',
				upper_driver = '',
				color = None,
				default_fkIk = 1,
				default_ik_base = 0,
				default_ik_pv = 1,
				default_ik_end = 1,
				finger_pose = False,
				pose_ctrl = None,
				log=False,
				**controller_kwargs
				):
		
		self.joint_list =  joint_list
		self.finger_names = finger_names
		self.pv_jnt_list =  pv_jnt_list
		self.setting_obj =  setting_obj
		self.rig_name =  rig_name
		self.aim_axis =  aim_axis
		self.up_axis =  up_axis
		self.rotate_order =  rotate_order
		self.connection_type =  connection_type
		self.scale =  scale
		self.feature =  feature
		self.stretch =  stretch
		self.squash =  squash
		self.stretch_attr =  stretch_attr
		self.squash_attr =  squash_attr
		self.global_scale =  global_scale
		self.base_orient_loc =  base_orient_loc
		self.end_orient_loc =  end_orient_loc
		self.world_space =  world_space
		self.ctrl_parent =  ctrl_parent
		self.mod_parent =  mod_parent
		self.bind_parent =  bind_parent
		self.upper_driver =  upper_driver
		self.default_fkIk =  default_fkIk
		self.default_ik_base =  default_ik_base
		self.default_ik_pv =  default_ik_pv
		self.default_ik_end =  default_ik_end
		self.finger_pose =  finger_pose
		self.pose_ctrl =  pose_ctrl
		self.controller_kwargs =  controller_kwargs

		if self.finger_names is None:
			self.finger_names = []
			for finger in self.joint_list:
				base_name = parser.get_base_name(finger[0], base_number=False)
				self.finger_names.append(base_name)
	
		if side is None :
			self.side = parser.find_element(self.joint_list[0][0], 'sides')
		else:
			self.side =  side

		if color is None:
			formatted_side = parser.format_side(self.side, 'upper')
			color = shape_color.CTRL_COLOR.get(formatted_side, 'yellow')
			self.color = color
		else: 
			self.color =  color 

		self.up_vector = bb.axis_convert(up_axis, 'vector')
		default_shape_rotation = [item * 90 for item in self.up_vector]
		self.shape_rotation = controller_kwargs.get('shape_rotation', default_shape_rotation)
		
		self.ctrl_grp = None
		self.mod_grp = None
		self.bind_jnts = None
		self.ctrl_dict = {}

		self._build()
		if log:
			bb.over_and_out('FingerRig', f'{self.side}{self.rig_name}')

	def _setup_finger_poses(self, pose_ctrl, filter_name=None):
		if not self.finger_pose:
			return

		path = io.define_path(POSE_FOLDER)
		pose_dict = io.import_data(POSE_FILE, folder_name = POSE_FOLDER, path = path)

		for pose in pose_dict:
			if not cmds.attributeQuery(pose, node=pose_ctrl, exists=True):
				cmds.addAttr(pose_ctrl, ln=pose, at='double', min=-10, max=10, dv=0, k=True)

			for ctrl in pose_dict[pose]:
				# If filter_name is provided, skip controls that don't belong to this finger
				if filter_name and filter_name not in ctrl:
					continue
				
				# Create SDK offset group
				sdk_grp_dict = bb.create_offset_group(ctrl, [f'{pose}_sdk'])
				sdk_grp = sdk_grp_dict[ctrl][0]
				bb.set_color(objects=[sdk_grp], color='lightPink', viewport=False, outliner=True)
				
				# Setup driven keys for each attribute in the pose data
				for attr_data in pose_dict[pose][ctrl]:
					sdk_attr = attr_data[0][0]
					sdk_val = attr_data[1][0]
					
					driven = f'{sdk_grp}.{sdk_attr}'
					# Set driven keys: 0 is default, 10 is full pose, -5 is reverse half
					bb.set_driven_key(
						main_ctrl=pose_ctrl, 
						attr=pose, 
						driven=driven, 
						values={0: 0, 10: sdk_val, -5: sdk_val * (-0.5)}
					)
					# Reset to default
					cmds.setAttr(driven, 0)

	def _build(self):
		if self.feature == 'fk':
			for i, finger in enumerate(self.joint_list):
				generated_joints = bb.duplicate_joint_chain(finger, add_elements=['fk'], remove_element='tmp')
				fk_jnts = generated_joints['fk']
				finger_fk = fk.FKRig(
						joints=fk_jnts,
						rig_name=self.finger_names[i],
						element_name='fk',
						side=None,
						stretch=self.stretch,
						squash=self.squash,
						aim_axis=self.aim_axis,
						up_axis = self.up_axis,
						shape=FK_CTRL_SHAPE,
						color=self.color,
						connection_type=self.connection_type,
						stretch_attr = self.stretch_attr,
						squash_attr = self.squash_attr,
						rig_end_joint = False,
						shape_rotation = [0, 0, 90],
						upper_driver = self.upper_driver
						)
				self.ctrl_dict[self.finger_names[i]] = finger_fk.ctrls
				self._setup_finger_poses(finger_fk.ctrls[0], filter_name=self.finger_names[i])
		# IF NOT FK
		else:
			self.ctrl_grp = bb.create_node('group', self.rig_name, ['ctrl'], None, self.side)
			self.mod_grp = bb.create_node('group', self.rig_name, ['mod'], None, self.side)
			if self.ctrl_parent:
				cmds.parent(self.ctrl_grp, self.ctrl_parent)
			if self.mod_parent:
				cmds.parent(self.mod_grp, self.mod_parent)
			if self.global_scale:
				scale_obj = self.global_scale.split('.')[0]
				bb.snap([scale_obj], self.ctrl_grp)
			if self.upper_driver:
				bb.create_constraint([self.upper_driver], self.mod_grp, 'parentScale')
				bb.create_constraint([self.upper_driver], self.ctrl_grp, 'parentScale')

			if self.feature == 'ik':
				upper_driver_scale = self.upper_driver + '.sx'
				for i, finger in enumerate(self.joint_list):	
					generated_joints = bb.duplicate_joint_chain(finger, add_elements=['ik'], remove_element='tmp')
					ik_jnts = generated_joints['ik']

					base_rig = bc.SingleControl(target_obj=ik_jnts[0], 
												#upper_driver=self.upper_driver,
												bind_parent=self.bind_parent, 
												ctrl_parent=self.ctrl_parent, 
												scale = self.scale * 4, 
												color = self.color, 
												shape = FK_BASE_CTRL_SHAPE,
												connection_type = 'matrix_parent',
												shape_rotation = [90, 90, 0],
												global_scale = self.global_scale,
												create_joint = True,
												add_element = 'bnd')
					
					ik_rig = ik.IkRig( joints = ik_jnts[1:],
								pole_vector_jnt = self.pv_jnt_list[i],
								rig_name = self.finger_names[i],
								element_name = 'ik',
								stretch = self.stretch,
								squash = self.squash,
								aim_axis = self.aim_axis,
								up_axis = self.up_axis,
								ctrl_shape = IK_CTRL_SHAPE,
								ctrl_color = self.color,
								connection_type = self.connection_type,
								scale = self.scale,
								stretch_attr = self.stretch_attr,
								squash_attr = self.squash_attr,
								global_scale = upper_driver_scale,
								base_orient_loc = self.base_orient_loc,
								end_orient_loc = self.end_orient_loc,
								world_space = self.world_space,
								ctrl_parent = base_rig.ctrl,
								mod_parent = self.mod_grp,
								upper_driver = base_rig.ctrl,
								default_ik_base = self.default_ik_base,
								default_ik_pv = self.default_ik_pv,
								default_ik_end = self.default_ik_end,
								)
					self.ctrl_dict[self.finger_names[i]] = [base_rig.ctrl] +[ ik_rig.ctrls]
					cmds.parent(base_rig.ctrl, self.ctrl_grp)
					self._setup_finger_poses(base_rig.ctrl, filter_name=self.finger_names[i])
				
			elif self.feature == 'fkIk':
				upper_driver_scale = self.upper_driver + '.sx'
				for i, finger in enumerate(self.joint_list):
					base_rig = bc.SingleControl(target_obj=finger[0], 
									#upper_driver = self.upper_driver,
									bind_parent=self.bind_parent, 
									ctrl_parent=self.ctrl_parent, 
									connection_type = 'matrix_parent',
									scale = self.scale * 4, 
									color = self.color, 
									shape = FK_BASE_CTRL_SHAPE,
									shape_rotation = [90, 90, 0],
									global_scale = self.global_scale,
									create_joint = True,
									add_element = 'bnd')

					fkIk_rig_jnts = finger[1:]
					finger_rig = fkIk.FkIkRig(joints = fkIk_rig_jnts,
						pole_vector_jnt = self.pv_jnt_list[i], 
						setting_obj = self.setting_obj,
						rig_name = self.finger_names[i],
						side = self.side,
						stretch = self.stretch,
						squash = self.squash,
						aim_axis = self.aim_axis,
						up_axis = self.up_axis,
						rotate_order = self.rotate_order,
						connection_type = self.connection_type,
						scale = self.scale,
						color = self.color,
						stretch_attr = self.stretch_attr,
						squash_attr = self.squash_attr,
						global_scale = upper_driver_scale,
						base_orient_loc = self.base_orient_loc,
						end_orient_loc = self.end_orient_loc,
						world_space = self.world_space,
						ctrl_parent = base_rig.ctrl,
						mod_parent = self.mod_grp,
						bind_parent = base_rig.bind_jnt,
						upper_driver = base_rig.ctrl,
						default_fkIk = self.default_fkIk,
						default_ik_base = self.default_ik_base,
						default_ik_pv = self.default_ik_pv,
						default_ik_end = self.default_ik_end,
						create_bind_joint = True,
						rig_end_joint=False,
						base_parent_type = 'parent')
					self.ctrl_dict[self.finger_names[i]] = [base_rig.ctrl] + [finger_rig.ctrl_dict]
					cmds.parent(base_rig.offset_grps[0], self.ctrl_grp)
				self._setup_finger_poses(self.pose_ctrl)
				
			else:
				cmds.error(f'Incorrect @feature: {self.feature}. Support feature: "fk", "ik", "fkIk"')




# from bbTools.core import bbFingerRig as finger
# reload(finger)
# fngr_dict = finger.finger_pose_data(
# 					pose = 'fist',
# 					finger_ctrls = ['l_thumb_03_fk_ctl', 'l_ring_02_fk_ctl', 'l_pinky_03_fk_ctl', 'l_ring_tmp_01_01_ctl', 'l_pinky_04_fk_ctl', 'l_middle_04_fk_ctl', 'l_index_04_fk_ctl', 'l_pinky_tmp_01_01_ctl', 'l_middle_tmp_01_01_ctl', 'l_thumb_tmp_01_01_ctl', 'l_pinky_02_fk_ctl', 'l_middle_02_fk_ctl', 'l_middle_03_fk_ctl', 'l_index_03_fk_ctl', 'l_ring_04_fk_ctl', 'l_ring_03_fk_ctl', 'l_index_tmp_01_01_ctl', 'l_index_02_fk_ctl', 'l_thumb_02_fk_ctl'],
# 					log = False,
# 					export = True
# 				)


# l_finger_rig = finger.FingerRig(
# 						joint_list = [['l_thumb_01_tmp_jnt', 'l_thumb_02_tmp_jnt', 'l_thumb_03_tmp_jnt', 'l_thumb_04_tmp_jnt'],
# 					['l_index_01_tmp_jnt', 'l_index_02_tmp_jnt', 'l_index_03_tmp_jnt', 'l_index_04_tmp_jnt', 'l_index_05_tmp_jnt'],
# 					['l_middle_01_tmp_jnt', 'l_middle_02_tmp_jnt', 'l_middle_03_tmp_jnt', 'l_middle_04_tmp_jnt', 'l_middle_05_tmp_jnt'],
# 					['l_ring_01_tmp_jnt', 'l_ring_02_tmp_jnt', 'l_ring_03_tmp_jnt', 'l_ring_04_tmp_jnt', 'l_ring_05_tmp_jnt'], 
# 					['l_pinky_01_tmp_jnt', 'l_pinky_02_tmp_jnt', 'l_pinky_03_tmp_jnt', 'l_pinky_04_tmp_jnt', 'l_pinky_05_tmp_jnt']
# 					],
# 						finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky'],
# 						pv_jnt_list = ['l_thumb_pv_tmp_jnt', 'l_index_pv_tmp_jnt', 'l_middle_pv_tmp_jnt','l_ring_pv_tmp_jnt', 'l_pinky_pv_tmp_jnt'], 
# 						setting_obj = None,
# 						rig_name = 'finger',
# 						side = None,
# 						aim_axis = 'x',
# 						up_axis = 'z',
# 						rotate_order = 'xyz',
# 						connection_type = 'parent',
# 						scale = 0.2,
# 						feature = 'fkIk',
# 						stretch = True,
# 						squash = True,
# 						stretch_attr = 'stretch',
# 						squash_attr = 'squash',
# 						global_scale = super_rig.scale_uniform,
# 						base_orient_loc = None,
# 						end_orient_loc = None,
# 						world_space = super_rig.placement_ctrl,
# 						ctrl_parent = super_rig.ctrl_grp,
# 						mod_parent = super_rig.mod_grp,
# 						bind_parent = l_arm_rig.bind_jnts[-1],
# 						upper_driver = l_arm_rig.bind_jnts[-1],
# 						color = 'sky',
# 						default_fkIk = 0,
# 						default_ik_base = 1,
# 						default_ik_end = 1,
# 						finger_pose = False
# 						)


































