from importlib import reload
import maya.cmds as cmds
from .utils import rig_utils as bb
from .controllers import creator as bc
from .controllers import shape_color
from .naming import namer_factory as naming
from .naming import current_project
from .naming import parser
from . import bbIkRig as ik
from . import bbFkRig as fk
from . import bbRibbonRig as rbn

reload(bb)
reload(bc)
reload(naming)
reload(current_project)
reload(parser)
reload(ik)
reload(fk)
reload(rbn)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

FK_CTRL_SHAPE = 'crossCircle'
IK_CTRL_SHAPE = 'cube'
IK_PV_CTRL_SHAPE = 'diamond'
IK_END_CTRL_SHAPE = 'cube'
SETTING_CTRL_SHAPE = 'hexagon3d'

class FkIkRig:
	def __init__(self,
				joints = None,
				pole_vector_jnt = None, 
				setting_obj = None,
				rig_name = None,
				parts_name = [],
				side = None,
				stretch = True,
				squash = True,
				aim_axis = 'x',
				up_axis = 'z',
				rotate_order = 'zxy',
				connection_type = 'parent',
				scale = 1,
				color = None,
				feature = 'fkIk',
				stretch_attr = 'stretch',
				squash_attr = 'squash',
				global_scale = '',
				base_orient_loc = '',
				end_orient_loc = '',
				world_space = None,
				ctrl_parent =None,
				mod_parent = None,
				bind_parent ='',
				upper_driver = '',
				default_fkIk = 1,
				default_ik_base = 0,
				default_ik_pv = 1,
				default_ik_end = 1,
				create_bind_joint = True,
				rig_end_joint = False,
				base_parent_type = 'parent',
				**controller_kwargs
				):
		
		self.joints =  joints
		self.pole_vector_jnt =  pole_vector_jnt
		self.setting_obj =  setting_obj
		self.rig_name =  rig_name
		self.stretch =  stretch
		self.squash =  squash
		self.aim_axis =  aim_axis
		self.up_axis =  up_axis
		self.rotate_order =  rotate_order
		self.connection_type =  connection_type
		self.scale =  scale
		self.color =  color
		self.feature =  feature
		self.stretch_attr =  stretch_attr
		self.squash_attr =  squash_attr
		self.global_scale =  global_scale
		self.base_orient_loc =  base_orient_loc
		self.end_orient_loc =  end_orient_loc
		self.world_space =  world_space
		self.ctrl_parent =  ctrl_parent
		self.mod_parent =  mod_parent
		self.bind_parent =  bind_parent
		self.upper_driver =  upper_driver
		self.default_fkIk =  default_fkIk
		self.default_ik_base =  default_ik_base
		self.default_ik_pv =  default_ik_pv
		self.default_ik_end =  default_ik_end
		self.create_bind_joint =  create_bind_joint
		self.rig_end_joint =  rig_end_joint
		self.base_parent_type =  base_parent_type
		self.controller_kwargs =  controller_kwargs
	
		if side is None :
			self.side = parser.find_element(joints[0], 'sides')
		else:
			self.side =  side

		if self.color is None:
			formatted_side = parser.format_side(self.side, 'upper')
			color = shape_color.CTRL_COLOR.get(formatted_side, [0,5, 0.5, 0.5])
			self.color = color
		else: 
			self.color =  color 

		if not parts_name:
			self.parts_name = []
			for jnt in joints:
				base_name = parser.get_base_name(jnt)
				base_name = parser.clean_name(base_name, 'tmp')
				self.parts_name.append(base_name)
		else:
			self.parts_name =  parts_name
		
		self.up_vector = bb.axis_convert(up_axis, 'vector')
		default_shape_rotation = [item * 90 for item in self.up_vector]
		self.shape_rotation = controller_kwargs.get('shape_rotation', default_shape_rotation)
			
		self.ctrl_grp = None
		self.mod_grp = None
		self.bind_jnts = None
		self.ctrl_dict = {}

		self.fk_ctrls = None
		self.fk_grps = None

		self.ik_ctrls = None

		self._build()
		bb.over_and_out('FkIk Rig', f'{self.side}{self.rig_name}')
	
	def _build(self):
		self.ctrl_grp = bb.create_node('group', self.rig_name, [self.feature, 'ctrl'], None, self.side)
		self.mod_grp = bb.create_node('group', self.rig_name, [self.feature, 'mod'], None, self.side)
		self.jnt_grp = bb.create_node('group', self.rig_name, [self.feature, 'jnt'], None, self.side, p=self.mod_grp)

		generated_joints = bb.duplicate_joint_chain(self.joints[0], add_elements=['fk', 'ik', 'rig', 'bnd'], remove_element='tmp', ignore_jnts=[self.pole_vector_jnt, self.setting_obj])
		fk_jnts = generated_joints['fk']
		ik_jnts = generated_joints['ik']
		rig_jnts = generated_joints['rig']
		bind_jnts = generated_joints['bnd']

		cmds.parent(fk_jnts[0], ik_jnts[0], rig_jnts[0], self.jnt_grp)
		cmds.parent(bind_jnts[0], self.bind_parent)


		ik_rig = ik.IkRig( joints = ik_jnts,
						pole_vector_jnt = self.pole_vector_jnt,
						rig_name = self.rig_name,
						side = self.side,
						element_name = 'ik',
						stretch = self.stretch,
						squash = self.squash,
						aim_axis = self.aim_axis,
						up_axis = self.up_axis,
						ctrl_shape = IK_CTRL_SHAPE,
						ctrl_color = self.color,
						connection_type = self.connection_type,
						scale = self.scale,
						stretch_attr = self.stretch_attr,
						squash_attr = self.squash_attr,
						global_scale = self.global_scale,
						base_orient_loc = self.base_orient_loc,
						end_orient_loc = self.end_orient_loc,
						world_space = self.world_space,
						ctrl_parent = self.ctrl_grp,
						mod_parent = self.mod_grp,
						upper_driver = self.upper_driver,
						default_ik_base = self.default_ik_base,
						default_ik_pv = self.default_ik_pv,
						default_ik_end = self.default_ik_end,
						base_parent_type = self.base_parent_type
						)
		ik_ctrl_grp = ik_rig.ctrl_grp
		ik_mod_grps = ik_rig.mod_grp

		fk_rig = fk.FKRig( 
						joints=fk_jnts,
						rig_name = self.rig_name,
						element_name = 'fk',
						side = self.side,
						stretch = True,
						squash = True,
						aim_axis = self.aim_axis,
						up_axis = self.up_axis,
						shape = FK_CTRL_SHAPE,
						color = self.color,
						connection_type = 'None',
						ctrl_parent = self.ctrl_grp,
						scale = self.scale * 1.3,
						rotate_order = self.rotate_order,
						shape_rotation = self.shape_rotation ,
						rig_end_joint=self.rig_end_joint
						)
		fk_ctrl_grp = fk_rig.ctrl_grp
		fk_ctrls = fk_rig.ctrls	
		fk_grps = fk_rig.grps	

		if self.end_orient_loc:
			bb.snap([self.end_orient_loc], fk_grps[-1][0] )

		for ctrl, jnt in zip(fk_ctrls, fk_jnts):
			bb.create_constrain([ctrl], jnt, self.connection_type)
		
		if self.setting_obj == None:
			self.setting_obj = self.ctrl_parent

		if cmds.objectType(self.setting_obj) == 'joint':
			setting_controller = bc.Controller( 
								objects = [self.setting_obj],
								main_ctrl_grp = self.ctrl_grp,
								shape = SETTING_CTRL_SHAPE,
								color = 'orange',
								scale = self.scale * 0.4,
								line_width = 1.25,
								connection_type = 'None',
								shape_rotation = [0,0,0]
								)
			setting_ctrl = setting_controller.ctrls[0]
			setting_grp = setting_controller.offset_grps[0][0]
			bb.create_guide_curve(ctrl = setting_ctrl, target = rig_jnts[2], parent = self.ctrl_grp, curve_elem = '')
			self.setting_obj = setting_ctrl

		bb.attr_separator(ctrl=self.setting_obj )
		bb.fk_ik_switch(
			parents_fk = fk_jnts,
			parents_ik = ik_jnts,
			targets = rig_jnts,
			attr_name = 'fkIk',
			features = ['translation', 'rotation', 'scale'],
			ctrl = self.setting_obj,
			ik_ctrl_grp = ik_rig.ctrl_grp,
			fk_ctrl_grp = fk_rig.ctrl_grp,
			setup_name = self.rig_name,
			default_value = self.default_fkIk
			)
		
		for rig_jnt, bind_jnt in zip(rig_jnts, bind_jnts):
			bb.create_constrain([rig_jnt], bind_jnt, 'parentScale')
		
		self.bind_jnts = bind_jnts















