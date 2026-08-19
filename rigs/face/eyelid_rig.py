from importlib import reload
import maya.cmds as cmds
from . import base
from . import face_config
from ...core.utils import rig_utils as bb
from ...core.utils import skin_utils as sk
from ...core.controllers import creator as bc
from ...core.naming import namer_factory as naming
from ...core.naming import current_project
from ...core.naming import parser

reload(bb)
reload(sk)
reload(base)
reload(face_config)
reload(bc)
reload(naming)
reload(current_project)
reload(parser)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

FaceModule = base.FaceModule

class EyelidRig(FaceModule):
	def __init__(self, 
				blueprint_grp = None, 
				name = 'eyelid',
				side='l',
				upper_curve = None,
				lower_curve = None,
				mid_curve = None,
				aim_loc = None,
				parent_ctrl_grp=None,
				parent_mod_grp=None,
				parent_jnt = None,
				remove_elem='bp'
				):
		super().__init__(name, side, parent_ctrl_grp, parent_mod_grp, remove_elem)
		self.blueprint_grp =  blueprint_grp
		self.name =  name
		self.side =  side
		self.upper_curve =  upper_curve
		self.lower_curve =  lower_curve
		self.mid_curve =  mid_curve
		self.aim_loc =  aim_loc
		self.parent_jnt =  parent_jnt

		self.curve_jnts = []
		self.corner_jnts = []
		self.corner_ctrls = []
		self.ctrls = []

		self.main_tip_jnts = []

		self.config = face_config.EYELIDS_SETTINGS
		self.ctrl_shape = face_config.EYELIDS_SETTINGS['lid_ctrl_shape']
		self.ctrl_scale = face_config.EYELIDS_SETTINGS['lid_ctrl_scale']

	def build(self):
		self.build_hierarchy(self.name, self.side)

		self.curves = [self.upper_curve, self.lower_curve]
		cv_count = bb.get_cv_count(self.curves[0])
		corner_cvs = [0, cv_count]
		cmds.parent(self.curves, self.mod_grp)
		cmds.parent(self.mid_curve, self.mod_grp)
		
		cmds.parent(self.jnt_grp, self.parent_jnt)

		# -------------------------------------------------------------------
		# Aim/Up Locators
		# -------------------------------------------------------------------
		loc_zro_grp = bb.create_node('group', self.name, ['loc_zro'], None, self.side, p=self.mod_grp)
		loc_grp = bb.create_node('group', self.name, ['loc'], None, self.side, p=loc_zro_grp)
		cmds.matchTransform(loc_zro_grp, self.parent_jnt)

		upper_aim_loc = self.aim_loc
		name = upper_aim_loc.replace('aim', 'up')
		upper_up_loc = cmds.duplicate(upper_aim_loc, n = name)[0]
		upper_up_loc = cmds.rename( upper_up_loc, upper_up_loc.replace('aim', 'up'))
		cmds.move(0, 3, 0, upper_up_loc, r=True)

		name = upper_aim_loc.replace('upper', 'lower')
		lower_aim_loc = cmds.duplicate(upper_aim_loc, n = name)[0]
		cmds.rotate(0, 0, -180, lower_aim_loc, r=True, os =True, fo=True)
		name = upper_aim_loc.replace('aim', 'up')
		lower_up_loc = cmds.duplicate(lower_aim_loc, n=name)[0]
		lower_up_loc = cmds.rename( lower_up_loc, lower_aim_loc.replace('aim', 'up'))
		cmds.move(0, -3, 0, lower_up_loc, r=True)

		aim_locs = [upper_aim_loc, lower_aim_loc]
		up_locs = [upper_up_loc, lower_up_loc]
		
		cmds.parent(aim_locs, loc_grp)
		cmds.parent(up_locs, loc_grp)
		bb.direct_connect([self.parent_jnt], [loc_grp])

		# -------------------------------------------------------------------
		# Corners Ctrls
		# -------------------------------------------------------------------
		for i, elem in enumerate(self.config['corners_elem']):
			base_crnr_jnt_grp, base_crnr_jnt = self.create_rig_joint(self.aim_loc, add_elem=elem, remove_elem='aim')
			tip_jnt = bb.create_node('joint', self.name, [elem, 'tip'], None, self.side)

			cv_posi = cmds.xform(f'{self.curves[0]}.cv[{corner_cvs[i]}]', ws=True, q=True, t=True)
			cmds.setAttr(f'{tip_jnt}.t', *cv_posi)
			cmds.parent(tip_jnt, base_crnr_jnt)

			shape_rotation = [0, 0, 90] if i == 0 else [0, 0, -90]
			self.corner_move_val = cmds.xform(tip_jnt, os=True, q=True, t=True)
			self.corner_jnts.append(base_crnr_jnt)
			crnr_ctrl_grp, crnr_ctrl = self.create_controller(base_crnr_jnt, 
															self.ctrl_shape, 
															self.ctrl_scale, 
															shape_rotation,
															self.config['corner_move'][i],
															connection_type='direct'
														)
			spans = bb.get_cv_count(crnr_ctrl)
			cmds.move(*self.corner_move_val, f'{crnr_ctrl}.cv[0:{spans}]', r=True, wd=True )
			cmds.setAttr(f'{crnr_ctrl}.sx', cb=False, k=False, l=True)
			cmds.setAttr(f'{crnr_ctrl}.sz', cb=False, k=False, l=True)
			self.corner_ctrls.append(crnr_ctrl)

		# -------------------------------------------------------------------
		# Upper/Lower ctrls
		# -------------------------------------------------------------------
		rig_crvs = [self.upper_curve, self.lower_curve ]
		self.upper_ctrls = []
		for i_part, part in enumerate(['upper', 'lower']):
			ctrls = []
			grps = []
			jnt_name = self.name + '_' + part
			part_ctrl_grp = bb.create_node('group', jnt_name, ['ctrl'], None, self.side, p=self.ctrl_grp)
			part_jnt_grp = bb.create_node('group', jnt_name, ['jnt'], None, self.side, p=self.mod_grp)
			rig_crv = rig_crvs[i_part]
			positions = []
			bnd_jnts = []
			jnt_count = bb.get_cv_count(self.curves[0]) - 1

			# -------------------------------------------------------------------
			# Tweakers Ctrls
			# -------------------------------------------------------------------
			for i in range(jnt_count):
				num = f'{i+1:02d}'
				npc = bb.create_node('nearestPointOnCurve', jnt_name, [], num, self.side)
				cv_posi = cmds.xform(f'{rig_crv}.cv[{i+1}]', ws=True, q=True, t=True)
				cmds.connectAttr(f'{rig_crv}Shape.worldSpace[0]', f'{npc}.inputCurve')
				cmds.setAttr( f'{npc}.inPositionX', cv_posi[0])
				cmds.setAttr( f'{npc}.inPositionY', cv_posi[1])
				cmds.setAttr( f'{npc}.inPositionZ', cv_posi[2])
				parameter = cmds.getAttr(f'{npc}.parameter')
				
				poc = bb.create_node('pointOnCurveInfo', jnt_name, [], num, self.side)
				jnt = bb.create_node('joint', jnt_name, [], num, self.side, rad = 0.1)
				cmds.setAttr( f'{poc}.turnOnPercentage', 1)
				cmds.setAttr( f'{poc}.parameter', parameter)
				cmds.connectAttr(f'{rig_crv}Shape.worldSpace[0]', f'{poc}.inputCurve')
				cmds.connectAttr(f'{poc}.position', f'{jnt}.t')
				cmds.delete(npc)

				cmds.aimConstraint(aim_locs[i_part], jnt, aim=(0,0,-1), u=(0,1,0), wut='object', wuo=up_locs[i_part])

				jnt_posi = cmds.getAttr(f'{poc}.position')
				positions.append(jnt_posi)
				bnd_jnts.append(jnt)

			cmds.parent(bnd_jnts, part_jnt_grp)

			# -------------------------------------------------------------------
			# Main Tweakers Ctrls
			# -------------------------------------------------------------------
			main_elems = ['in', 'mid', 'out']
			self.main_jnts = []
			jnt_space_grps = []
			for i, elem in enumerate(main_elems):
				base_jnt_grp, base_jnt = self.create_rig_joint(aim_locs[i_part], add_elem=f'{part}_{elem}', remove_elem='aim')
				tip_jnt = bb.create_node('joint', self.name, [part, elem, 'tip'], None, self.side, rad=0.3)

				#val = ((cv_count-2)/(len(main_elems)+1)) * (i+1)
				val = round(cv_count/4) * (i+1)
				cv_posi = cmds.xform(f'{rig_crv}.cv[{val}]', ws=True, q=True, t=True)
				cmds.setAttr( f'{tip_jnt}.t', *cv_posi)

				# poc = bb.create_node('pointOnCurveInfo', self.name, [part, elem, 'tip'], None, self.side)
				# pos_val = 0.25 * i
				# cmds.setAttr( f'{poc}.parameter', pos_val)
				# cmds.connectAttr(f'{rig_crv}.worldSpace[0]', f'{poc}.inputCurve')
				# cmds.connectAttr(f'{poc}.position', f'{tip_jnt}.t')
				#cmds.delete(poc)

				self.main_jnts.append(tip_jnt)
				self.curve_jnts.append(tip_jnt)
				cmds.parent(tip_jnt, base_jnt)

			
				color_set = 'sec'
				offset_names = ['Offset']
				shape_rotation = [0, 0, 0]
				
				if i != 1:
					#offset_names = ['Offset', 'space']
					color_set = 'grp'
					jnt_space_grps.append(base_jnt_grp)

				move_val = cmds.xform(tip_jnt, os=True, q=True, t=True)
				ctrl_grp, ctrl = self.create_controller(base_jnt, 
														self.ctrl_shape, 
														self.ctrl_scale, 
														shape_rotation, 
														self.config['main_tweakers_move'][i_part],
														connection_type='direct',
														color_set=color_set,
														offset_names=offset_names
													)
				spans = bb.get_cv_count(ctrl)
				cmds.move(*move_val, f'{ctrl}.cv[0:{spans}]', r=True, wd=True )
				ctrls.append(ctrl)
				grps.append(ctrl_grp)
				cmds.parent(ctrl_grp, part_ctrl_grp)

				if i_part == 0:
					self.upper_ctrls = ctrls

				# -------------------------------------------------------------------
				# Additional Attrs
				# -------------------------------------------------------------------

				bb.attr_separator(ctrl)
				for ax in 'xyz':
					cmds.setAttr(f'{ctrl}.t{ax}', l = True)
					cmds.setAttr(f'{ctrl}.t{ax}', k = False)

				z_scale_attr = 'z_depth'
				cmds.addAttr( ctrl, ln = z_scale_attr, at = 'float' , min=1 , max=2 , dv=1 , k = True )
				cmds.connectAttr(f'{ctrl}.{z_scale_attr}', f'{ctrl}.sz')	

				if i == 1:
					blink_attr = 'blink'
					cmds.addAttr( ctrl, ln = blink_attr, at = 'float' , min=-1 , max=1 , dv=0 , k = True )
					cmds.setAttr(f'{ctrl}.sy', cb=False, k=False, l=True)
					cmds.setAttr(f'{ctrl}.sz', cb=False, k=False, l=True)

			self.main_tip_jnts.append(self.main_jnts)

			for i, ctrl in enumerate([ctrls[0], ctrls[2]]):
				parents_list = [[self.corner_ctrls[0], ctrls[1]], [self.corner_ctrls[1], ctrls[1]]]
				target_grps = [grps[0][0], grps[2][0]]
				bb.add_follow_attr(parents = parents_list[i], target = target_grps[i], attr_name = 'follow', ctrl = ctrl, min=0, max=1, dv=self.config['follow_dv'][i], multiply=False, connect_type='parent')
				bb.direct_connect([target_grps[i]], [jnt_space_grps[i]])

			cmds.connectAttr(f'{ctrls[1]}.sx', f'{ctrls[0]}.sx')
			cmds.connectAttr(f'{ctrls[1]}.sx', f'{ctrls[2]}.sx')
			
			cmds.connectAttr(f'{self.corner_ctrls[0]}.sy', f'{ctrls[0]}.sy')
			cmds.connectAttr(f'{self.corner_ctrls[1]}.sy', f'{ctrls[2]}.sy')
			# -------------------------------------------------------------------
			# Curve Skin
			# -------------------------------------------------------------------
			crv_skc = sk.bind_skin(self.main_jnts+self.corner_jnts, self.curves[i_part])
			# -------------------------------------------------------------------
			# Blink Curve Blendshape
			# -------------------------------------------------------------------
			bsh_name =  NAMER.format(blink_attr, [part], None, self.side, 'bsh')
			cmds.blendShape(self.mid_curve, self.curves[i_part], tc = 0, n = bsh_name, foc=True)
			cmds.connectAttr(f'{ctrls[1]}.{blink_attr}', f'{bsh_name}.{self.mid_curve}')

			for ctrl in [ctrls[0], ctrls[2]]:
				for ax in 'xyz':
					cmds.setAttr(f'{ctrl}.s{ax}', cb=False, k=False, l=True)
			
		#tmp_skcs, tmp_crvs = self._curve_skin_helper()
		#cmds.copySkinWeights(ss=tmp_skcs[i], ds=crv_skc, noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='closestJoint')
		#cmds.delete(tmp_crvs)

	def _curve_skin_helper(self):
		tmp_skcs = []
		tmp_crvs = []
		for i_part, part in enumerate(['upper', 'lower']):
			tmp_skin_crv = cmds.duplicate(self.curves[i_part])[0]
			tmp_skin_crv = cmds.rebuildCurve(tmp_skin_crv, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=1, s=2, d=3, tol=0.01)[0]
			for i, jnt in enumerate(self.main_tip_jnts[i_part]):
				posi = cmds.xform(jnt, ws= True, q=True, t=True)
				cmds.xform(f'{tmp_skin_crv}.cv[{i+1}]', t=posi, ws=True)

			skc = sk.bind_skin(self.main_tip_jnts[i_part]+self.corner_jnts, tmp_skin_crv)
			tmp_skcs.append(skc)
			tmp_crvs.append(tmp_skin_crv)

		return tmp_skcs, tmp_crvs

	def add_eye_main_ctrl(self, center_obj = None, ctrl_grps = None, jnt_grps = None, skull_jnt = None, skull_ctrl = None, name = 'eye', color_set = 'sec'):
		'''
			Add main controller for eye squash and overall movement
			@ctrl_grps: list of control grps that will be squashed. eg. ['l_eyelid_ctrl_grp', 'l_eyesocket_ctrl_grp', 'l_lash_tweakers_setup_grp']
			@jnt_grps: list of joint grps that will be squashed. Eg. ['l_eyelid_drv_grp', 'l_eyesocket_jnt_grp']

		'''
		center_obj = center_obj if center_obj else self.aim_loc
		ctrl_grps = ctrl_grps if ctrl_grps else ['l_eyelid_ctrl_grp', 'l_eyesocket_ctrl_grp']#, 'l_lash_tweakers_setup_grp']
		jnt_grps = jnt_grps if jnt_grps else ['l_eyelid_drv_grp', 'l_eyesocket_jnt_grp']

		# Try query the parent of one of the ctrl grp
		ctrl_parent = cmds.listRelatives(ctrl_grps[0], p=True)[0]

		# Try query the parent of one of the jnt grp
		jnt_parent = cmds.listRelatives(jnt_grps[0], p=True)[0]

		skull_jnt = skull_jnt if skull_jnt else jnt_parent
		skull_ctrl = skull_ctrl if skull_ctrl else ctrl_parent

		main_ctrl_move_val = list(map(lambda x, y: x * y, self.corner_move_val, [2, 0, 2]))  

		eye_main_jnt = bb.create_node('joint', name, ['main'], None, self.side)
		eye_main_grp = bb.create_offset_group(eye_main_jnt, ['zro'])
		eye_main_grp = eye_main_grp[eye_main_jnt]
		cmds.matchTransform(eye_main_grp, center_obj)

		ctrl_grp, ctrl = self.create_controller(eye_main_jnt, 'sparkle', 0.5, [90, 0, 90], main_ctrl_move_val, 'direct', ['Main'], color_set = color_set, ctrl_grp = skull_ctrl)

		cmds.parent(ctrl_grps, ctrl)
		cmds.parent(jnt_grps, eye_main_jnt)
		cmds.parent(eye_main_grp, skull_jnt)

		return ctrl

	def eyelash_rig(self, curve=None, name='eyelash', side='l', eyelid_jnts_grp='l_eyelid_upper_jnt_grp', mod_ctrl_grp = None):
		'''
		Add child joint on eyelid rig for the similar primary movement with eyelid, and add eyelash controllers for sec movement
			num(int): numbers of eyelash ctrls
			curve(str): curve name from eyelid rig
			name(str): rig name
			side(str): rig side
			eyelid_jnts_grp(str): group of eyelid joints
		'''
		#main_ctrl_grp = bb.create_node('group', name, ['ctrl'], None, side, p=mod_ctrl_grp)
		num = 5
		format_side = parser.format_side(side, 'upper')
		ctrl_parents = [self.corner_ctrls[0], self.upper_ctrls[0], self.upper_ctrls[1], self.upper_ctrls[2], self.corner_ctrls[1]]
		ctrls = []
		ctrl_params = []

		curve_shp = cmds.listRelatives(curve, s=True)[0]
		
		# Create eyelash controllers 
		for i in range(0, num):
			ctrl_param = (1/(num-1)) * (i)
			mtp = bb.create_node('motionPath', name, [], f'{i+1:02d}', side)
			cmds.setAttr( f'{mtp}.uValue', ctrl_param)
			cmds.connectAttr(f'{curve_shp}.worldSpace[0]', f'{mtp}.geometryPath')

			tmp_loc = bb.create_node('locator', name, [], f'{i+1:02d}', side)
			cmds.connectAttr(f'{mtp}.allCoordinates', f'{tmp_loc}.translate')
			cmds.connectAttr(f'{mtp}.rotate', f'{tmp_loc}.rotate')

			controller = bc.Controller(
					objects=[tmp_loc],
					offset_names = ['ctrl'],
					shape='cube',
					color='lightGreen',
					scale=0.05,
					connection_type='None')
			ctrl = controller.ctrls[0]
			ctrl_grp = controller.offset_grps[0][0]

			cmds.setAttr( f'{mtp}.upAxis', 1)
			cmds.setAttr( f'{mtp}.frontAxis', 0)
			cmds.connectAttr(f'{mtp}.allCoordinates', f'{ctrl_grp}.translate')
			cmds.connectAttr(f'{mtp}.rotate', f'{ctrl_grp}.rotate')

			if format_side == 'R':
				cmds.setAttr( f'{mtp}.inverseFront', 1)

			cmds.disconnectAttr(f'{mtp}.allCoordinates', f'{ctrl_grp}.translate')
			cmds.disconnectAttr(f'{mtp}.rotate', f'{ctrl_grp}.rotate')
			cmds.parent(ctrl_grp, ctrl_parents[i])

			cmds.delete(tmp_loc)
			ctrls.append(ctrl)
			ctrl_params.append(ctrl_param)

		# Create eyelash joint under each eyelid joint
		lid_jnts = cmds.listRelatives(eyelid_jnts_grp, ad=True, type='joint')
		for i, jnt in enumerate(lid_jnts):
			jnt_num = ''.join(num for num in jnt if num.isdigit())
			lash_jnt = bb.create_node('joint', name, [], jnt_num, side, rad = 0.05)
			#cmds.setAttr(f'{lash_jnt}.displayLocalAxis', 1)
			lash_grp = bb.create_offset_group(lash_jnt, ['jnt'])
			lash_grp = lash_grp[lash_jnt][0]
			bb.set_color([lash_grp], color='lime', viewport=True, outliner=True)
			
			# Finding lash_jnt's position on curve
			jnt_npc = bb.create_node('nearestPointOnCurve', name, [], jnt_num, side)
			cmds.connectAttr(f'{curve_shp}.worldSpace[0]', f'{jnt_npc}.inputCurve')

			jnt_dcm = bb.create_node('decomposeMatrix', name, [], jnt_num, side)
			cmds.connectAttr(f'{jnt}.worldMatrix[0]', f'{jnt_dcm}.inputMatrix')
			cmds.connectAttr(f'{jnt_dcm}.outputTranslate', f'{jnt_npc}.inPosition')
			jnt_param = cmds.getAttr(f'{jnt_npc}.result.parameter')
			
			# Aim lash_jnt along the curve using motion path
			jnt_mtp = bb.create_node('motionPath', name, [], jnt_num, side)
			cmds.setAttr( f'{jnt_mtp}.uValue', jnt_param)
			cmds.connectAttr(f'{curve_shp}.worldSpace[0]', f'{jnt_mtp}.geometryPath')
			cmds.setAttr( f'{jnt_mtp}.upAxis', 1)
			cmds.setAttr( f'{jnt_mtp}.frontAxis', 0)
			if format_side == 'R':
				cmds.setAttr( f'{jnt_mtp}.inverseFront', 1)

			cmds.connectAttr(f'{jnt_mtp}.allCoordinates', f'{lash_grp}.translate')
			cmds.connectAttr(f'{jnt_mtp}.rotate', f'{lash_grp}.rotate')

			cmds.disconnectAttr(f'{jnt_mtp}.allCoordinates', f'{lash_grp}.translate')
			cmds.disconnectAttr(f'{jnt_mtp}.rotate', f'{lash_grp}.rotate')

			cmds.delete(jnt_npc, jnt_mtp)
			cmds.parent(lash_grp, jnt)

			# check if jnt_param is in between values in ctrl_params, return as start_ctrl, end_ctrl
			i = next(j for j, e in enumerate(ctrl_params) if e >= jnt_param)
			# print(ctrls[i-1])
			# print(ctrls[i])
			start_ctrl = ctrls[i-1]
			end_ctrl = ctrls[i]
			
			# Normalization value for blend attr 
			val_min = jnt_param - ctrl_params[i-1]
			max_min = ctrl_params[i] - ctrl_params[i-1]
			blend_val = val_min/max_min

			## —————————————————————————
			## Method using BlendColors
			# ctrls_blend_bcl = bb.create_node('blendColors', name, ['rot'], jnt_num, side)
			# cmds.connectAttr(f'{start_ctrl}.rotate', f'{ctrls_blend_bcl}.color2')
			# cmds.connectAttr(f'{end_ctrl}.rotate', f'{ctrls_blend_bcl}.color1')

			# cmds.setAttr( f'{ctrls_blend_bcl}.blender', blend_val)
			# cmds.connectAttr(f'{ctrls_blend_bcl}.output', f'{lash_jnt}.rotate')
			## —————————————————————————

			# Method using BlendMatrix
			start_ctrl_cpm = bb.create_node('composeMatrix', name, ['start_compose'], jnt_num, side)
			cmds.connectAttr(f'{start_ctrl}.t', f'{start_ctrl_cpm}.inputTranslate')
			cmds.connectAttr(f'{start_ctrl}.r', f'{start_ctrl_cpm}.inputRotate')
			cmds.connectAttr(f'{start_ctrl}.s', f'{start_ctrl_cpm}.inputScale')
			
			end_ctrl_cpm = bb.create_node('composeMatrix', name, ['end_compose'], jnt_num, side)
			cmds.connectAttr(f'{end_ctrl}.t', f'{end_ctrl_cpm}.inputTranslate')
			cmds.connectAttr(f'{end_ctrl}.r', f'{end_ctrl_cpm}.inputRotate')
			cmds.connectAttr(f'{end_ctrl}.s', f'{end_ctrl_cpm}.inputScale')

			blend_mtx = bb.create_node('blendMatrix', name, ['blend'], jnt_num, side)
			cmds.connectAttr(f'{start_ctrl_cpm}.outputMatrix', f'{blend_mtx}.target[0].targetMatrix')
			cmds.connectAttr(f'{end_ctrl_cpm}.outputMatrix', f'{blend_mtx}.target[1].targetMatrix')
			cmds.connectAttr(f'{blend_mtx}.outputMatrix', f'{lash_jnt}.offsetParentMatrix')
			cmds.setAttr( f'{blend_mtx}.target[1].weight', blend_val)
			


































