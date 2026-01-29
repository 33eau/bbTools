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

# reload(bb)
# reload(bsk)
# reload(bc)
# reload(shape_color)
# reload(naming)
# reload(templates)
# reload(current_project)
# reload(parser)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

FK_CTRL_SHAPE='crossCircle'

class FkSplineRig:
	def __init__(self, 
				joints=None,
				rig_name=None,
				element_name=None,
				side=None,
				aim_axis='y',
				up_axis='-z',
				num_mid_controls = 2,
				stretch=False,
				squash=False,
				offset_names=[],
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				global_scale = None,
				rig_on_provided_joints = False,
				scale=1.0,
				rotate_order = 'zxy',
				bind_parent ='',
				ctrl_parent ='',
				mod_parent = '',
				upper_driver = '',
				shape_rotation = None,
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
		self.global_scale =  global_scale
		self.rig_on_provided_joints =  rig_on_provided_joints
		self.scale = scale 
		self.rotate_order =  rotate_order
		self.bind_parent =  bind_parent
		self.ctrl_parent =  ctrl_parent
		self.mod_parent =  mod_parent
		self.upper_driver =  upper_driver
		self.shape_rotation =  shape_rotation
		self.controller_kwargs = controller_kwargs

		if not joints or not isinstance(joints, list) or len(joints) < 2:
			raise ValueError("The 'joints' argument must be a list of at least two joint names.")
		
		if self.num_mid_controls >= (len(self.joints)/2):
			cmds.warning(f'The amount of middle ctrls should be less than half of rig joints. Stretchy ik may pop when using mid ctrls.')

		if side is None:
			side = parser.find_element(self.joints[0], 'sides')
			self.side = side if side else 'M'
		else:
			self.side = side

		self.connection_type = 'parent'
		self.color =  'yellow' 
		self.subColor = 'green'	
		self.position_attr = 'position'
		
		self.mod_grp = None
		self.ctrl_grp = None
		self.bind_jnts = None
		
		self.ctrls = None
		self.grps = None

		self._build()
		bb.over_and_out('FkSplineRig', self.rig_name)
	
	def _build(self):
		self.ctrl_grp = bb.create_node('group', self.rig_name, ['Ctrl'], side = self.side )
		self.mod_grp = bb.create_node('group', self.rig_name, ['Mod'], side = self.side )
		self.mod_cons_grp = bb.create_node('group', self.rig_name, ['Mod', 'cons'], side = self.side, p = self.mod_grp )

		
		if not self.rig_on_provided_joints:
			element_names = ['Spline', 'Bnd']
			joints = bb.duplicate_joint_chain(self.joints, add_elements=element_names, remove_element='tmp')

		rig_jnts = joints[element_names[0]]
		self.bind_jnts = joints[element_names[1]]
		cmds.parent(rig_jnts[0], self.mod_cons_grp)

		ikh, eff, ik_crv = cmds.ikHandle(sj=rig_jnts[0], ee=rig_jnts[-1], sol='ikSplineSolver', pcv=False)
		ikh_name = NAMER.format(self.rig_name, ['Spline'], None, self.side, templates.TYPE_SUFFIX['ikHandle'])
		eff_name = NAMER.format(self.rig_name, ['Spline'], None, self.side, templates.TYPE_SUFFIX['ikEffector'])
		crv_name = NAMER.format(self.rig_name, ['Spline'], None, self.side, templates.TYPE_SUFFIX['nurbsCurve'])
		ikh = cmds.rename(ikh, ikh_name)
		eff = cmds.rename(eff, eff_name)

		cmds.rebuildCurve(ik_crv, ch=False, rpo=True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=self.num_mid_controls+1, d=1, tol=0.01 )
		ik_crv = cmds.rename(ik_crv, crv_name)
		cmds.parent(ik_crv, self.mod_grp)
		cmds.parent(ikh, self.mod_cons_grp)

		crv_jnt_grp = bb.create_node('group', self.rig_name, ['crv', 'jnt'], None, self.side, p= self.mod_cons_grp)
		cv_count = bb.get_cv_count(ik_crv)
		cv_joints = []
		if self.num_mid_controls > 1:
			for cv in range(0, cv_count+1):
				cmds.select(cl=True)
				position = cmds.xform(f'{ik_crv}.cv[{cv}]', ws=True, q = True, t=True)
				cv_jnt = bb.create_node('joint', self.rig_name, ['Spline', 'Crv'], number=f'{cv+1:02d}', side=self.side, p=position)
				cmds.makeIdentity(cv_jnt, a=True, r=True)
				cmds.parent(cv_jnt, crv_jnt_grp)
				cv_joints.append(cv_jnt)
		else:
			pos_parameters = [0.0, 0.5, 1.0]
			tmp_point_poc = bb.create_node('pointOnCurveInfo', 'temp', [], None, None)
			cmds.connectAttr(f'{ik_crv}Shape.worldSpace[0]', f'{tmp_point_poc}.inputCurve')
			for i in range(0, 3):
				cmds.setAttr( f'{tmp_point_poc}.parameter', pos_parameters[i])
				position = cmds.getAttr(f'{tmp_point_poc}.position')[0]
				cv_jnt = bb.create_node('joint', self.rig_name, ['Spline', 'Crv'], number=f'{i+1:02d}', side=self.side, p=position)
				cmds.parent(cv_jnt, crv_jnt_grp)
				cv_joints.append(cv_jnt)


		cmds.rebuildCurve(ik_crv, ch=False, rpo = True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=(self.num_mid_controls/2)+1, d=3, tol = 0.01 )
		curve_skc = cmds.skinCluster(cv_joints, ik_crv, tsb = True, mi=3, dr=2, rui=False, nw=0, bindMethod=0 )
		bsk.name_it(curve_skc)

		fk_controllers = bc.Controller(
						objects = cv_joints,
						main_ctrl_grp = self.ctrl_parent,
						name = self.rig_name,
						side = self.side,
						offset_names = ['Zro'],
						color = self.color,
						scale = self.scale * 1.2,
						fk_chain=True,
						connection_type = 'parent',
						rotate_order = self.rotate_order,
						shape_rotation = self.shape_rotation,
						**self.controller_kwargs
						)
		self.ctrls = fk_controllers.ctrls	
		self.grps = fk_controllers.offset_grps	

		cmds.parent(self.grps[0][0], self.ctrl_grp)
		cmds.parent(self.ctrl_grp, self.ctrl_parent)
		cmds.parent(self.mod_grp, self.mod_parent)
		cmds.parent(self.bind_jnts[0], self.bind_parent)
		if self.upper_driver:
			bb.create_constrain([self.upper_driver], self.ctrl_grp, 'parentScale')
			bb.create_constrain([self.upper_driver], self.mod_cons_grp, 'parentScale')

		for i, jnt in enumerate(rig_jnts):
			bb.matrix_constrain(jnt, self.bind_jnts[i])

