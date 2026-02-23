from importlib import reload
import maya.cmds as cmds
from . import base
from . import face_config
from ...core.utils import rig_utils as bb
from ...core.naming import namer_factory as naming
from ...core.naming import current_project
from ...core.naming import parser

reload(bb)
reload(base)
reload(face_config)
reload(naming)
reload(current_project)
reload(parser)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

FaceModule = base.FaceModule

class LipRig(FaceModule):
	def __init__(self, 
				blueprint_grp = None, 
				default_shape='crossCircle',
				name = 'lip',
				side=None,
				lip_jnts = ['upper_lip_bp_jnt', 'lower_lip_bp_jnt'],
				corner_jnts = ['l_lip_corner_lip_bp_jnt', 'r_lip_corner_lip_bp_jnt'],
				nurbs = ['lip_upper_nrb', 'lip_lower_nrb'],
				parent_ctrl_grp=None,
				parent_mod_grp=None,
				remove_elem='bp'
				):
		super().__init__(name, side, parent_ctrl_grp, parent_mod_grp, remove_elem)
		self.blueprint_grp =  blueprint_grp
		self.default_shape =  default_shape
		self.name =  name
		self.side = side
		self.lip_jnts =  lip_jnts
		self.corner_jnts =  corner_jnts
		self.nurbs =  nurbs

		self.config = face_config.LIP_SETTINGS
		self.follow_attr = 'follow'
		self.corner_parents = ['skull_ctl', 'jaw_ctl']

		self.feature_name = ''

	def build(self):
		face_module = self.build_hierarchy(self.name, self.side)	
		#cmds.parent(face_module.mod_grp, )
		# main_jnt_grp = NAMER.format(self.name, ['main'], None, self.side, 'grp')
		# self.jnt_grp = cmds.rename(self.jnt_grp, main_jnt_grp)

		self.lip_grps = []
		self.lip_ctrls = []

		self.lip_corner_grps = []
		self.lip_corner_ctrls = []
		self.lip_corner_jnt_grps = []

		cmds.parent(self.nurbs, self.mod_grp)

		for jnt in self.lip_jnts:
			part = 'upper' if 'upper' in jnt else 'lower'
			lip_jnt_grp, lip_jnt = self.create_rig_joint(jnt, parent_jnt_grp=self.jnt_grp, rad=0.25)
			lip_ctrl_grp, lip_ctrl = self.create_controller(
											lip_jnt, 
											self.config[f'{part}_shape'], 
											1, 
											[0, 0, 0], 
											self.config[f'main_{part}_move'], 
											'direct'
										)
			self.lip_grps.append(lip_ctrl_grp)
			self.lip_ctrls.append(lip_ctrl)
		
			lip_ctrl_grp = lip_ctrl_grp[0]
			if part == 'upper':
				bb.create_constrain([self.corner_parents[0]], lip_ctrl_grp)
			else:
				bb.create_constrain([self.corner_parents[1]], lip_ctrl_grp)
			bb.direct_connect([lip_ctrl_grp], [lip_jnt_grp])

		for jnt in self.corner_jnts:
			corner_jnt_grp, corner_jnt = self.create_rig_joint(jnt, parent_jnt_grp=self.jnt_grp, rad=0.25, offset_names=['jnt', 'jnt_' + self.follow_attr])
			self.lip_corner_jnt_grps.append(corner_jnt_grp)

			corner_ctrl_grp, corner_ctrl = self.create_controller(
												corner_jnt, 
												self.config['shape'], 
												self.config['scale'], 
												self.config['rotate'], 
												self.config['move'], 
												'direct', 
												offset_names=['ctrl', 'ctrl_'+ self.follow_attr]
											)

			bb.add_follow_attr(parents = self.corner_parents, target = corner_ctrl_grp[1], attr_name = self.follow_attr, ctrl = corner_ctrl, min=0, max=1, dv=0.5, multiply=False, connect_type = 'parent')
			#bb.create_constrain([corner_ctrl_grp[1]],  corner_jnt_grp, 'pac')
			bb.direct_connect([corner_ctrl_grp[1]],  [corner_jnt_grp[1]])
			self.lip_corner_grps.append(corner_ctrl_grp)
			self.lip_corner_ctrls.append(corner_ctrl)

	def ribbon_rig(self):
		ribbon_ctrl_grp = bb.create_node('group', base=self.name, elements=[self.feature_name, 'ctrl'], side=self.side, p = self.ctrl_grp)
		local_nurb_ctrl_grp = bb.create_node('group', base=self.name, elements=[self.feature_name, 'sec', 'ctrl'], side=self.side, p = ribbon_ctrl_grp)

		for i_part, nurb in enumerate(self.nurbs):
			nurb_name = parser.get_base_name(nurb)
			nurb_side = parser.find_element(nurb, 'sides')

			is_upper = 'upper' in nurb_name
			part = 'upper' if is_upper else 'lower'

			part_ctrl_grp = bb.create_node('group', base=self.name, elements=[part, self.feature_name, 'ctrl'], side=self.side, p = ribbon_ctrl_grp)
			subdivision = cmds.getAttr(f'{nurb}.spansUV')[0]
			subdivision = max(subdivision)
			
			nurb_shp = cmds.listRelatives(nurb, s=True)[0]
			follicle_grp = bb.create_node('group', base=nurb_name, elements=['follicle'], side=nurb_side, p = self.mod_grp)

			local_nurb_grp = bb.create_node('group', base=nurb_name, elements=[self.feature_name, 'sec', 'nurb'], side=nurb_side, p = self.mod_grp)

			local_nurb = cmds.duplicate(nurb)[0]
			local_nurb_name = NAMER.format(nurb_name, [self.feature_name, 'sec'], None, nurb_side, 'nrb')
			local_nurb = cmds.rename(local_nurb, local_nurb_name)
			cmds.parent(local_nurb, local_nurb_grp)

			l_num = (round(subdivision/2))
			r_num = 0
			cmds.hide(follicle_grp)

			for i in range(0, subdivision):
				u_position = ((1/subdivision) * i) + (1/(subdivision*2))
				if u_position < 0.5:
					sub_side = 'l'
					l_num -= 1
					#scale_value = [1, 1, 1]
					l_num = abs(l_num)
					num = f'{l_num:02d}'
				elif u_position > 0.5:
					sub_side = 'r'
					r_num += 1
					#scale_value = [-1, 1, 1]
					num = f'{r_num:02d}'
				else:
					sub_side = 'm'
					#scale_value = [1, 1, 1]
					num = None
							
				follicle = bb.create_node('follicle', nurb_name, [self.feature_name], None, None)
				follicle_name = NAMER.format(nurb_name, [self.feature_name], num, sub_side, 'fol')
				follicle = cmds.rename(follicle, follicle_name)
				follicle_shp = cmds.listRelatives(follicle, s=True)[0]
				cmds.connectAttr(f'{nurb_shp}.local', f'{follicle_shp}.inputSurface')
				cmds.connectAttr(f'{nurb_shp}.worldMatrix[0]', f'{follicle_shp}.inputWorldMatrix')
				cmds.connectAttr(f'{follicle_shp}.ot', f'{follicle}.t')
				cmds.connectAttr(f'{follicle_shp}.or', f'{follicle}.r')
				cmds.setAttr( f'{follicle_shp}.parameterU', u_position)
				cmds.setAttr( f'{follicle_shp}.parameterV', 0.5)
				cmds.parent(follicle, follicle_grp)

				bind_jnt_grp, bind_jnt = self.create_rig_joint(follicle, parent_jnt_grp=follicle, rad=0.25,)

				cmds.xform(bind_jnt_grp, ro=self.config[f'{part}_rotate'], r=True, os=True)
				#cmds.setAttr(f'{bind_offset_grp}.s', *scale_value)

				lip_rbn_ctrl_grp, lip_rbn_ctrl = self.create_controller(
													bind_jnt, 
													'crossCircle', 
													self.config['scale'] * 0.2, 
													[90, 0, 0], 
													self.config[f'{part}_move'], 
													'direct', 
													offset_names=['con', 'zro'],
													color_set = 'ter',
													ctrl_grp = part_ctrl_grp
												)
				bb.direct_connect([follicle], [lip_rbn_ctrl_grp[0]])
				cmds.xform(lip_rbn_ctrl_grp[1], os=True, ro=self.config[f'{part}_rotate'])
				point_jnt_grp, point_jnt = self.create_rig_joint(bind_jnt, parent_jnt_grp=self.jnt_grp, rad=0.25, add_elem = 'point')
				cmds.parent(point_jnt_grp, follicle_grp)
				bb.matrix_constrain(bind_jnt, point_jnt, channels = ['translate', 'scale'])

				# Nurb Blendshape
				local_nurb_jnts = []
				if num is None or int(num) %2 == 0:
					#nurb_jnt_grp, nurb_jnt = self.create_rig_joint(bind_jnt, parent_jnt_grp=self.jnt_grp, rad=0.25, add_elem='main', remove_elem='bnd')
					nurb_jnt = bb.create_node('joint', nurb_name, ['sec'], None, sub_side, radius = 0.6)
					nurb_jnt_offset_grp = bb.create_offset_group(nurb_jnt, ['offset', 'jnt'])
					nurb_jnt_grp = nurb_jnt_offset_grp[nurb_jnt][0]
					bb.snap([lip_rbn_ctrl], nurb_jnt_grp)
					#cmds.matchTransform(lip_rbn_ctrl, nurb_jnt_grp)
					cmds.parent(nurb_jnt_grp, local_nurb_grp)
					local_nurb_jnts.append(nurb_jnt)

					nurb_ctrl_grp, nurb_ctrl = self.create_controller(
													nurb_jnt, 
													'squareRound', 
													self.config['scale'] * 0.4, 
													[90, 0, 0], 
													self.config[f'{part}_move'], 
													'direct', 
													color_set = 'grp',
													ctrl_grp = local_nurb_ctrl_grp,
													side = sub_side
												)
					#cmds.setAttr(f'{nurb_ctrl_grp}.s', *scale_value)
					#cmds.setAttr(f'{nurb_jnt_grp}.s', *scale_value)
					main_lip_ctrl = self.lip_ctrls[i_part]

					main_ctrl = 'lip_upper_main_ctl' if is_upper else 'lip_lower_main_ctl'
					if num is None:
						bb.create_constrain([main_ctrl], nurb_ctrl_grp[0], 'parent')
					else:
						side_ctrl = f'{sub_side}_lip_corner_ctl'
						bb.create_constrain([main_ctrl, side_ctrl], nurb_ctrl_grp[0], 'parent')

