import maya.cmds as cmds
from bbTools.core.utils import rig_utils as bb
from bbTools.core.utils import skin_utils as sk
from bbTools.core.controllers import creator as bc
from bbTools.core.controllers import shape_color
from bbTools.core.naming import namer_factory as naming
from bbTools.core.naming import current_project
from bbTools.core.naming import parser
from bbTools.core.naming import templates

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

AUTO_SPIN_TYPE_ATTR = 'autoSpinType'
AUTO_TYPE_ENUM = 'OFF:distance:time'
SPEED_ATTR = 'speed'
OFFSET_ATTR = 'offset'

class TracksRig:
	def __init__(self, 
				base='track',
				side='l',
				main_ctrl=None,
				aim_axis='z',
				up_axis='x',
				tweakers = None,	
				geo_grp = None, 
				engine_grp = None,
				pivot_vtx = None,
				scale = 1
				):

		self.base = base
		self.side = side
		self.aim_axis = aim_axis
		self.up_axis = up_axis
		self.tweakers = tweakers
		self.scale =  scale

		# Required Scene Objects
		self.main_ctrl = main_ctrl
		self.geo_grp =  geo_grp
		self.engine_grp =  engine_grp
		self.pivot_vtx =  pivot_vtx
		self.time_node = 'time1'
		
		self.mod_grp = None
		self.ikh = None
		self.joints = None
		self.meshes = None
		self.ik_crv = None

		self.nodes = {}

		self.number = parser.find_number(self.base, base_number=True)
		if self.number:
			self.base = self.base.replace(self.number, '')

	def build(self):

		self.mod_grp = bb.create_node('group', self.base, ['mod'], self.number, self.side)
		self.jnt_list = self.create_joints()
		cmds.parent(self.jnt_list[0], self.mod_grp)
		cmds.hide([self.jnt_list[0], self.mod_grp])
		self.constrain_mesh()

		ikh_name = NAMER.format(self.base, ['Spline'], self.number, self.side, templates.TYPE_SUFFIX['ikHandle'])
		eff_name = NAMER.format(self.base, ['Spline'], self.number, self.side, templates.TYPE_SUFFIX['ikEffector'])
		crv_name = NAMER.format(self.base, ['Spline'], self.number, self.side, templates.TYPE_SUFFIX['nurbsCurve'])

		# Create curve from default ik spline cmd
		ikh, eff, ik_crv = cmds.ikHandle(sj=self.jnt_list[0], ee=self.jnt_list[-1], ccv=True, scv=False, sol='ikSplineSolver', pcv=False)
		ik_crv = cmds.rename(ik_crv, crv_name)
		_, span, _ = bb.get_curve_info(ik_crv)

		# Rebuild to max 1
		cmds.closeCurve(ik_crv,rpo=True, ch=False, ps=True, bb=0.5, bki=0, p=0.1)
		ik_crv = cmds.rebuildCurve(ik_crv, ch=False, rpo=True, rt=False, end=True, kr=False, kcp=True, kep=True, kt=True, s = span, d=3, tol=0.01)[0]
		cmds.delete(ikh, eff)

		# Create ik handle with the curve from above
		ikh, eff = cmds.ikHandle(sj=self.jnt_list[0], ee=self.jnt_list[-1], c=ik_crv, ccv=False, scv=False, sol='ikSplineSolver', pcv=False)
		ikh = cmds.rename(ikh, ikh_name)
		eff = cmds.rename(eff, eff_name)
		self.ik_crv = cmds.rename(ik_crv, crv_name)

		# Ik Advance Twist
		up_ab_axis = bb.axis_convert(self.up_axis, 'absolute_letter')
		other_axes = 'XYZ'.replace(up_ab_axis.upper(), '')
		fwd_axis_idx = bb.axis_convert(self.aim_axis, 'ik_twist_index')
		up_axis_idx = bb.axis_convert(self.up_axis, 'ik_twist_up_index')
		up_axis_value = -1 if '-' in self.up_axis else 1
		cmds.setAttr( f'{ikh}.dTwistControlEnable', 1)
		cmds.setAttr( f'{ikh}.dWorldUpType', 3)
		cmds.setAttr( f'{ikh}.dForwardAxis', fwd_axis_idx)
		cmds.setAttr( f'{ikh}.dWorldUpAxis', up_axis_idx)
		cmds.setAttr( f'{ikh}.dWorldUpVector{up_ab_axis.upper()}', up_axis_value)
		for ax in other_axes:
			cmds.setAttr( f'{ikh}.dWorldUpVector{ax}', 0)
		cmds.connectAttr(f'{self.main_ctrl}.worldMatrix[0]', f'{ikh}.dWorldUpMatrix')

		# Finding Circumference
		ik_crv_shp = cmds.listRelatives(self.ik_crv, s=True)[0]
		ik_crv_cif = bb.create_node('curveInfo', self.base, ['iksp'], self.number, self.side)
		cmds.connectAttr(f'{ik_crv_shp}.worldSpace[0]', f'{ik_crv_cif}.inputCurve')

		# calculate percentage of the moved distance to 1 full loop (max offset value in .i1x = 1)
		max_val = cmds.getAttr(f'{self.ik_crv}.max')
		perc_mdv = bb.create_node('multiplyDivide', self.base, ['perc'], self.number, self.side)
		cmds.setAttr(f'{perc_mdv}.op', 2 )
		cmds.setAttr( f'{perc_mdv}.i1x', max_val)
		cmds.connectAttr(f'{ik_crv_cif}.arcLength', f'{perc_mdv}.i2x')

		start_loc = bb.create_node('locator', self.base, ['start'], self.number, self.side)
		move_loc = bb.create_node('locator', self.base, ['move'], self.number, self.side)
		cmds.parent([start_loc, move_loc], self.mod_grp)

		main_ctrl_pos = cmds.xform(self.main_ctrl, q=True, t=True, ws=True)
		cmds.xform(start_loc, t=[main_ctrl_pos[0], 0, main_ctrl_pos[2]], ws=True)
		cmds.xform(move_loc, t=[main_ctrl_pos[0], 0, main_ctrl_pos[2]], ws=True)
		bb.create_constrain([self.main_ctrl], move_loc, 'parent', maintain_offset=True)

		start_loc_shp = cmds.listRelatives(start_loc, s=True)[0]
		move_loc_shp = cmds.listRelatives(move_loc, s=True)[0]
		distance_ddm = bb.create_node('distanceDimShape', self.base, ['dist'], self.number, self.side)
		distance_ddm_shp = cmds.listRelatives(distance_ddm, s=True)[0]
		cmds.connectAttr(f'{start_loc_shp}.worldPosition[0]', f'{distance_ddm}.startPoint')
		cmds.connectAttr(f'{move_loc_shp}.worldPosition[0]', f'{distance_ddm}.endPoint')
		cmds.parent(distance_ddm, self.mod_grp)
		cmds.hide(distance_ddm)

		mul_dis_mdl = bb.create_node('multDoubleLinear', self.base, ['mul', 'dis'], self.number, self.side)
		cmds.connectAttr(f'{perc_mdv}.ox', f'{mul_dis_mdl}.i1')
		cmds.connectAttr(f'{distance_ddm}.distance', f'{mul_dis_mdl}.i2')

		start_loc_dcm = bb.create_node('decomposeMatrix', self.base, ['start'], self.number, self.side)
		move_loc_dcm = bb.create_node('decomposeMatrix', self.base, ['move'], self.number, self.side)
		cmds.connectAttr(f'{start_loc}.matrix', f'{start_loc_dcm}.inputMatrix')
		cmds.connectAttr(f'{move_loc}.matrix', f'{move_loc_dcm}.inputMatrix')

		fwd_dir_pma = bb.create_node('plusMinusAverage', self.base, ['fwd', 'dir'], self.number, self.side)
		cmds.setAttr(f'{fwd_dir_pma}.op', 2 )
		cmds.connectAttr(f'{move_loc_dcm}.outputTranslateZ', f'{fwd_dir_pma}.input1D[0]')
		cmds.connectAttr(f'{start_loc_dcm}.outputTranslateZ', f'{fwd_dir_pma}.input1D[1]')

		dir_cdt = bb.create_node('condition', self.base, ['dir'], self.number, self.side)
		cmds.setAttr(f'{dir_cdt}.op', 2 )
		cmds.setAttr( f'{dir_cdt}.st', 0)
		cmds.setAttr( f'{dir_cdt}.ctr', -1)
		cmds.setAttr( f'{dir_cdt}.cfr', 1)
		cmds.connectAttr(f'{fwd_dir_pma}.output1D', f'{dir_cdt}.ft')

		dir_mul_mdl = bb.create_node('multDoubleLinear', self.base, ['dir', 'mul'], self.number, self.side)
		cmds.connectAttr(f'{mul_dis_mdl}.o', f'{dir_mul_mdl}.i1')
		cmds.connectAttr(f'{dir_cdt}.ocr', f'{dir_mul_mdl}.i2')

		only_fwd_cdt = bb.create_node('condition', self.base, ['fwd', 'dir'], self.number, self.side)
		cmds.setAttr(f'{only_fwd_cdt}.op', 1 )
		cmds.setAttr( f'{only_fwd_cdt}.st', 0)
		cmds.setAttr( f'{only_fwd_cdt}.cfr', 0)
		cmds.connectAttr(f'{dir_mul_mdl}.o', f'{only_fwd_cdt}.ctr')
		cmds.connectAttr(f'{fwd_dir_pma}.output1D', f'{only_fwd_cdt}.ft')

		# Extra Attribute
		prefix = '_'.join([self.side, self.base])
		bb.attr_separator(self.main_ctrl, f'{prefix}')
		auto_spin_attr = prefix + '_' + AUTO_SPIN_TYPE_ATTR
		speed_attr = prefix + '_' + SPEED_ATTR
		offset_attr = prefix + '_' + OFFSET_ATTR

		cmds.addAttr( self.main_ctrl, ln = auto_spin_attr, at = 'enum', en = AUTO_TYPE_ENUM, k = True )
		cmds.addAttr( self.main_ctrl, ln = speed_attr, at = 'float', dv = 1, k = True )
		cmds.addAttr( self.main_ctrl, ln = offset_attr, at = 'float', dv = 0, k = True )

		# Add switch
		#auto_type_bta = bb.create_node('blendTwoAttr', self.base, ['switch'], self.number, self.side)
		auto_type_chc = bb.create_node('choice', self.base, ['switch'], self.number, self.side)
		cmds.connectAttr(f'{self.main_ctrl}.{auto_spin_attr}', f'{auto_type_chc}.selector')
		cmds.setAttr( f'{auto_type_chc}.input[0]', 0)

		# Add auto time
		mul_val = -0.005
		auto_time_mdl = bb.create_node('multDoubleLinear', self.base, ['auto', 'time'], self.number, self.side)
		cmds.connectAttr(f'{self.time_node}.outTime', f'{auto_time_mdl}.input1')
		cmds.setAttr( f'{auto_time_mdl}.i2', mul_val)

		# Connect switch
		cmds.connectAttr(f'{only_fwd_cdt}.ocr', f'{auto_type_chc}.input[1]')
		cmds.connectAttr(f'{auto_time_mdl}.o', f'{auto_type_chc}.input[2]')
		
		# Speed Attribute
		speed_mdl = bb.create_node('multDoubleLinear', self.base, [SPEED_ATTR], self.number, self.side)
		cmds.connectAttr(f'{auto_type_chc}.o', f'{speed_mdl}.i1')
		cmds.connectAttr(f'{self.main_ctrl}.{speed_attr}', f'{speed_mdl}.i2')
		#cmds.connectAttr(f'{only_fwd_cdt}.ocr', f'{speed_mdl}.i2')				# <<<<< 

		# Inv Offset Attr
		inv_offset_mdl = bb.create_node('multDoubleLinear', self.base, ['inv', OFFSET_ATTR], self.number, self.side)
		cmds.connectAttr(f'{self.main_ctrl}.{offset_attr}', f'{inv_offset_mdl}.i1')
		cmds.setAttr( f'{inv_offset_mdl}.i2', -1)

		# Offset Attribute
		offset_adl = bb.create_node('addDoubleLinear', self.base, [OFFSET_ATTR], self.number, self.side)
		cmds.connectAttr(f'{inv_offset_mdl}.o', f'{offset_adl}.i1')
		cmds.connectAttr(f'{speed_mdl}.o', f'{offset_adl}.i2')

		# Set Driven Key
		driver = f'{offset_adl}.o'
		driven = f'{ikh}.offset'
		cmds.setDrivenKeyframe(driven, cd=driver, itt = 'linear', ott = 'linear', dv=0, v=0 )
		cmds.setDrivenKeyframe(driven, cd=driver, itt = 'linear', ott = 'linear', dv=max_val, v=max_val )
		key = cmds.listConnections(driven, type='animCurve')[0]
		cmds.setAttr( f'{key}.preInfinity', 3)
		cmds.setAttr( f'{key}.postInfinity', 3)

		# Tweakers rig
		if self.tweakers == None:
			bb.create_constrain([self.main_ctrl], self.ik_crv, 'pac')
		else:
			self.tweaker_rig(tweaker_num = self.tweakers)

		cmds.parent([ikh, self.ik_crv], self.mod_grp)

		# Make variables accesible for function wheel_rig
		self.fwd_dir_pma =  fwd_dir_pma
		self.dir_cdt =  dir_cdt
		self.speed_mdl = speed_mdl
		self.offset_adl =  offset_adl

		self.auto_spin_attr =  auto_spin_attr
		self.speed_attr =  speed_attr
		self.offset_attr =  offset_attr

		self.auto_type_chc =  auto_type_chc

		if self.engine_grp is not None:
			self.engine_fx()

	def create_joints(self, rad = 10):
		transforms = cmds.listRelatives(self.geo_grp, c=True, type='transform')
		self.meshes = []

		for obj in transforms:
			shape = cmds.listRelatives(obj, s=True)
			if shape and cmds.objectType(shape[0], i='mesh'):
				self.meshes.append(obj)
		aim_vec = bb.axis_convert(self.aim_axis, 'vector')
		up_vec = bb.axis_convert(self.up_axis, 'vector')
		jnts = []		
		for mesh in self.meshes:
			base, element, number, side, suffix = NAMER.extract(mesh)
			base = parser.get_base_name(base, base_number=False)
			pv_cpn = [f'{mesh}.vtx{self.pivot_vtx[0]}', f'{mesh}.vtx{self.pivot_vtx[1]}']
			pv_pos = bb.get_center_position(pv_cpn)
			jnt = bb.create_node('joint', base, element, number, side, rad = rad)
			cmds.xform(jnt, t=[pv_pos[0], pv_pos[1], pv_pos[2]], ws=True)
			if len(jnts) > 0:
				cmds.delete(cmds.aimConstraint(jnt, jnts[-1], aimVector= aim_vec, upVector=up_vec, worldUpType="vector", worldUpVector = up_vec ))
				cmds.parent(jnt, jnts[-1])
			jnts.append(jnt)
		cmds.delete(cmds.aimConstraint(jnts[0], jnts[-1], aimVector= aim_vec, upVector=up_vec, worldUpType="vector", worldUpVector = up_vec ))

		# Create last joint
		# last_jnt = bb.create_node('joint', base, element, str(int(number)+1), side, rad = rad)
		# cmds.matchTransform(last_jnt, jnts[0])
		# cmds.parent(last_jnt, jnts[-1])
		# cmds.setAttr( f'{last_jnt}.radius', rad*2)

		# Aim last joint
		cmds.aimConstraint(jnts[0], jnts[-1], offset=[0, 0, 0], aim=aim_vec, u=up_vec, wut='objectrotation', wuo=self.main_ctrl)
		return jnts

	def constrain_mesh(self):
		for jnt, mesh in zip(self.jnt_list, self.meshes):
			bb.create_constrain([jnt], mesh, 'psc')

	def tweaker_rig(self, tweaker_num = 10, color_set = 'sec'):
		twk_jnts = []
		twk_ctrls = []

		twk_ctrl_grp = bb.create_node('group', self.base, ['tweaker', 'ctrl'], self.number, self.side)
		bb.create_constrain([self.main_ctrl], twk_ctrl_grp)
		cv, spans, degree = bb.get_curve_info(self.ik_crv)
		twk_amount = round(cv/tweaker_num)

		format_side = parser.format_side(self.side, 'upper') or 'M'
			
		if color_set == 'sec':
			side_color = shape_color.CTRL_SEC_COLOR[format_side]
		elif color_set == 'ter':
			side_color = shape_color.CTRL_TER_COLOR[format_side]
		elif color_set == 'grp':
			side_color = shape_color.CTRL_GRP_COLOR[format_side]
		else:
			side_color = shape_color.CTRL_COLOR[format_side]

		for i in range(0, cv):
			if i%twk_amount == 0:
				cv_pos = cmds.xform(f'{self.ik_crv}.cv[{i}]', ws=True, t=True, q=True)
				jnt_num = len(twk_jnts) + 1
				twk_jnt = bb.create_node('joint', self.base, ['tweaker'], jnt_num, self.side, p=cv_pos)
				cmds.parent(twk_jnt, self.mod_grp)
				twk_jnts.append(twk_jnt)

				twk_ctrl = bc.Controller(objects = [twk_jnt],
										main_ctrl_grp = twk_ctrl_grp,
										offset_names = ['tweaker', 'ctrl'],
										shape = 'arrowPlus2dir',
										color = side_color,
										scale = self.scale,
										line_width = 1.0,
										connection_type = 'parent',
										clean_elem = 'bnd',
										deg=1)
			
		twk_skc = sk.bind_skin(twk_jnts, self.ik_crv)

	def wheel_rig(self, wheel_meshes = [], inverse_val = -1):
		result_node = f'{self.fwd_dir_pma}.output1D'
		full_loop_value = -360
		time_mul_value = inverse_val

		# Reverse forward value
		cmds.setAttr( f'{self.dir_cdt}.ctg', 1)
		cmds.setAttr( f'{self.dir_cdt}.cfg', -1)

		# Calculate wheel rotation angle
		wheel_dis_mdl = bb.create_node('multDoubleLinear', self.base, ['wheel', 'dist'], self.number, self.side)
		cmds.connectAttr(f'{self.fwd_dir_pma}.output1D', f'{wheel_dis_mdl}.i1')
		cmds.connectAttr(f'{self.dir_cdt}.ocg', f'{wheel_dis_mdl}.i2')

		# Auto time
		auto_time_mdl = bb.create_node('multDoubleLinear', self.base, ['wheel', 'auto', 'time'], self.number, self.side)
		cmds.connectAttr(f'{self.time_node}.outTime', f'{auto_time_mdl}.i1')
		cmds.setAttr( f'{auto_time_mdl}.i2', time_mul_value)

		# Inverse value or not?
		inv_dir_mdl = bb.create_node('multDoubleLinear', self.base, ['wheel', 'dir', 'mul'], self.number, self.side)
		cmds.connectAttr(result_node, f'{inv_dir_mdl}.i1')
		cmds.setAttr( f'{inv_dir_mdl}.i2', inverse_val)

		# Inverse offset value 
		inv_offset_val = bb.create_node('multDoubleLinear', self.base, ['wheel', 'inv', 'offset'], self.number, self.side)
		cmds.connectAttr(f'{self.main_ctrl}.{self.offset_attr}', f'{inv_offset_val}.i1')
		cmds.setAttr( f'{inv_offset_val}.i2', -100)

		for wheel in wheel_meshes:
			bbox = cmds.exactWorldBoundingBox(wheel)
			zmin = bbox[2]
			zmax = bbox[5]
			size = zmax - zmin                              # Finding diameter
			ccf = 2 * 3.14 * ( size/2 )                     # Finding circumference 2 ∙ Pi ∙ R

			base, element, number, side, suffix = NAMER.extract(wheel)

			type_switch_chc = bb.create_node('choice', base, ['switch'], number, side)
			cmds.connectAttr(f'{self.main_ctrl}.{self.auto_spin_attr}', f'{type_switch_chc}.selector')
			cmds.setAttr( f'{type_switch_chc}.input[0]', 0)
			cmds.connectAttr(f'{inv_dir_mdl}.o', f'{type_switch_chc}.input[1]')
			cmds.connectAttr(f'{auto_time_mdl}.o', f'{type_switch_chc}.input[2]')

			# x Speed
			time_speed_mdl = bb.create_node('multDoubleLinear', base, [SPEED_ATTR], number, side)
			cmds.connectAttr(f'{type_switch_chc}.o', f'{time_speed_mdl}.i1')
			cmds.connectAttr(f'{self.main_ctrl}.{self.speed_attr}', f'{time_speed_mdl}.i2')

			# + Offset
			time_offset_adl = bb.create_node('addDoubleLinear', base, [OFFSET_ATTR], number, side)
			cmds.connectAttr(f'{time_speed_mdl}.o', f'{time_offset_adl}.i1')
			cmds.connectAttr(f'{inv_offset_val}.o', f'{time_offset_adl}.i2')

			full_turn_mdl = bb.create_node('multDoubleLinear', base, ['full', 'turn'], number, side)
			cmds.connectAttr(f'{time_offset_adl}.o', f'{full_turn_mdl}.i1')
			cmds.setAttr( f'{full_turn_mdl}.i2', full_loop_value/ccf)

			mesh_tmp = cmds.duplicate(wheel)[0]
			cmds.xform(mesh_tmp, cpc=True)
			wheel_jnt = bb.create_node('joint', base, element, number, side)
			cmds.matchTransform(wheel_jnt, mesh_tmp)
			cmds.connectAttr(f'{full_turn_mdl}.o', f'{wheel_jnt}.r{self.up_axis}')
			cmds.delete(mesh_tmp)

			zro_grp = bb.create_offset_group(wheel_jnt, ['jnt'])
			zro_grp = zro_grp[wheel_jnt][0]

			cmds.parent(zro_grp, self.mod_grp)
			bb.create_constrain([self.main_ctrl], zro_grp)
			bb.create_constrain([wheel_jnt], wheel)

	def engine_fx(self):
		ATTR_NAME = 'engineFx'
		attr_soften_val = 0.1
		time_mul_val = -100

		cmds.addAttr( self.main_ctrl, ln = ATTR_NAME, at = 'float', min = 0, k = True )

		# Soften attr val
		attr_soften_mdl = bb.create_node('multDoubleLinear', self.base, ['soften'], self.number, self.side)
		cmds.connectAttr(f'{self.main_ctrl}.{ATTR_NAME}', f'{attr_soften_mdl}.i1')
		cmds.setAttr( f'{attr_soften_mdl}.i2', attr_soften_val)

		# Time mul val
		time_mul = bb.create_node('multDoubleLinear', self.base, ['engine'], self.number, self.side)
		cmds.connectAttr(f'{self.auto_type_chc}.o', f'{time_mul}.i1')
		cmds.setAttr( f'{time_mul}.i2', time_mul_val)

		# Create noise
		fx_noi = bb.create_node('noise', self.base, ['engine', 'fx'], self.number, self.side)
		cmds.connectAttr(f'{time_mul}.o', f'{fx_noi}.time')
		for CH in 'RGB':
			cmds.connectAttr(f'{attr_soften_mdl}.o', f'{fx_noi}.colorGain{CH}')

		# Connect result to the group
		cmds.connectAttr(f'{fx_noi}.outColor', f'{self.engine_grp}.rotate')
		


# from bbTools.core.utils import tracks_rig as tr
# reload(tr)

# l_tracks = tr.TracksRig(
# 						base='tracks',
# 						side='l',
# 						main_ctrl='main_ctl',
# 						aim_axis='z',
# 						up_axis='x',
# 						tweakers = 10,	
# 						geo_grp = 'l_tracks_geo_grp', 
# 						engine_grp = 'body_grp',
# 						pivot_vtx = [[4], [7]],
# 						scale = 4
# )

# l_tracks.build()
# l_tracks.wheel_rig(wheel_meshes = ['l_wheel_01_ply', 'l_wheel_02_ply', 'l_wheel_03_ply', 'l_wheel_04_ply', 'l_wheel_05_ply'])



# r_tracks = tr.TracksRig(
# 						base='tracks',
# 						side='r',
# 						main_ctrl='main_ctl',
# 						aim_axis='z',
# 						up_axis='x',
# 						tweakers = 10,	
# 						geo_grp = 'r_tracks_geo_grp', 
# 						engine_grp = 'body_grp',
# 						pivot_vtx = [[4], [7]],
# 						scale = 4
# )

# r_tracks.build()
# r_tracks.wheel_rig(wheel_meshes = ['l_wheel_01_ply', 'l_wheel_02_ply', 'l_wheel_03_ply', 'l_wheel_04_ply', 'l_wheel_05_ply'])











