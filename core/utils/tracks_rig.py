import maya.cmds as cmds
from bbTools.core.utils import rig_utils as bb
from bbTools.core.naming import namer_factory as naming
from bbTools.core.naming import current_project
from bbTools.core.naming import parser
from bbTools.core.naming import templates

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

AUTO_SPIN_ATTR = 'autoSpin'
OFFSET_ATTR = 'offset'
SPEED_ATTR = 'speed'

class TracksRig:
	def __init__(self, 
				base='track',
				side='l',
				first_jnt=None,
				main_ctrl=None,
				ik_crv=None,
				aim_axis='z',
				up_axis='x'				
				):

		self.base = base
		self.side = side
		self.aim_axis = aim_axis
		self.up_axis = up_axis

		# Required Scene Objects
		self.first_jnt = first_jnt 
		self.main_ctrl = main_ctrl
		self.ik_crv = ik_crv

		# Constants
		self.auto_spin_attr = AUTO_SPIN_ATTR
		self.offset_attr = OFFSET_ATTR
		self.speed_attr = SPEED_ATTR
		
		self.mod_grp = None
		self.ikh = None
		self.joints = None

		self.nodes = {}

	def build(self):
		number = parser.find_number(self.base, base_number=True)
		if number:
			self.base = self.base.replace(number, '')

		self.mod_grp = bb.create_node('group', self.base, ['mod'], number, self.side)

		jnt_list = cmds.listRelatives( self.first_jnt ,  type = 'joint', allDescendents = True )
		jnt_list.append(self.first_jnt)
		jnt_list.reverse()
		cmds.parent(jnt_list[0], self.mod_grp)

		if not self.ik_crv:
			pos_list = []
			for jnt in jnt_list:
				pos = cmds.xform(jnt, q=True, t=True, ws=True)
				pos_list.append(pos)
			self.ik_crv = cmds.curve(p=pos_list, d=1)
			crv_name = NAMER.format(self.base, ['Spline'], number, self.side, templates.TYPE_SUFFIX['nurbsCurve'])
			self.ik_crv = cmds.rename(self.ik_crv, crv_name)

		ik_name = NAMER.format(self.base, ['ik'], number, self.side, '')
		ikh_name = NAMER.format(self.base, ['Spline'], number, self.side, templates.TYPE_SUFFIX['ikHandle'])
		eff_name = NAMER.format(self.base, ['Spline'], number, self.side, templates.TYPE_SUFFIX['ikEffector'])

		ikh, eff = cmds.ikHandle(sj=jnt_list[0], ee=jnt_list[-1], ccv=False, scv=False, sol='ikSplineSolver', pcv=False, c=self.ik_crv)
		ikh = cmds.rename(ikh, ikh_name)
		eff = cmds.rename(eff, eff_name)
		bb.create_constrain([self.main_ctrl], self.ik_crv, 'pac')
		cmds.parent([ikh, self.ik_crv], self.mod_grp)

		# Ik Advance Twist
		up_ab_axis = bb.axis_convert(self.up_axis, 'absolute_letter')
		fwd_axis_idx = bb.axis_convert(self.aim_axis, 'ik_twist_index')
		up_axis_idx = bb.axis_convert(self.up_axis, 'ik_twist_up_index')
		up_axis_value = -1 if '-' in self.up_axis else 1
		cmds.setAttr( f'{ikh}.dTwistControlEnable', 1)
		cmds.setAttr( f'{ikh}.dWorldUpType', 4)
		cmds.setAttr( f'{ikh}.dForwardAxis', fwd_axis_idx)
		cmds.setAttr( f'{ikh}.dWorldUpAxis', up_axis_idx)
		cmds.setAttr( f'{ikh}.dWorldUpVector{up_ab_axis.upper()}', up_axis_value)
		cmds.setAttr( f'{ikh}.dWorldUpVectorEnd{up_ab_axis.upper()}', up_axis_value)

		# Finding Circumference
		ik_crv_shp = cmds.listRelatives(self.ik_crv, s=True)[0]
		ik_crv_cif = bb.create_node('curveInfo', self.base, ['iksp'], number, self.side)
		cmds.connectAttr(f'{ik_crv_shp}.worldSpace[0]', f'{ik_crv_cif}.inputCurve')

		# calculate percentage of the moved distance to 1 full loop (max offset value in .i1x = 1)
		perc_mdv = bb.create_node('multiplyDivide', self.base, ['perc'], number, self.side)
		cmds.setAttr(f'{perc_mdv}.op', 2 )
		cmds.setAttr( f'{perc_mdv}.i1x', 1)
		cmds.connectAttr(f'{ik_crv_cif}.arcLength', f'{perc_mdv}.i2x')

		start_loc = bb.create_node('locator', self.base, ['start'], number, self.side)
		move_loc = bb.create_node('locator', self.base, ['move'], number, self.side)
		cmds.parent([start_loc, move_loc], self.mod_grp)

		main_ctrl_pos = cmds.xform(self.main_ctrl, q=True, t=True, ws=True)
		cmds.xform(start_loc, t=[main_ctrl_pos[0], 0, main_ctrl_pos[2]], ws=True)
		cmds.xform(move_loc, t=[main_ctrl_pos[0], 0, main_ctrl_pos[2]], ws=True)
		bb.create_constrain([self.main_ctrl], move_loc, 'parent', maintain_offset=True)

		start_loc_shp = cmds.listRelatives(start_loc, s=True)[0]
		move_loc_shp = cmds.listRelatives(move_loc, s=True)[0]
		distance_ddm = bb.create_node('distanceDimShape', self.base, ['dist'], number, self.side)
		distance_ddm_shp = cmds.listRelatives(distance_ddm, s=True)[0]
		cmds.connectAttr(f'{start_loc_shp}.worldPosition[0]', f'{distance_ddm}.startPoint')
		cmds.connectAttr(f'{move_loc_shp}.worldPosition[0]', f'{distance_ddm}.endPoint')
		cmds.parent(distance_ddm, self.mod_grp)

		mul_dis_mdl = bb.create_node('multDoubleLinear', self.base, ['mul', 'dis'], number, self.side)
		cmds.connectAttr(f'{perc_mdv}.ox', f'{mul_dis_mdl}.i1')
		cmds.connectAttr(f'{distance_ddm}.distance', f'{mul_dis_mdl}.i2')

		start_loc_dcm = bb.create_node('decomposeMatrix', self.base, ['start'], number, self.side)
		move_loc_dcm = bb.create_node('decomposeMatrix', self.base, ['move'], number, self.side)
		cmds.connectAttr(f'{start_loc}.matrix', f'{start_loc_dcm}.inputMatrix')
		cmds.connectAttr(f'{move_loc}.matrix', f'{move_loc_dcm}.inputMatrix')

		fwd_dir_pma = bb.create_node('plusMinusAverage', self.base, ['fwd', 'dir'], number, self.side)
		cmds.setAttr(f'{fwd_dir_pma}.op', 2 )
		cmds.connectAttr(f'{move_loc_dcm}.outputTranslateZ', f'{fwd_dir_pma}.input1D[0]')
		cmds.connectAttr(f'{start_loc_dcm}.outputTranslateZ', f'{fwd_dir_pma}.input1D[1]')

		dir_cdt = bb.create_node('condition', self.base, ['dir'], number, self.side)
		cmds.setAttr(f'{dir_cdt}.op', 2 )
		cmds.setAttr( f'{dir_cdt}.st', 0)
		cmds.setAttr( f'{dir_cdt}.ctr', 1)
		cmds.setAttr( f'{dir_cdt}.cfr', -1)
		cmds.connectAttr(f'{fwd_dir_pma}.output1D', f'{dir_cdt}.ft')

		dir_mul_mdl = bb.create_node('multDoubleLinear', self.base, ['dir', 'mul'], number, self.side)
		cmds.connectAttr(f'{mul_dis_mdl}.o', f'{dir_mul_mdl}.i1')
		cmds.connectAttr(f'{dir_cdt}.ocr', f'{dir_mul_mdl}.i2')

		only_fwd_cdt = bb.create_node('condition', self.base, ['fwd', 'dir'], number, self.side)
		cmds.setAttr(f'{only_fwd_cdt}.op', 1 )
		cmds.setAttr( f'{only_fwd_cdt}.st', 0)
		cmds.setAttr( f'{only_fwd_cdt}.cfr', 0)
		cmds.connectAttr(f'{dir_mul_mdl}.o', f'{only_fwd_cdt}.ctr')
		cmds.connectAttr(f'{fwd_dir_pma}.output1D', f'{only_fwd_cdt}.ft')

		# Extra Attribute
		bb.attr_separator(self.main_ctrl)
		cmds.addAttr( self.main_ctrl, ln = AUTO_SPIN_ATTR, at = 'enum', en = 'OFF:ON' , k = True )
		cmds.addAttr( self.main_ctrl, ln = SPEED_ATTR, at = 'float', dv = 1, k = True )
		cmds.addAttr( self.main_ctrl, ln = OFFSET_ATTR, at = 'float', dv = 0, k = True )
		cmds.setAttr( f'{self.main_ctrl}.{AUTO_SPIN_ATTR}', 1)

		# Speed Attribute
		speed_mdl = bb.create_node('multDoubleLinear', self.base, [SPEED_ATTR], number, self.side)
		cmds.connectAttr(f'{self.main_ctrl}.{SPEED_ATTR}', f'{speed_mdl}.i1')
		cmds.connectAttr(f'{only_fwd_cdt}.ocr', f'{speed_mdl}.i2')

		# Offset Attribute
		offset_adl = bb.create_node('addDoubleLinear', self.base, [OFFSET_ATTR], number, self.side)
		cmds.connectAttr(f'{self.main_ctrl}.{OFFSET_ATTR}', f'{offset_adl}.i1')
		cmds.connectAttr(f'{speed_mdl}.o', f'{offset_adl}.i2')

		# AutoSpin Switch
		switch_mdl = bb.create_node('multDoubleLinear', self.base, [AUTO_SPIN_ATTR], number, self.side)	
		cmds.connectAttr(f'{self.main_ctrl}.{AUTO_SPIN_ATTR}', f'{switch_mdl}.i1')
		cmds.connectAttr(f'{offset_adl}.o', f'{switch_mdl}.i2')

		# Set Driven Key
		driver = f'{switch_mdl}.o'
		driven = f'{ikh}.offset'
		cmds.setDrivenKeyframe(driven, cd=driver, itt = 'linear', ott = 'linear', dv=0, v=0 )
		cmds.setDrivenKeyframe(driven, cd=driver, itt = 'linear', ott = 'linear', dv=1, v=1 )
		key = cmds.listConnections(driven, type='animCurve')[0]
		cmds.setAttr( f'{key}.preInfinity', 3)
		cmds.setAttr( f'{key}.postInfinity', 3)

	def create_joints(self, geo_grp = 'tracksGeoLFT_grp', pivot_vtx = [[7212], [8089]]):
		transforms = cmds.listRelatives(geo_grp, c=True, type='transform')
		meshes = []

		for obj in transforms:
			shape = cmds.listRelatives(obj, s=True)
			if shape and cmds.objectType(shape[0], i='mesh'):
				meshes.append(obj)
		aim_vec = bb.axis_convert(self.aim_axis, 'vector')
		up_vec = bb.axis_convert(self.up_axis, 'vector')
		jnts = []		
		for mesh in meshes:
			base, element, number, side, suffix = NAMER.extract(mesh)
			base = parser.get_base_name(base, base_number=False)
			pv_cpn = [f'{mesh}.vtx{pivot_vtx[0]}', f'{mesh}.vtx{pivot_vtx[1]}']
			pv_pos = bb.get_center_position(pv_cpn)
			jnt = bb.create_node('joint', base, element, number, side)
			cmds.xform(jnt, t=[pv_pos[0], pv_pos[1], pv_pos[2]], ws=True)
			if len(jnts) > 0:
				cmds.delete(cmds.aimConstraint(jnts[-1], jnt, aimVector= aim_vec, upVector=up_vec, worldUpType="vector", worldUpVector = up_vec ))
				cmds.parent(jnt, jnts[-1])
			jnts.append(jnt)
			
		cmds.select(jnts)
		return jnts






# from bbTools.core.utils import tracks_rig as tr
# reload(tr)

# l_tracks = tr.TracksRig(
# 				base='track',
# 				side='l',
# 				first_jnt='jnt_l_tracks001',
# 				main_ctrl='trackLFT_ctrl',
# 				ik_crv='track_iksp_crv',
# 				aim_axis='z',
# 				up_axis='x'				
# 				) 
# l_tracks.build()

# jnts = l_tracks.create_joints(geo_grp = 'tracksGeoRGT_grp', pivot_vtx = [[7212], [8089]])








