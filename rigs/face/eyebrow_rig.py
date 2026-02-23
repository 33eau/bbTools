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

class EyebrowRig(FaceModule):
	def __init__(self, 
				blueprint_grp = None, 
				default_shape='crossCircle',
				name = 'eyebrow',
				side=None,
				eyebrow_jnts = ['l_eyebrow_in_bp_jnt', 'l_eyebrow_in_aux_bp_jnt', 'l_eyebrow_mid_aux_bp_jnt', 'l_eyebrow_mid_bp_jnt', 'l_eyebrow_out_aux_bp_jnt', 'l_eyebrow_out_bp_jnt'],
				eyebrow_main_jnt = 'l_eyebrow_main_bp_jnt',
				curve  = 'l_eyebrow_crv',
				parent_ctrl_grp=None,
				parent_mod_grp=None,
				remove_elem='bp'
				):
		super().__init__(name, side, parent_ctrl_grp, parent_mod_grp, remove_elem)
		self.blueprint_grp =  blueprint_grp
		self.default_shape =  default_shape
		self.name =  name
		self.side =  side
		self.eyebrow_jnts =  eyebrow_jnts
		self.eyebrow_main_jnt =  eyebrow_main_jnt
		self.curve =  curve

		self.config = face_config.EYEBROWS_SETTINGS

		self.ctrls = []
		self.grps = []
		self.aux_ctrls = []
		self.aux_grps = []
	
	def build(self):
		self.build_hierarchy(self.name, self.side)
		cmds.parent(self.curve, self.mod_grp)

		main_jnt_grp, main_jnt = self.create_rig_joint(self.eyebrow_main_jnt, rad = 0.4)
		main_ctrl_grp, main_ctrl = self.create_controller(main_jnt,
													'eyebrow',
													0.35,
													[0, 0, 0],
													[0, 0, 0],
													'direct',
													ctrl_grp = self.ctrl_grp
													)

		for jnt in self.eyebrow_jnts:
			rig_jnt_grp, rig_jnt = self.create_rig_joint(jnt, rad = 0.3)
			#cmds.parent(rig_jnt_grp, main_jnt)
			if 'aux' in jnt:
				aux_ctrl_grp, aux_ctrl = self.create_controller(rig_jnt,
													self.default_shape,
													0.075,
													self.config['ctrl_rotate'],
													[0, 0, 0.3],
													'direct',
													ctrl_grp = self.ctrl_grp,
													color_set = 'ter'
													)
				bb.direct_connect([aux_ctrl_grp[0]], [rig_jnt_grp])
				#bb.create_constrain([aux_ctrl_grp[0]], rig_jnt_grp, 'pac')
				self.aux_grps.append(aux_ctrl_grp[0])
				self.aux_ctrls.append(aux_ctrl)
			else:
				part_ctrl_grp, part_ctrl = self.create_controller(rig_jnt,
													self.default_shape,
													0.09,
													self.config['ctrl_rotate'],
													[0, 0, 0.3],
													'direct',
													ctrl_grp = main_ctrl,
													color_set = 'grp'
													)
				bb.direct_connect([part_ctrl_grp[0]], [rig_jnt_grp])
				#bb.create_constrain([part_ctrl_grp[0]], rig_jnt_grp, 'pac')
				self.grps.append(part_ctrl_grp)
				self.ctrls.append(part_ctrl)
			
			
		for i, aux in enumerate(self.aux_grps):
			if i == 0:
				parents = [self.ctrls[1], self.ctrls[0]]
			elif i == 1:
				parents = [self.ctrls[0], self.ctrls[1]]
			else:
				parents = [self.ctrls[1], self.ctrls[2]]
			part = self.config['part'][i]
			attr_name = f'follow_{part}'

			bb.add_follow_attr(parents=parents, target=aux, attr_name=attr_name, ctrl=self.aux_ctrls[i], min=0, max=1, dv=self.config['default_values'][i], multiply=False)

		bind_jnt_grp = bb.create_node('group', self.name, ['bnd'], None, self.side, p=self.jnt_grp)
		bb.set_color(objects=[bind_jnt_grp], color='pink', viewport=True, outliner=True)
		point_jnt_grp = bb.create_node('group', self.name, ['point'], None, self.side, p=self.jnt_grp)
		bb.set_color(objects=[point_jnt_grp], color='lime', viewport=True, outliner=True)

		cv_count = bb.get_cv_count(self.curve)
		curve_shp = cmds.listRelatives(self.curve, s=True)[0]

		for i in range(cv_count+1):
			if i == 1:
				# Skip creating cv[1] since it's too close to the beginning
				continue
			num = f'{i+1:02d}' if i == 0 else f'{i:02d}'
			bnd_jnt = bb.create_node('joint', self.name, None, num, self.side, rad=0.2)
			bnd_jnt_grp = bb.create_offset_group(bnd_jnt, ['jnt'])
			bnd_jnt_grp = bnd_jnt_grp[bnd_jnt][0]
			cv_posi = cmds.xform(f'{curve_shp}.cv[{i}]', q=True, t=True, ws=True)
			cmds.setAttr(f'{bnd_jnt_grp}.t', *cv_posi)
			bb.set_color(objects=[bnd_jnt], color='lightPink', viewport=True, outliner=True)

			bind_npc = bb.create_node('nearestPointOnCurve', self.name, ['bnd'], num, self.side)
			cmds.connectAttr(f'{curve_shp}.worldSpace[0] ', f'{bind_npc}.inputCurve')
			cmds.connectAttr(f'{bnd_jnt_grp}.t', f'{bind_npc}.inPosition')
			parameter = cmds.getAttr(f'{bind_npc}.parameter')
			cmds.delete(bind_npc)

			bind_mtp = bb.create_node('motionPath', self.name, ['bnd'], num, self.side)
			cmds.setAttr(f'{bind_mtp}.uValue', parameter)
			cmds.connectAttr(f'{curve_shp}.worldSpace[0] ', f'{bind_mtp}.geometryPath')
			cmds.connectAttr(f'{bind_mtp}.allCoordinates ', f'{bnd_jnt_grp}.t')
			cmds.connectAttr(f'{bind_mtp}.r ', f'{bnd_jnt_grp}.r')

			poi_jnt = bb.create_node('joint', self.name, ['point'], num, self.side, rad=0.1)
			poi_jnt_grp = bb.create_offset_group([poi_jnt])
			poi_jnt_grp = poi_jnt_grp[poi_jnt][0]
			bb.snap([bnd_jnt_grp], poi_jnt_grp)
			bb.set_color(objects=[poi_jnt_grp], color='lightLime', viewport=True, outliner=True)

			bb.direct_connect([bnd_jnt_grp], [poi_jnt_grp], channels = ['translate'])
			
			cmds.parent(bnd_jnt_grp, bind_jnt_grp)
			cmds.parent(poi_jnt_grp, point_jnt_grp)

	def add_mid_ctrl(self, l_in_ctrl, r_in_ctrl, mid_ctrl ):
		grp_dic = bb.create_offset_group(mid_ctrl, ['ctrl_follow'])
		mid_grp = grp_dic[mid_ctrl][0]
		bb.add_follow_attr(parents=[r_in_ctrl, l_in_ctrl], target=mid_grp, ctrl = mid_ctrl)

		jnt = cmds.listConnections(mid_ctrl, c=True, type='joint', s=True)[-1]
		jnt_grp_dic = bb.create_offset_group(jnt, ['jnt_follow'])
		jnt_mid_grp = jnt_grp_dic[jnt][0]
		bb.direct_connect([mid_grp], [jnt_mid_grp])

		return


		
		