from importlib import reload
import maya.cmds as cmds
from .utils import rig_utils as bb
from .utils import skin_utils as bsk
from .controllers import creator as bc
from .controllers import shape_color
from .naming import namer_factory as naming
from .naming import templates
from .naming import current_project
from .naming import parser

reload(bb)
reload(bsk)
reload(bc)
reload(shape_color)
reload(naming)
reload(templates)
reload(current_project)
reload(parser)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

class SpineRig:
	def __init__(self, 
				joints=None,
				rig_name=None,
				element_name=None,
				side=None,
				aim_axis='y',
				up_axis='x',
				num_mid_controls = 2,
				stretch=False,
				squash=False,
				offset_names=[],
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				global_ctrl = None,
				rig_on_provided_joints = False,
				scale=1.0,
				**controller_kwargs
                ):

		self.joints = joints
		self.rig_name = rig_name
		self.element_name = element_name
		self.stretch = stretch
		self.squash = squash
		self.aim_axis =  aim_axis
		self.up_axis =  up_axis
		self.num_mid_controls =  num_mid_controls
		self.offset_names = offset_names
		self.stretch_attr =  stretch_attr
		self.squash_attr =  squash_attr
		self.global_ctrl =  global_ctrl
		self.rig_on_provided_joints =  rig_on_provided_joints
		self.scale = scale
		self.controller_kwargs = controller_kwargs

		if not joints or not isinstance(joints, list) or len(joints) < 2:
			raise ValueError("The 'joints' argument must be a list of at least two joint names.")
		
		if self.num_mid_controls >= (len(self.joints)/2):
			cmds.error(f'The amount of middle ctrls should be less than half of rig joints. Stretchy ik may pop when using.')

		if side is None:
			side = parser.find_element(self.joints[0], 'sides')
			self.side = side if side else 'M'
		else:
			self.side = side

		self.connection_type = 'parent'
		self.color =  'yellow' 
		self.subColor = 'green'	
		self.position_attr = 'position'
		
		self.module_grp = None
		self.controller_group = None
		self.bindJoints = None

		self._build()
		cmds.select(cl=True)
		print(f'Created\tSpineRig:\t{self.rig_name}')

	def _build(self):
		self.module_grp = bb.create_node('group', self.rig_name, ['Mod'], side = self.side )
		self.controller_grp = bb.create_node('group', self.rig_name, ['Ctrl'], side = self.side )

		ik_mod_grp = bb.create_node('group', self.rig_name, ['ik', 'Mod'], side=self.side)
		ik_ctrl_grp = bb.create_node('group', self.rig_name, ['ik', 'Ctrl'], side=self.side)
		bb.create_constrain([self.global_ctrl], ik_ctrl_grp, 'psc')

		if not self.rig_on_provided_joints:
			element_names = ['Spline', 'Bnd']
			joints = bb.duplicate_joint_chain(self.joints[0], add_elements=element_names, remove_element='Tmp')

		rig_jnts = joints[element_names[0]]
		cmds.parent(rig_jnts[0], ik_mod_grp)


		ikh, eff, ik_crv = cmds.ikHandle(sj=rig_jnts[0], ee=rig_jnts[-1], sol='ikSplineSolver', pcv=False)
		ikh_name = NAMER.format(self.rig_name, ['Spline'], None, self.side, templates.TYPE_SUFFIX['ikHandle'])
		eff_name = NAMER.format(self.rig_name, ['Spline'], None, self.side, templates.TYPE_SUFFIX['ikEffector'])
		crv_name = NAMER.format(self.rig_name, ['Spline'], None, self.side, templates.TYPE_SUFFIX['nurbsCurve'])
		ikh = cmds.rename(ikh, ikh_name)
		eff = cmds.rename(eff, eff_name)

		cmds.rebuildCurve(ik_crv, ch=False, rpo=True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=self.num_mid_controls+1, d=1, tol=0.01 )
		ik_crv = cmds.rename(ik_crv, crv_name)
		cmds.parent([ikh, ik_crv], ik_mod_grp)

		bind_joints = joints[element_names[1]]
		for i, jnt in enumerate(rig_jnts):
			cmds.connectAttr(f'{jnt}.t', f'{bind_joints[i]}.t')
			cmds.connectAttr(f'{jnt}.r', f'{bind_joints[i]}.r')
			cmds.connectAttr(f'{jnt}.s', f'{bind_joints[i]}.s')
			cmds.setAttr( f'{bind_joints[i]}.radius', self.scale * 3)
		cmds.delete(self.joints)
		
		cv_count = bb.get_cv_count(ik_crv)
		cv_joints = []
		for cv in range(0, cv_count+1):
			cmds.select(cl=True)
			position = cmds.xform(f'{ik_crv}.cv[{cv}]', ws=True, q = True, t=True)
			cv_jnt = bb.create_node('joint', self.rig_name, ['Spline', 'Crv'], number=f'{cv+1:02d}', side=self.side, p=position, rad=2)
			cmds.makeIdentity(cv_jnt, a=True, r=True)
			cv_joints.append(cv_jnt)

		base_jnt = cv_joints[0]
		top_jnt = cv_joints[-1]
		cmds.parent(cv_joints, ik_mod_grp)

		baseIk_ctrl = bc.Controller(
						objects = [base_jnt],
						main_ctrl_grp = ik_ctrl_grp,
						name = f'{self.rig_name}Base',
						side = self.side,
						offset_names = ['Zro','Position', 'Offset'],
						shape = 'chest',
						color = self.subColor,
						scale = self.scale,
						connection_type = self.connection_type,
						**self.controller_kwargs
						)
		base_ctrl = baseIk_ctrl.ctrls[0]
		base_grps = baseIk_ctrl.top_grps[0]

		topIk_ctrl = bc.Controller(
						objects = [top_jnt],
						main_ctrl_grp = ik_ctrl_grp,
						name = f'{self.rig_name}Top',
						side = self.side,
						offset_names = ['Zro','Position', 'Offset'],
						shape = 'chest',
						color = 'green',
						scale = self.scale,
						connection_type = self.connection_type,
						**self.controller_kwargs
						)
		
		top_ctrl = topIk_ctrl.ctrls[0]
		top_grps = topIk_ctrl.top_grps[0]

		# Ctrl Position Attr
		target_grps = [topIk_ctrl.top_grps[0][1], baseIk_ctrl.top_grps[0][1]]
		negative_grps = []
		for i, ctrl in enumerate([top_ctrl, base_ctrl]):
			target_ctrls = [top_ctrl, base_ctrl]
			ctrl_name, element, number, side, suffix = NAMER.extract(ctrl)
			destination_obj = target_ctrls
			destination_obj.remove(ctrl)
			cmds.matchTransform(ctrl, destination_obj)
			target_position = cmds.xform(ctrl, q =True, t=True, os=True)

			position_bcl = bb.create_node('blendColors', ctrl_name, element, number, self.side, )
			if i == 0:
				default = 'color1'
				result = 'color2'
				dv = 1
			else:
				default = 'color2'
				result = 'color1'
				dv = 0
			cmds.setAttr( f'{position_bcl}.{default}', 0,0,0)
			cmds.setAttr( f'{position_bcl}.{result}', *target_position)
			cmds.setAttr( f'{ctrl}.t', 0, 0, 0)
			cmds.addAttr( ctrl, ln = self.position_attr, at = 'float', min = 0, max = 1, dv = dv, k = True )
			cmds.connectAttr(f'{ctrl}.{self.position_attr}', f'{position_bcl}.blender')
			cmds.connectAttr(f'{position_bcl}.op', f'{target_grps[i]}.t')
			
			negative_grp = bb.create_node('group', ctrl_name, ['neg'], number, self.side, em=True)
			neg_mdv = bb.create_node('multiplyDivide', ctrl_name, element, number, self.side)
			cmds.connectAttr(f'{ctrl}.t', f'{neg_mdv}.i1')
			cmds.setAttr( f'{neg_mdv}.i2', -1,-1,-1)
			cmds.connectAttr(f'{neg_mdv}.o', f'{negative_grp}.t')
			cmds.parent(negative_grp, ctrl)
			negative_grps.append(negative_grp)
		topNeg_grp = negative_grps[0]
		baseNeg_grp = negative_grps[1]

		mid_joints = cv_joints[1:-1]
		mid_controllers = bc.Controller(
						objects = mid_joints,
						main_ctrl_grp = ik_ctrl_grp,
						name = self.rig_name,
						side = self.side,
						offset_names = ['Zro', 'Space', 'Offset'],
						shape = 'squareRound',
						color = f'light{self.subColor.capitalize()}',
						scale = self.scale * 0.6,
						connection_type = 'parentScale',
						**self.controller_kwargs
						)
		mid_ctrls = mid_controllers.ctrls
		mid_grps = mid_controllers.top_grps
		cmds.rebuildCurve(ik_crv, ch=False, rpo = True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=(self.num_mid_controls/2)+1, d=3, tol = 0.01 )
		curve_skc = cmds.skinCluster(cv_joints, ik_crv, tsb = True, mi=3, dr=2, rui=False, nw=0, bindMethod=0 )
		bsk.name_it(curve_skc)

		# Ik stretch
		feature = self.stretch_attr
		if 'auto' in feature:
			feature = feature.replace('auto', '')
		feature = feature.lower()

		curve_info = bb.create_node('curveInfo', self.rig_name, [feature], None, self.side)
		curve_shape = cmds.listRelatives(ik_crv, s=True)[0]
		cmds.connectAttr(f'{curve_shape}.worldSpace[0]', f'{curve_info}.inputCurve')
		original_length = cmds.getAttr(f'{curve_info}.arcLength')

		global_scale_mdv = bb.create_node('multiplyDivide', self.rig_name, [feature, 'scale'], None, self.side)
		cmds.connectAttr(f'{curve_info}.arcLength', f'{global_scale_mdv}.i1x')
		cmds.connectAttr(f'{self.global_ctrl}.s{self.aim_axis}', f'{global_scale_mdv}.i2x')
		cmds.setAttr(f'{global_scale_mdv}.op', 2 )

		dist_perc_mdv = bb.create_node('multiplyDivide', self.rig_name, [feature, 'dist'], None, self.side)
		cmds.connectAttr(f'{global_scale_mdv}.ox', f'{dist_perc_mdv}.i1x')
		cmds.setAttr( f'{dist_perc_mdv}.i2x', original_length )
		cmds.setAttr(f'{dist_perc_mdv}.op', 2 )

		cmds.addAttr( top_ctrl, ln = self.stretch_attr, at = 'float', min = 0, max = 1, dv = 1, k = True )

		strech_switch_bcl = bb.create_node('blendColors', self.rig_name, [feature, 'switch'], None, self.side)
		cmds.connectAttr(f'{dist_perc_mdv}.ox', f'{strech_switch_bcl}.c1r')
		#cmds.setAttr( f'{strech_switch_bcl}.c2r', 1)
		cmds.connectAttr(f'{top_ctrl}.{self.stretch_attr}', f'{strech_switch_bcl}.blender')

		# Squash Volume
		feature = self.squash_attr
		if 'auto' in feature:
			feature = feature.replace('auto', '')
		feature = feature.lower()

		squash_sqr_mdv = bb.create_node('multiplyDivide', self.rig_name, [feature, 'sqr'], None, self.side)
		cmds.connectAttr(f'{strech_switch_bcl}.opr', f'{squash_sqr_mdv}.i1x')
		cmds.setAttr( f'{squash_sqr_mdv}.i2x', 0.5 )
		cmds.setAttr(f'{squash_sqr_mdv}.op', 3 )

		squash_one_div_mdv = bb.create_node('multiplyDivide', self.rig_name, [feature, 'one', 'div'], None, self.side)
		cmds.setAttr( f'{squash_one_div_mdv}.i1x', 1)
		cmds.connectAttr(f'{squash_sqr_mdv}.ox', f'{squash_one_div_mdv}.i2x')
		cmds.setAttr(f'{squash_one_div_mdv}.op', 2 )

		cmds.addAttr( top_ctrl, ln = self.squash_attr, at = 'float', min = 0, max = 1, dv = 1, k = True )

		squash_switch_bcl = bb.create_node('blendColors', self.rig_name, [feature, 'switch'], None, self.side)
		cmds.connectAttr(f'{squash_one_div_mdv}.ox', f'{squash_switch_bcl}.c1r')
		cmds.setAttr( f'{squash_switch_bcl}.c2r', 1)
		cmds.connectAttr(f'{top_ctrl}.{self.squash_attr}', f'{squash_switch_bcl}.blender')

		result_scale_mdl = bb.create_node('multDoubleLinear', self.rig_name, [feature, 'result', 'scale'], None, self.side)
		cmds.connectAttr(f'{strech_switch_bcl}.opr', f'{result_scale_mdl}.i1')
		cmds.connectAttr(f'{self.global_ctrl}.sx', f'{result_scale_mdl}.i2')

		for rig_jnt in rig_jnts[1:]:
			base, element, number, _, _ = NAMER.extract(rig_jnt)
			orig_pos = cmds.getAttr(f'{rig_jnt}.t{self.aim_axis}')
			orig_pos_mdl = bb.create_node('multDoubleLinear', base, element + ['orig', 'pos'], number, self.side )
			cmds.setAttr( f'{orig_pos_mdl}.i1', orig_pos )
			cmds.connectAttr(f'{result_scale_mdl}.o', f'{orig_pos_mdl}.i2')

			output_stretch = cmds.getAttr(f'{orig_pos_mdl}.o')
			if round(output_stretch, 5) == round(orig_pos, 5):
				cmds.connectAttr(f'{orig_pos_mdl}.o', f'{rig_jnt}.t{self.aim_axis}')
			else:
				cmds.error(f'{self.stretch_attr} Output is not matching with the original position.\n\t output {output_stretch} : original {orig_pos}')
		for rig_jnt in rig_jnts:
			squash_axis = 'xyz'.replace(self.aim_axis, '')
			output_squash = cmds.getAttr(f'{squash_switch_bcl}.opr')
			if output_squash == 1:
				for ax in squash_axis:
					cmds.connectAttr(f'{squash_switch_bcl}.opr', f'{rig_jnt}.s{ax}')
			else:
				cmds.error(f'{self.squash_attr} Output is not 1 by default.')
			
		#Space Switch
		all_spaces_grp = bb.create_node('group', self.rig_name, ['spaces'], side=self.side )
		follow_type = ['point', 'orient']
		follow_attrs = ['followPosition', 'followRotation']
		for typ, attr in zip(follow_type, follow_attrs):
			for i, ctrl in enumerate(mid_ctrls):
				target_grp = mid_grps[i][1]
				space_grps = bb.space_switch(parentA = base_ctrl, parentB = top_ctrl , attr = attr, target_grp = target_grp, follow_type = typ, ctrl = ctrl)
				follow_value = (1/(len(mid_ctrls)+1)) * (i+1)
				cmds.setAttr( f'{ctrl}.{attr}', follow_value)
				cmds.parent(space_grps, all_spaces_grp)


### Example use:
# spine_rig = SpineRig(joints=None,
# 					rig_name=None,
# 					element_name=None,
# 					side=None,
# 					aim_axis='y',
# 					up_axis='x',
# 					num_mid_controls = 2,
# 					stretch=False,
# 					squash=False,
# 					offset_names=[],
# 					connection_type='parent',
# 					stretch_attr = 'stretch',
# 					squash_attr = 'squash',
# 					global_ctrl = None,
# 					rig_on_provided_joints = False,
# 					scale=1.0
# 					)


















