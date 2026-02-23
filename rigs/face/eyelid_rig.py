from importlib import reload
import maya.cmds as cmds
from . import base
from . import face_config
from ...core.utils import rig_utils as bb
from ...core.utils import skin_utils as sk
from ...core.naming import namer_factory as naming
from ...core.naming import current_project
from ...core.naming import parser

reload(bb)
reload(sk)
reload(base)
reload(face_config)
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
		
		upper_aim_loc = self.aim_loc
		upper_up_loc = cmds.duplicate(upper_aim_loc)[0]
		upper_up_loc = cmds.rename( upper_up_loc, upper_up_loc.replace('aim', 'up'))
		cmds.move(0, 3, 0, upper_up_loc, r=True)

		lower_aim_loc = cmds.duplicate(upper_aim_loc)[0]
		cmds.rotate(0, 0, -180, lower_aim_loc, r=True, os =True, fo=True)
		lower_up_loc = cmds.duplicate(lower_aim_loc)[0]
		lower_up_loc = cmds.rename( lower_up_loc, lower_up_loc.replace('aim', 'up'))
		cmds.move(0, -3, 0, lower_up_loc, r=True)


		aim_locs = [upper_aim_loc, lower_aim_loc]
		up_locs = [upper_up_loc, lower_up_loc]

		self.curves = [self.upper_curve, self.lower_curve]
		cmds.parent(self.curves, self.mod_grp)
		cv_count = bb.get_cv_count(self.curves[0])
		corner_cvs = [0, cv_count]

		# -------------------------------------------------------------------
		# Corners Ctrls
		# -------------------------------------------------------------------
		for i, elem in enumerate(self.config['corners_elem']):
			base_crnr_jnt_grp, base_crnr_jnt = self.create_rig_joint(self.aim_loc, add_elem=elem)
			tip_jnt = bb.create_node('joint', self.name, [elem, 'tip'], None, self.side)

			cv_posi = cmds.xform(f'{self.curves[0]}.cv[{corner_cvs[i]}]', ws=True, q=True, t=True)
			cmds.setAttr(f'{tip_jnt}.t', *cv_posi)
			cmds.parent(tip_jnt, base_crnr_jnt)

			shape_rotation = [0, 0, 90] if i == 0 else [0, 0, -90]
			move_val = cmds.xform(tip_jnt, os=True, q=True, t=True)
			self.corner_jnts.append(base_crnr_jnt)
			crnr_ctrl_grp, crnr_ctrl = self.create_controller(base_crnr_jnt, 
															self.ctrl_shape, 
															self.ctrl_scale, 
															shape_rotation,
															self.config['corner_move'][i],
															connection_type='direct'
														)
			spans = bb.get_cv_count(crnr_ctrl)
			cmds.move(*move_val, f'{crnr_ctrl}.cv[0:{spans}]', r=True, wd=True )
			cmds.setAttr(f'{crnr_ctrl}.sx', cb=False, k=False, l=True)
			cmds.setAttr(f'{crnr_ctrl}.sz', cb=False, k=False, l=True)
			self.corner_ctrls.append(crnr_ctrl)

		# -------------------------------------------------------------------
		# Upper/Lower ctrls
		# -------------------------------------------------------------------
		rig_crvs = [self.upper_curve, self.lower_curve ]
		for i_part, part in enumerate(['upper', 'lower']):
			ctrls = []
			grps = []
			part_ctrl_grp = bb.create_node('group', self.name, [part, 'ctrl'], None, self.side, p=self.ctrl_grp)
			part_mod_grp = bb.create_node('group', self.name, [part, 'mod'], None, self.side, p=self.mod_grp)
			part_jnt_grp = bb.create_node('group', self.name, [part, 'jnt'], None, self.side, p=part_mod_grp)
			rig_crv = rig_crvs[i_part]
			positions = []
			bnd_jnts = []
			jnt_count = bb.get_cv_count(self.curves[0]) - 1

			# -------------------------------------------------------------------
			# Tweakers Ctrls
			# -------------------------------------------------------------------
			for i in range(jnt_count):
				num = f'{i+1:02d}'
				npc = bb.create_node('nearestPointOnCurve', self.name, [part], num, self.side)
				cv_posi = cmds.xform(f'{rig_crv}.cv[{i+1}]', ws=True, q=True, t=True)
				cmds.connectAttr(f'{rig_crv}Shape.worldSpace[0]', f'{npc}.inputCurve')
				cmds.setAttr( f'{npc}.inPositionX', cv_posi[0])
				cmds.setAttr( f'{npc}.inPositionY', cv_posi[1])
				cmds.setAttr( f'{npc}.inPositionZ', cv_posi[2])
				parameter = cmds.getAttr(f'{npc}.parameter')
				
				poc = bb.create_node('pointOnCurveInfo', self.name, [part], num, self.side)
				jnt = bb.create_node('joint', self.name, [part], num, self.side, rad = 0.1)
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
				base_jnt_grp, base_jnt = self.create_rig_joint(aim_locs[i_part], add_elem=f'{part}_{elem}')
				tip_jnt = bb.create_node('joint', self.name, [part, elem, 'tip'], None, self.side, rad=0.3)

				val = ((cv_count-2)/(len(main_elems)+1)) * (i+1)
				cv_posi = cmds.xform(f'{rig_crv}.cv[{val}]', ws=True, q=True, t=True)
				cmds.setAttr( f'{tip_jnt}.t', *cv_posi)

				self.main_jnts.append(tip_jnt)
				self.curve_jnts.append(tip_jnt)
				cmds.parent(tip_jnt, base_jnt)
				cmds.parent(base_jnt_grp, part_mod_grp)
			
				color_set = 'sec'
				offset_names = ['Offset']
				shape_rotation = [0, 0, 0]
				
				if i != 1:
					offset_names = ['Offset', 'space']
					color_set = 'grp'
					jnt_space_grp = bb.create_offset_group([base_jnt], ['space_jnt'])
					jnt_space_grp = jnt_space_grp[base_jnt][0]
					jnt_space_grps.append(jnt_space_grp)

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
					cmds.addAttr( ctrl, ln = blink_attr, at = 'float' , min=0 , max=1 , dv=0 , k = True )
					cmds.setAttr(f'{ctrl}.sy', cb=False, k=False, l=True)
					cmds.setAttr(f'{ctrl}.sz', cb=False, k=False, l=True)

			self.main_tip_jnts.append(self.main_jnts)

			for i, ctrl in enumerate([ctrls[0], ctrls[2]]):
				parents_list = [[self.corner_ctrls[0], ctrls[1]], [self.corner_ctrls[1], ctrls[1]]]
				target_grps = [grps[0][1], grps[2][1]]
				bb.add_follow_attr(parents = parents_list[i], target = target_grps[i], attr_name = 'follow', ctrl = ctrl, min=0, max=1, dv=self.config['follow_dv'][i], multiply=False, connect_type='parent')
				#bb.create_constrain([target_grps[i]], jnt_space_grps[i])
				bb.direct_connect([target_grps[i]], [jnt_space_grps[i]])

			cmds.connectAttr(f'{ctrls[1]}.sx', f'{ctrls[0]}.sx')
			cmds.connectAttr(f'{ctrls[1]}.sx', f'{ctrls[2]}.sx')
			
			cmds.connectAttr(f'{self.corner_ctrls[0]}.sy', f'{ctrls[0]}.sy')
			cmds.connectAttr(f'{self.corner_ctrls[1]}.sy', f'{ctrls[2]}.sy')
			
			for ctrl in [ctrls[0], ctrls[2]]:
				for ax in 'xyz':
					cmds.setAttr(f'{ctrl}.s{ax}', cb=False, k=False, l=True)
			
		tmp_skcs, tmp_crvs = self._curve_skin_helper()
		for i, crv in enumerate(self.curves):
			crv_skc = sk.bind_skin(self.main_tip_jnts[i]+self.corner_jnts, crv)
			cmds.copySkinWeights(ss=tmp_skcs[i], ds=crv_skc, noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='closestJoint')
		cmds.delete(tmp_crvs)

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



































