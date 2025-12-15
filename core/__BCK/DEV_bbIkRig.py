import maya.cmds as cmds
from bbTools.core.utils import rig_utils as bb
from bbTools.core.controllers import creator as bc
from bbTools.core.controllers import shape_library as ctrl_shapes
from bbTools.core.data import constants as constants
from bbTools.core.naming import namer_factory as naming
from bbTools.core.naming import current_project
from bbTools.core.naming import parser
reload(bb )
reload(bc)
reload(constants)
reload(naming)
reload(current_project)
reload(parser)

NAME_TEMPLATE = 'default'
NAMER = naming.get_namer(NAME_TEMPLATE)

joints = ['l_thigh_jnt', 'l_knee_jnt', 'l_ankle_jnt', 'l_ball_jnt']
rig_name = 'leg'
element_name = 'ik'
side = None
stretch = True
squash = True
aim_axis = 'x'
up_axis = 'z'
offset_names = ['offset']
ctrl_shape = 'crossSquare'
ctrl_color = 'sky'
connection_type = 'parent'
scale = 10
shape_rotation = [0, 0, 90]
feature_stretch = 'stretch'
feature_squash = 'squash'

SHAPE = 'cube'
CTRL_COLOR = constants.CTRL_COLOR
SCALE = 5

base, element, number, side, suffix = NAMER.extract(joints[0]) 
# module_grp = bb.create_node('group', base=rig_name, side=side)
# controller_grp = bb.create_node('group', base=rig_name, elements=['ctrl'], side=side)

# IK SYSTEM
base_names =[]
joint_positions = []
for jnt in joints:
	posi = cmds.xform(jnt, ws=True, q=True, t=True)
	joint_positions.append(posi)
	base_name = parser.get_base_name(jnt)
	base_names.append(base_name)
	

formatted_side = parser.format_side(side, 'upper')
COLOR = CTRL_COLOR[formatted_side]

ik_ctrl_grp = bb.create_node('group', base=rig_name, elements=[element_name, 'ctrl'], side=side)

cmds.setAttr( f'{joints[1]}.preferredAngle{up_axis.capitalize()}', 90)

node_name = NAMER.format(rig_name, ['ik'], number, side, 'ikh')
ikh, eff = cmds.ikHandle(sj=joints[0], ee=joints[2], n = node_name)
node_name = NAMER.format(rig_name, ['ik'], number, side, 'eff')
cmds.rename(eff, node_name)

ikh_end_controller = bc.Controller(objects = [ikh],
						name=rig_name+'_ik',
						side = side,
						offset_names = offset_names,
						main_ctrl_grp = ik_ctrl_grp,
						shape = SHAPE,
						color = COLOR,
						connection_type = connection_type,
						rotate_order = 'xyz',
						name_template=NAME_TEMPLATE,
						side_case='lower',
						scale = SCALE
						)
ik_end_ctrl = ikh_end_controller.ctrls[0]
ik_end_grp = ikh_end_controller.top_grps[0][0]

ik_base_controller = bc.Controller(objects = [joints[0]],
						side = side,
						offset_names = offset_names,
						main_ctrl_grp = ik_ctrl_grp,
						shape = SHAPE,
						color = COLOR,
						connection_type = 'None',
						rotate_order = 'xyz',
						shape_rotation = [0, 0, -90],
						name_template=NAME_TEMPLATE,
						side_case='lower',
						scale = SCALE
						)
ik_base_ctrl = ik_base_controller.ctrls[0]
ik_base_grp = ik_base_controller.top_grps[0][0]

node_name = NAMER.format(rig_name, ['pv'], number, side, 'loc')
pv_position_loc = bb.pole_vector_position(joints[:3], 0.5, create_locator=True)
pv_position_loc = cmds.rename(pv_position_loc, node_name)
ik_pv_controller = bc.Controller(objects = [pv_position_loc],
						offset_names = ['Offset'],
						main_ctrl_grp = ik_ctrl_grp,
						shape = 'diamond',
						color = COLOR,
						connection_type = 'None',
						rotate_order = 'xyz',
						shape_rotation = [0, 0, 0],
						name_template=NAME_TEMPLATE,
						side_case='lower',
						scale=SCALE
						)
ik_pv_ctrl = ik_pv_controller.ctrls[0]
cmds.delete(pv_position_loc)
cmds.poleVectorConstraint(ik_pv_ctrl, ikh)


ctrls = [ik_base_ctrl, ik_end_ctrl]
position_locators = []
for i, point in enumerate(['start', 'end']):
	loc = bb.create_node( node_type='locator', base=rig_name, elements=[feature_stretch, point], number=number, side=side, namer=NAMER)
	cmds.matchTransform(loc, ctrls[i])
	if NAME_TEMPLATE == 'hatrig':
		cmds.parent(loc, ctrls[i])
	else:
		bb.create_constrain( parents=[ctrls[i]], target=loc, type="parent")
	cmds.hide(loc)
	position_locators.append(loc)
base_loc = position_locators[0]
end_loc = position_locators[1]

real_time_distant_dbt = bb.create_node( node_type='distanceBetween', base=rig_name, elements=[feature_stretch], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{base_loc}.worldPosition[0]',  f'{real_time_distant_dbt}.p1')
cmds.connectAttr(f'{end_loc}.worldPosition[0]',  f'{real_time_distant_dbt}.p2')
distance = cmds.getAttr(f'{real_time_distant_dbt}.distance')

dist_perc_mdv = bb.create_node( node_type='multiplyDivide', base=rig_name, elements=['dist', 'perc'], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{real_time_distant_dbt}.distance', f'{dist_perc_mdv}.i1x')
cmds.setAttr(f'{dist_perc_mdv}.op', 2 )

attr_name = 'auto' + feature_stretch.capitalize()
mannual_attr = 'mannual' + feature_stretch.capitalize()
bb.attr_separator(ik_end_ctrl, ln='extraAttr')
cmds.addAttr( ik_end_ctrl, ln = attr_name, at = 'float', min = 0, max = 1, dv = 1, k = True )
cmds.addAttr( ik_end_ctrl, ln = mannual_attr, at = 'float', min = -1, max = 10, dv = 1, k = True )

feature_switch = bb.create_node( node_type='blendColors', base=rig_name, elements=[feature_stretch], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{ik_end_ctrl}.{attr_name}', f'{feature_switch}.blender')
cmds.connectAttr(f'{dist_perc_mdv}.ox', f'{feature_switch}.c1r')
cmds.setAttr( f'{feature_switch}.c2', 1,1,1 )

mannual_mdl = bb.create_node( node_type='multDoubleLinear', base=rig_name, elements=[feature_stretch], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{ik_end_ctrl}.{mannual_attr}', f'{mannual_mdl}.i2')
cmds.connectAttr(f'{feature_switch}.opr', f'{mannual_mdl}.i1')

bend_cdt = bb.create_node( node_type='condition', base=rig_name, elements=[feature_stretch], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{real_time_distant_dbt}.distance', f'{bend_cdt}.ft')
cmds.setAttr(f'{bend_cdt}.op', 2 )
cmds.connectAttr(f'{mannual_mdl}.o', f'{bend_cdt}.ctr')
cmds.connectAttr(f'{ik_end_ctrl}.{mannual_attr}', f'{bend_cdt}.cfr')

upper_len = cmds.getAttr(f'{joints[1]}.t{aim_axis}')
lower_len = cmds.getAttr(f'{joints[2]}.t{aim_axis}')
total_len = upper_len+lower_len
cmds.setAttr( f'{bend_cdt}.st', total_len)
cmds.setAttr( f'{dist_perc_mdv}.i2x', total_len)

if NAME_TEMPLATE == 'hatrig':
	for jnt in joints[:2]:
		cmds.connectAttr(f'{bend_cdt}.ocr', f'{jnt}.s{aim_axis}')
else:
	for jnt in joints[1:3]:
		base_name = parser.get_base_name(jnt)
		original_posi = cmds.getAttr(f'{jnt}.t{aim_axis}')
		original_posi_mdl = bb.create_node(node_type='multDoubleLinear', base=base_name, elements=[feature_stretch], number=number, side=side)
		cmds.setAttr( f'{original_posi_mdl}.i1', original_posi)
		cmds.connectAttr(f'{bend_cdt}.ocr', f'{original_posi_mdl}.i2')
		cmds.connectAttr(f'{original_posi_mdl}.o', f'{jnt}.t{aim_axis}')

# Squash
power_mdv = bb.create_node( node_type='multiplyDivide', base=rig_name, elements=[feature_squash, 'power'], number=number, side=side, namer=NAMER)
cmds.setAttr(f'{power_mdv}.op', 3 )
cmds.setAttr( f'{power_mdv}.i2x', 0.5)
cmds.connectAttr(f'{bend_cdt}.ocr', f'{power_mdv}.i1x')

one_div_mdv = bb.create_node( node_type='multiplyDivide', base=rig_name, elements=[feature_squash, 'one', 'div'], number=number, side=side, namer=NAMER)
cmds.setAttr( f'{one_div_mdv}.i1x', 1)
cmds.setAttr(f'{one_div_mdv}.op', 2 )
cmds.connectAttr(f'{power_mdv}.ox', f'{one_div_mdv}.i2x')

attr_name = 'auto' + feature_squash.capitalize()
cmds.addAttr( ik_end_ctrl, ln = attr_name, at = 'float', min = 0, dv = 1, k = True )

sq_switch = bb.create_node( node_type='blendColors', base=rig_name, elements=[feature_squash], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{ik_end_ctrl}.{attr_name}', f'{sq_switch}.blender')
cmds.connectAttr(f'{one_div_mdv}.ox', f'{sq_switch}.c1r')
cmds.setAttr( f'{sq_switch}.c2r', 1)
cmds.setAttr( f'{sq_switch}.c2', 1,1,1 )

scale_axes = 'xyz'.replace(aim_axis, '')
for jnt in joints:
	for ax in scale_axes: 
		cmds.connectAttr(f'{sq_switch}.opr', f'{jnt}.s{ax}')



