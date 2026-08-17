from importlib import reload
import maya.cmds as cmds
from ..core.utils import rig_utils as bb
from ..core.controllers import creator as bc
from ..core.utils import skin_utils as skin
from ..core.naming import namer_factory as naming
from ..core.naming import current_project
from ..core.naming import parser

reload(bb)
reload(bc)
reload(skin)
reload(naming)
reload(current_project)
reload(parser)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

class RibbonRig:
	def __init__(self,
				joints = None,
				rig_name = None,
				feature_name = None,
				side = None,
				aim_axis = 'x',
				up_axis = 'y',
				num_nurb_subdivision = 8,
				connection_type = 'parent',
				scale = 1,
				ctrl_parent =None,
				mod_parent = None,
				upper_bind_parent ='',
				lower_bind_parent = '',
				color = None,
				end_orient_loc = None,
				upper_driver = None,
				global_scale = None,
				**controller_kwargs
				):
		
		self.joints =  joints
		self.rig_name =  rig_name
		self.feature_name =  feature_name or 'ribbon'
		self.aim_axis =  aim_axis
		self.up_axis =  up_axis
		self.num_nurb_subdivision =  num_nurb_subdivision
		self.connection_type =  connection_type
		self.scale =  scale
		self.ctrl_parent =  ctrl_parent
		self.mod_parent =  mod_parent
		self.upper_bind_parent =  upper_bind_parent
		self.lower_bind_parent =  lower_bind_parent
		self.color =  color
		self.end_orient_loc = end_orient_loc
		self.upper_driver =  upper_driver
		self.global_scale =  global_scale
		self.controller_kwargs =  controller_kwargs

		self.cross_vector = bb.axis_convert(aim_axis, 'cross_vector', up_axis)
		default_shape_rotation = [item * 90 for item in self.cross_vector]
		self.shape_rotation = controller_kwargs.get('shape_rotation', default_shape_rotation)
		#self.shape_rotation = default_shape_rotation

		if side is None :
			self.side = parser.find_element(joints[0], 'sides')
		else:
			self.side =  side
		
		self.ctrl_grp = None
		self.mod_grp = None
		self.bind_jnts = None
		self.ctrls = None
		self.jnts_grp = None

		self.build()
		#bb.over_and_out('RibbonRig', f'{self.side}{self.rig_name}')

	def build(self):
		self.ctrl_grp = bb.create_node('group', self.rig_name, [self.feature_name, 'ctrl'], None, self.side, p=self.ctrl_parent)
		self.mod_grp = bb.create_node('group', self.rig_name, [self.feature_name,'mod'], None, self.side, p=self.mod_parent)

		aim_axis_vector = list(bb.axis_convert(self.aim_axis, return_type = 'vector'))
		up_axis_vector = list(bb.axis_convert(self.up_axis, return_type = 'vector'))
		cross_axis_vector = bb.axis_convert(self.aim_axis, 'cross_vector', self.up_axis)

		base_names =[]
		joint_positions = []
		for jnt in self.joints:
			posi = cmds.xform(jnt, ws=True, q=True, t=True)
			joint_positions.append(posi)
			base_name = parser.get_base_name(jnt, first_name = True)
			base_names.append(base_name)

		# ———————————————————————————————
		# ========= Create Nurb =========
		nurb_a_crv = cmds.curve(p=joint_positions, d=1)
		nurb_a_crv = cmds.rename(nurb_a_crv, 'nurb_a_crv')
		cmds.matchTransform(nurb_a_crv, self.joints[0])
		bb.freeze(nurb_a_crv, r=False)
		for i in range(0, bb.get_cv_count(nurb_a_crv)+1):
			cmds.xform(f'{nurb_a_crv}.cv[{i}]', t = joint_positions[i], ws=True)
		nurb_a_crv = cmds.rebuildCurve(nurb_a_crv, ch=False, rpo=True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=self.num_nurb_subdivision, d=3, tol=0.01)
		nurb_b_crv = cmds.duplicate(nurb_a_crv, n='nurb_b_crv')[0]
		a_move_value = [item * 2 for item in up_axis_vector]
		b_move_value = [item * -2 for item in up_axis_vector]
		cmds.move(*a_move_value, nurb_a_crv, r=True, os=True)
		cmds.move(*b_move_value, nurb_b_crv, r=True, os=True)
		node_name = NAMER.format(base= self.rig_name, element = [self.feature_name], side = self.side, suffix = 'nrb' )
		nurb = cmds.loft(nurb_b_crv, nurb_a_crv, ch=False, u=1, c=0, ar=1, d=1, ss=1, rn=0, po=0, rsn=True, n=node_name)[0]
		cmds.delete(nurb_a_crv,nurb_b_crv)
		cmds.parent(nurb, self.mod_grp)

		# —————————————————————————————————————————————
		# ========= Create Ribbon Controllers =========
		up_posi = bb.get_center_position(self.joints[:2])
		lo_posi = bb.get_center_position(self.joints[1:])
		up_joint = bb.create_node('joint', self.rig_name, [self.feature_name, 'up'], side = self.side, p = up_posi, rad = 2)
		lo_joint = bb.create_node('joint', self.rig_name, [self.feature_name, 'lo'], side = self.side, p = lo_posi, rad = 2)

		mid_jnts_grp = bb.create_node('group', self.rig_name, [self.feature_name, 'mid'], None, self.side)
		mid_up_joint = bb.create_node('joint', self.rig_name, [self.feature_name, 'mid', 'up'], side = self.side, rad = 2)
		mid_lo_joint = bb.create_node('joint', self.rig_name, [self.feature_name, 'mid', 'lo'], side = self.side, rad = 2)
		cmds.parent(mid_up_joint, mid_lo_joint, mid_jnts_grp)
		cmds.matchTransform(mid_jnts_grp, self.joints[1])

		up_controller = bc.Controller(objects = [up_joint],
						offset_names = ['Zro', 'Offset'],
						main_ctrl_grp = self.ctrl_grp,
						color = 'sky',
						connection_type = 'parent',
						scale = self.scale,
						**self.controller_kwargs
						)
		self.up_ctrl = up_controller.ctrls[0]
		up_grp = up_controller.offset_grps[0][0]
		cmds.matchTransform(up_grp, self.joints[0], rot=True)

		lo_controller = bc.Controller(objects = [lo_joint],
								offset_names = ['Zro', 'aim', 'Offset'],
								main_ctrl_grp = self.ctrl_grp,
								color = 'sky',
								connection_type = 'parent',
								scale = self.scale,
								**self.controller_kwargs
								)
		self.lo_ctrl = lo_controller.ctrls[0]
		lo_grp = lo_controller.offset_grps[0]
		cmds.matchTransform(lo_grp, self.joints[1], rot=True)

		mid_controller = bc.Controller(objects = [mid_jnts_grp],
								offset_names = ['Zro', 'Offset'],
								main_ctrl_grp = self.ctrl_grp,
								color = 'sky',
								connection_type = 'point',
								scale = self.scale,
								**self.controller_kwargs
								)
		self.mid_ctrl = mid_controller.ctrls[0]
		mid_grp = mid_controller.offset_grps[0][0]

		# ————————————————————————————
		# ========= Follicle =========
		subdivision = cmds.getAttr(f'{nurb}.spansUV')[0]
		subdivision = max(subdivision)
		nurb_shp = cmds.listRelatives(nurb, s=True)[0]

		follicle_grp = bb.create_node('group', base=self.rig_name, elements=['follicle'], side=self.side, p = self.mod_grp)
		cmds.hide(follicle_grp)
		self.bind_jnts = []
		half_length = (subdivision)/2
		for i in range(0, subdivision):
			u_position = ((1/subdivision) * i) + (1/(subdivision*2))
			follicle = bb.create_node('follicle', self.rig_name, [self.feature_name], number = f'{i+1:02d}', side = self.side)
			follicle_shp = cmds.listRelatives(follicle, s=True)[0]
			cmds.connectAttr(f'{nurb_shp}.local', f'{follicle_shp}.inputSurface')
			cmds.connectAttr(f'{nurb_shp}.worldMatrix[0]', f'{follicle_shp}.inputWorldMatrix')
			cmds.connectAttr(f'{follicle_shp}.ot', f'{follicle}.t')
			cmds.connectAttr(f'{follicle_shp}.or', f'{follicle}.r')
			cmds.setAttr( f'{follicle_shp}.parameterU', u_position)
			cmds.setAttr( f'{follicle_shp}.parameterV', 0.5)
			cmds.parent(follicle, follicle_grp)
			bind_jnt = bb.create_node('joint', self.rig_name, [self.feature_name, 'bnd'], f'{i+1:02d}', self.side)
			cmds.matchTransform(bind_jnt, follicle)
			#bb.create_constrain([follicle], bind_jnt, type = 'parent', maintain_offset=True)
			if self.upper_bind_parent:
				if i < half_length:
					cmds.parent(bind_jnt, self.upper_bind_parent)
				else:
					cmds.parent(bind_jnt, self.lower_bind_parent)
				self.bind_jnts.append(bind_jnt)
			
			if i < half_length -1:
				scale_ctrl = self.up_ctrl
			elif i > half_length + 1:
				scale_ctrl = self.lo_ctrl
			else:
				scale_ctrl = self.mid_ctrl

			#cmds.connectAttr(f'{scale_ctrl}.s',  f'{follicle}.s')
			scale_base, scale_element, scale_number, scale_side, suffix = NAMER.extract(scale_ctrl)
			node_name = NAMER.format(scale_base, scale_element, scale_number, scale_side, 'mmt')
			if not cmds.objExists(node_name):
				scale_mmt = bb.create_node('multMatrix', scale_base, scale_element + ['scale'], scale_number, scale_side)
				scale_dcm = bb.create_node('decomposeMatrix', scale_base, scale_element + ['scale'], scale_number, scale_side)
			
			cmds.connectAttr(f'{scale_ctrl}.worldMatrix[0]', f'{scale_mmt}.matrixIn[0]')
			cmds.connectAttr(f'{scale_mmt}.matrixSum', f'{scale_dcm}.inputMatrix')
			cmds.connectAttr(f'{scale_dcm}.outputScale', f'{follicle}.s')

			bb.matrix_constrain(follicle, bind_jnt)
		
		# —————————————————————————————————————
		# ========= Parent Inverse Mtx =========
		bb.create_constrain([self.joints[1]], mid_grp, type = 'point')
		mid_orc = bb.create_constrain(self.joints[:2], mid_grp, type = 'orient')[0][0]
		cmds.setAttr(f'{mid_orc}.interpType', 2)

		mid_up_orc = bb.create_constrain([self.joints[0]], mid_up_joint, type = 'orient')[0][0]
		mid_lo_orc = bb.create_constrain([self.joints[1]], mid_lo_joint, type = 'orient')[0][0]
		cmds.connectAttr(f'{self.mid_ctrl}.parentInverseMatrix[0]', f'{mid_up_orc}.constraintParentInverseMatrix', f=True)
		cmds.connectAttr(f'{self.mid_ctrl}.parentInverseMatrix[0]', f'{mid_lo_orc}.constraintParentInverseMatrix', f=True)

		# i = 1
		# for jnt in self.bind_jnts:
		# 	parent_jnt = self.joints[0] if i <= 5 else self.joints[1]
		# 	cmds.connectAttr(f'{parent_jnt}.s', f'{jnt}.s')
		# 	i += 1
		
		# —————————————————————————
		# ========= Twist =========
		twist_jnt = bb.create_node('joint', base_names[2], [self.feature_name, 'twist'], None, self.side)
		twist_grp = bb.create_offset_group([twist_jnt], ['Zro', 'Offset'])
		twist_grp= twist_grp[twist_jnt]
		if self.end_orient_loc:
			bb.snap(parents=[self.end_orient_loc], target=twist_grp[0])
		else:
			bb.snap(parents=[self.joints[2]], target=twist_grp[0])
		bb.create_constrain([self.joints[2]], twist_grp[0], type='parent')
		neg_aim_axis_vector = [ax * -1 for ax in aim_axis_vector]
		cmds.aimConstraint(self.joints[1], twist_grp[1], aimVector=neg_aim_axis_vector, upVector=neg_aim_axis_vector, worldUpType= 'object', worldUpObject = self.joints[1], mo = True)

		# ————————————————————————————
		# ========= No Twist =========
		no_twist_jnt = bb.create_node('joint', base_names[0], [self.feature_name, 'no', 'twist'], None, self.side)
		no_twist_grp = bb.create_offset_group([no_twist_jnt], ['Zro', 'Offset'])
		no_twist_grp= no_twist_grp[no_twist_jnt]
		bb.snap(parents=[self.joints[0]], target=no_twist_grp[0])
		bb.create_constrain([self.joints[0]], no_twist_grp[0], type='point')
		cmds.aimConstraint(self.joints[1], no_twist_grp[1], aimVector=aim_axis_vector, upVector=up_axis_vector, worldUpType= 'objectrotation', mo = True, wuo = self.upper_driver, wu = up_axis_vector)

		# ————————————————————————————
		# ========= Organize =========
		bb.create_constrain(self.joints[:2], up_grp, type = 'point')
		up_orc = bb.create_constrain([self.joints[0], no_twist_jnt], up_grp, type = 'orient')[0][0]
		cmds.setAttr(f'{up_orc}.interpType', 2)

		bb.create_constrain(self.joints[1:], lo_grp[0], type = 'point')
		lo_orc = bb.create_constrain(self.joints[1:], lo_grp[0], type = 'orient')[0][0]
		cmds.setAttr(f'{lo_orc}.interpType', 2)
		cmds.aimConstraint(self.joints[1], lo_grp[1], aimVector=neg_aim_axis_vector, upVector=cross_axis_vector, worldUpType= 'None', mo = True)

		ribbon_jnts = [up_joint, mid_up_joint, mid_lo_joint, lo_joint, twist_jnt, no_twist_jnt]
		skin_jnts = self.joints + ribbon_jnts
		nurb_skc = skin.bind_skin(skin_jnts, nurb)

		ribbon_jnt_grp = bb.create_node('group', self.rig_name, [self.feature_name, 'jnt'], None, self.side, p=self.mod_grp)
		cmds.parent(up_joint, lo_joint, mid_jnts_grp, twist_grp[0], no_twist_grp[0], ribbon_jnt_grp)

		self.ctrls = [self.up_ctrl, self.mid_ctrl, self.lo_ctrl]
		self.jnts_grp = ribbon_jnt_grp


## Example usage
# from bbTools.core import RibbonRig as rbn
# ribbon_rig = rbn.RibbonRig(joints = ['l_shoulder_rig_jnt', 'l_elbow_rig_jnt', 'l_wrist_rig_jnt'],
# 				rig_name = 'arm',
# 				feature_name = 'ribbon',
# 				aim_axis = 'x',
# 				up_axis = 'y',
# 				num_nurb_subdivision = 8,
# 				connection_type = 'parent',
# 				scale = 1,
# 				ctrl_parent =None,
# 				mod_parent = None,
# 				upper_bind_parent ='',
# 				lower_bind_parent = '',
# 				shape_rotation = [0,0,90],
# 				color = None )






		