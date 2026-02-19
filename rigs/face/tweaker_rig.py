from importlib import reload
import maya.cmds as cmds
from .base import FaceModule
from . import face_config
from ...core.utils import rig_utils as bb
reload(bb)

class TweakerRig(FaceModule):
	def __init__(self, 
				blueprint_grp = None, 
				default_shape='crossCircle',
				add_jnts = None,
				name = 'face',
				side='M',
				parent_ctrl_grp=None,
				parent_mod_grp=None,
				remove_elem='bp'
				):
		super().__init__(name, side, parent_ctrl_grp, parent_mod_grp, remove_elem)
		self.blueprint_grp =  blueprint_grp
		self.default_shape =  default_shape
		self.add_jnts =  add_jnts

	
	def build(self):
		face_mod = self.build_hierarchy()		
		bp_jnts = cmds.listRelatives(self.blueprint_grp, ad=True)

		template_jnts = face_config.BASIC_BONES
		default_config = face_config.DEFAULT_SETTINGS

		created_jnts = []
		ctrls = []
		grps = []
		both_parent = []

		for jnt in bp_jnts:
			if jnt in template_jnts:
				shape = template_jnts[jnt]['shape']
				scale = template_jnts[jnt]['scale']
				rotate = template_jnts[jnt]['rotate']
				move = template_jnts[jnt]['move']
				parent = template_jnts[jnt]['parent']
			else:
				shape = default_config['shape']
				scale = default_config['scale']
				rotate = default_config['rotate']
				move = default_config['move']
				parent = cmds.listRelatives(jnt, p=True)[0]

			rig_jnt_grp, rig_jnt = self.create_rig_joint(jnt, parent_jnt_grp=self.jnt_grp, rad=0.5)
			rig_ctrl_grp, rig_ctrl = self.create_controller(jnt, shape, scale, rotate, move, 'direct')
			
			if parent == 'both':
				both_parent.append([rig_ctrl_grp, rig_ctrl])

			created_jnts.append(jnt)
			ctrls.append(rig_ctrl)
			grps.append(rig_ctrl_grp)
		
		# Heirarchy organize
		for jnt in created_jnts:
			jnt_idx = created_jnts.index(jnt)
			parent = cmds.listRelatives(jnt, p=True)[0]
			if parent in created_jnts:
				parent_idx = created_jnts.index(parent)
				cmds.parent(grps[jnt_idx], ctrls[parent_idx])

		for items in both_parent:
			rig_grp = items[0]
			rig_ctrl = items[1]
			follow_dic = bb.create_offset_group(rig_ctrl, ['follow'])
			follow_grp = follow_dic[rig_ctrl]
			bb.add_follow_attr(parents = [], target = '', attr_name = 'follow', ctrl = '', min=0, max=1, dv=0.5, multiply=False, connect_type = 'parent')
