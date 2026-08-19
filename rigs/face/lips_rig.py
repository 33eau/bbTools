from importlib import reload
import maya.cmds as cmds
import maya.mel as mel
from . import base
from . import face_config
from ...core.utils import rig_utils as bb
from ...core.utils import skin_utils as sk
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
				remove_elem='bp',
				surface_rotation = True
				):
		super().__init__(name, side, parent_ctrl_grp, parent_mod_grp, remove_elem)
		self.blueprint_grp =  blueprint_grp
		self.default_shape =  default_shape
		self.name =  name
		self.side = side
		self.lip_jnts =  lip_jnts
		self.corner_jnts =  corner_jnts
		self.nurbs =  nurbs
		self.surface_rotation =  surface_rotation

		self.config = face_config.LIP_SETTINGS
		self.follow_attr = 'follow'
		self.corner_parents = ['skull_ctl', 'jaw_ctl']

		self.feature_name = ''

	def build(self):
		face_module = self.build_hierarchy(self.name, self.side)	

		self.lip_grps = []
		self.lip_ctrls = []

		self.lip_corner_grps = []
		self.lip_corner_ctrls = []
		self.lip_corner_jnt_grps = []

		self.lip_main_jnts = []

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
			self.lip_main_jnts.append(lip_jnt)
		
			lip_ctrl_grp = lip_ctrl_grp[0]
			if part == 'upper':
				bb.create_constraint([self.corner_parents[0]], lip_ctrl_grp)
			else:
				bb.create_constraint([self.corner_parents[1]], lip_ctrl_grp)
			bb.direct_connect([lip_ctrl_grp], [lip_jnt_grp])

		for jnt in self.corner_jnts:
			corner_jnt_grp, corner_jnt = self.create_rig_joint(jnt, parent_jnt_grp=self.jnt_grp, rad=0.25, offset_names=['jnt'])
			self.lip_corner_jnt_grps.append(corner_jnt_grp)
			follow_grp = bb.create_offset_group(corner_jnt, [self.follow_attr])
			follow_grp = follow_grp[corner_jnt][0]

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
			bb.direct_connect([corner_ctrl_grp[1]], [follow_grp])
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

			l_num = 0
			r_num = (round(subdivision/2))
			cmds.hide(follicle_grp)

			for i in range(0, subdivision):
				u_position = ((1/subdivision) * i) + (1/(subdivision*2))
				if u_position > 0.5:
					sub_side = 'l'
					l_num += 1
					#scale_value = [1, 1, 1]
					l_num = abs(l_num)
					num = f'{l_num:02d}'
				elif u_position < 0.5:
					sub_side = 'r'
					r_num -= 1
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
				if self.surface_rotation:
					point_jnt_grp, point_jnt = self.create_rig_joint(bind_jnt, parent_jnt_grp=self.jnt_grp, rad=0.25, add_elem = 'point')
					cmds.parent(point_jnt_grp, follicle_grp)
					bb.matrix_constrain(bind_jnt, point_jnt, channels = ['translate', 'scale'])
				else:
					cmds.disconnectAttr(f'{follicle_shp}.or', f'{follicle}.r')

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
						bb.create_constraint([main_ctrl], nurb_ctrl_grp[0], 'parent')
					else:
						side_ctrl = f'{sub_side}_lip_corner_ctl'
						bb.create_constraint([main_ctrl, side_ctrl], nurb_ctrl_grp[0], 'parent')

	def lip_zip_rig(self):
		'''

		Duplicate both upper and lower nurbs
		Copy skinweight from the main nurbs to each zipper nurb but add both upr&lwr
		Create blendshape from local nurb Post Def
		Add target 9 (cv) times 
		blendShape -e  -t lip_lower_nrb 9 lip_lower_zipper_nrb 1 lip_lower_zipper_bsh;
		weight each row 1 for each bsh target
		create zipper attr on corner ctrl
		
		'''
		fearture_name = 'zip'
		u, v = bb.get_nurb_info(self.nurbs[0])
		max_cv = max(u, v)
		num_vtx = bb.get_nurb_info(self.nurbs[0], num_vtx=True)

		for orig_nrb in self.nurbs:
			nurb_name = parser.get_base_name(orig_nrb)
			nurb_side = parser.find_element(orig_nrb, 'sides')
			is_upper = True if 'upper' in orig_nrb else False
			zip_nrb_name = NAMER.format(nurb_name, [fearture_name], None, nurb_side, 'nrb')
			zip_nrb = cmds.duplicate(orig_nrb)[0]
			zip_nrb = cmds.rename(zip_nrb, zip_nrb_name)
			#cmds.parent(zip_nrb, self.mod_grp)

			sk.copy_skin([zip_nrb, orig_nrb])
			zip_skc = sk.get_skin_cluster_name(zip_nrb)

			# ————————— Editing inf weight —————————
			host_joint = 'lip_upper_main_jnt' if is_upper else 'lip_lower_main_jnt'
			add_joint =  'lip_lower_main_jnt' if is_upper else 'lip_upper_main_jnt'
			infs = cmds.skinCluster(zip_skc, e=True, ai=add_joint, lw=True)

			infs = cmds.skinCluster(zip_skc, q=True, inf=True)
			# Lock other joints
			for inf in infs:
				cmds.setAttr(f'{inf}.liw', 1)
				
			cmds.select(zip_nrb)
			cmds.setToolTo('artAttrSkinContext')
			cmds.artAttrSkinPaintCtx('artAttrSkinContext', edit=True, sao='scale')
			cmds.setAttr(f'{add_joint}.liw', 0)
			cmds.setAttr(f'{host_joint}.liw', 0)
			cmds.artAttrSkinPaintCtx('artAttrSkinContext', edit=True, opacity=0.5)
			cmds.artAttrSkinPaintCtx('artAttrSkinContext', edit=True, value=0)

			SKIN_CLUSTER_INFLUENCE_LIST = 'theSkinClusterInflList'
			last_jnt = cmds.artAttrSkinPaintCtx('artAttrSkinContext', q=True, inf=True)
			mel.eval('artSkinInflListChanging "{}" 0'.format(last_jnt))
			cmds.treeView(SKIN_CLUSTER_INFLUENCE_LIST, edit=True, clearSelection=True)
			cmds.treeView(SKIN_CLUSTER_INFLUENCE_LIST, edit=True, selectItem=(host_joint, True))
			mel.eval('artSkinInflListChanging "{}" 1'.format(host_joint))
			mel.eval('artSkinInflListChanged artAttrSkinPaintCtx')
			mel.eval('refreshAE')
			mel.eval ("artAttrSkinPaintCtx -e -clear artAttrSkinContext")

			# ————————— Create blendshape and targets —————————
			bsh_name =  NAMER.format(nurb_name, [fearture_name], None, nurb_side, 'bsh')
			cmds.blendShape(zip_nrb, orig_nrb, tc = 0, n = bsh_name, bf=True)
			for i in range(num_vtx):
				attr = f'{bsh_name}.inputTarget[0].inputTargetGroup[0].targetWeights[{i}]'
				cmds.setAttr(attr, 0)
				for i in range(0, v):
					attr = f'{bsh_name}.inputTarget[0].inputTargetGroup[0].targetWeights[{i}]'
					cmds.setAttr(attr, 1)
				
			for cv_i in range(max_cv-1):
				next_index = cmds.blendShape(bsh_name, q=True, weightCount=True)
				cmds.blendShape( bsh_name, edit=True, t=(orig_nrb, next_index, zip_nrb, 1.0))
				weight_start = v * (cv_i+1)
				weight_end = v * (cv_i+2)
				
				for i in range(num_vtx):
					attr = f'{bsh_name}.inputTarget[0].inputTargetGroup[{next_index}].targetWeights[{i}]'
					cmds.setAttr(attr, 0)
				
				for i in range(weight_start, weight_end):
					attr = f'{bsh_name}.inputTarget[0].inputTargetGroup[{next_index}].targetWeights[{i}]'
					cmds.setAttr(attr, 1)
				
		sides = {
			'r': [0, 1, 2, 3, 4],
			'l': [9, 8, 7, 6, 5]
		}

		sections = ['upper', 'lower']
		driver_attr = 'zip'
		dv_steps = [0, 2, 4, 6, 8, 10]

		for side, indices in sides.items():
			crnr_ctrl = f'{side}_lip_corner_ctl'
			cmds.addAttr(crnr_ctrl, ln = driver_attr, min=0, max=10, dv=0, k=True)
			driver = f'{crnr_ctrl}.{driver_attr}'
				
			for section in sections:
				zip_bsh = f'lip_{section}_zip_bsh'
				zip_nrb_base = f'lip_{section}_zip_nrb'

				for i, target_idx in enumerate(indices):
					suffix = str(target_idx) if target_idx > 0 else ''
					driven = f'{zip_bsh}.{zip_nrb_base}{suffix}'
					activation_threshold = (i + 1) * 2
					
					for dv in dv_steps:
						val = 1 if dv >= activation_threshold else 0
						cmds.setDrivenKeyframe(driven, cd=driver, dv=dv, v=val)
