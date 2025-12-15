path = 'W:/RIG/PROJ/MAYA_PROJ/HATRIG/scenes/week04_Apissara_leg_start.ma'
cmds.file(path, o=True, f=True )
from importlib import reload
import maya.cmds as cmds

from .utils import rig_utils as bb
from .controllers import creator as bc
from .data import constants 
from .naming import namer_factory as naming
from .naming import parser
from .naming import current_project

reload(bb )
reload(bc)
reload(constants)
reload(naming)
reload(parser)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

blueprint_joints = ['l_thigh_tmp_jnt', 'l_knee_tmp_jnt', 'l_ankle_tmp_jnt', 'l_ball_tmp_jnt', 'l_ball_tip_tmp_jnt']
aim_axis = 'y'
up_axis = 'x'
rig_name = 'leg'
feature_stretch = 'stretch'
feature_squash = 'volume'

fkIk_attr_name = 'fkIk'

side = parser.find_element(blueprint_joints[0], 'sides')
formatted_side = parser.format_side(side,'upper')
COLOR = constants.CTRL_COLOR[formatted_side]

cmds.hide(blueprint_joints)
joint_chains = bb.duplicate_joint_chain(top_joint=blueprint_joints[0], add_elements=['ik', 'fk', 'drv'], remove_element='tmp', radius = 1.0, color = None)

ik_joints = joint_chains['ik']
fk_joints = joint_chains['fk']
drv_joints = joint_chains['drv']

module_grp = bb.create_node('group', base=rig_name, side=side)
controller_grp = bb.create_node('group', base=rig_name, elements=['ctrl'], side=side, p=module_grp)
joint_grp = bb.create_node('group', base=rig_name, elements=['jnt'], side=side, p=module_grp)
cmds.parent(ik_joints[0], fk_joints[0], drv_joints[0], joint_grp)


# FK SYSTEM
fk_ctrl_grp = bb.create_node('group', base=rig_name, elements=['fk'], side=side, p =controller_grp)

fk_controller = bc.Controller(objects = fk_joints,
						main_ctrl_grp = fk_ctrl_grp,
						name = '',
						side = '',
						offset_names = ['orient', 'offset'],
						shape = 'crossCircle',
						color = COLOR,
						scale = 1.5,
						line_width = 1,
						gimbal = False,
						connection_type = 'None',
						rotate_order = 'xyz',
						lock_attrs = None,
						shape_rotation = [0,0,0],
						temp = False,
						fk_chain = False,
						name_template=NAME_TEMPLATE,
						side_case='lower',
						)

fk_ctrls = fk_controller.ctrls
fk_ori_groups = fk_controller.top_grps
fk_grps = []
for i, grps in enumerate(fk_ori_groups):
	cmds.setAttr( f'{grps[1]}.rx', 180)
	cmds.parent(grps[1], w=True)
	cmds.delete(grps[0])
	if i >= 2:
		cmds.setAttr( f'{grps[1]}.r', 0,0,0)
	if i > 0:
		cmds.parent(grps[1], fk_ctrls[i-1])
	bb.create_constrain([fk_ctrls[i]], fk_joints[i])
	i+=1
cmds.parent(fk_ori_groups[0][1], fk_ctrl_grp)

# IK SYSTEM
base_names =[]
joint_positions = []
for jnt in ik_joints:
	posi = cmds.xform(jnt, ws=True, q=True, t=True)
	joint_positions.append(posi)
	base_name = parser.get_base_name(jnt)
	base_names.append(base_name)

base, element, number, side, suffix = NAMER.extract(ik_joints[0]) 

ik_ctrl_grp = bb.create_node('group', base=rig_name, elements=['ik'], side=side, p=controller_grp)

cmds.setAttr( f'{ik_joints[1]}.preferredAngle{up_axis.capitalize()}', 90)
node_name = NAMER.format(rig_name, ['ik'], number, side, 'ikh')
ikh, eff = cmds.ikHandle(sj=ik_joints[0], ee=ik_joints[2], n = node_name)
node_name = NAMER.format(rig_name, ['ik'], number, side, 'eff')
cmds.rename(eff, node_name)

ikh_end_controller = bc.Controller(objects = [ikh],
						name=rig_name+'_ik',
						side = side,
						offset_names = ['Offset'],
						main_ctrl_grp = ik_ctrl_grp,
						shape = 'cube',
						color = COLOR,
						connection_type = 'None',
						rotate_order = 'xyz',
						name_template=NAME_TEMPLATE,
						side_case='lower',
						)
ik_end_ctrl = ikh_end_controller.ctrls[0]
ik_end_grp = ikh_end_controller.top_grps[0][0]

ik_base_controller = bc.Controller(objects = [ik_joints[0]],
						offset_names = ['Offset'],
						main_ctrl_grp = ik_ctrl_grp,
						shape = 'stickSphere',
						color = COLOR,
						connection_type = 'None',
						rotate_order = 'xyz',
						shape_rotation = [0, 0, -90],
						name_template=NAME_TEMPLATE,
						side_case='lower',
						)
ik_base_ctrl = ik_base_controller.ctrls[0]
ik_base_grp = ik_base_controller.top_grps[0][0]
# cmds.parent(ikh, ik_end_ctrl)

node_name = NAMER.format(base_names[2], ['ik'], number, side, 'ikh')
ankle_ikh, ankle_eff = cmds.ikHandle(sj=ik_joints[2], ee=ik_joints[3], n = node_name)
node_name = NAMER.format(base_names[2], ['ik'], number, side, 'eff')
cmds.rename(ankle_eff, node_name)

node_name = NAMER.format(base_names[3], ['ik'], number, side, 'ikh')
ball_ikh, ball_eff = cmds.ikHandle(sj=ik_joints[3], ee=ik_joints[4], n = node_name)
node_name = NAMER.format(base_names[3], ['ik'], number, side, 'eff')
cmds.rename(ball_eff, node_name)
cmds.parent([ankle_ikh, ball_ikh], ik_end_ctrl)

ik_ball_controller = bc.Controller(objects = [ik_joints[3]],
						offset_names = ['Offset'],
						main_ctrl_grp = ik_end_ctrl,
						shape = 'cube',
						color = 'dark' + COLOR.capitalize(),
						connection_type = 'None',
						rotate_order = 'xyz',
						shape_rotation = [0, 0, 0],
						name_template=NAME_TEMPLATE,
						side_case='lower',
						)
ik_ball_ctrl = ik_ball_controller.ctrls[0]
cmds.parent([ankle_ikh, ikh], ik_ball_ctrl)

ik_toe_controller = bc.Controller(objects = [ik_joints[3]],
						offset_names = ['Offset'],
						name = 'toe_ik',
						side=side,
						main_ctrl_grp = ik_end_ctrl,
						shape = 'cube',
						color = 'deep' + COLOR.capitalize(),
						connection_type = 'None',
						rotate_order = 'xyz',
						shape_rotation = [0, 0, 0],
						name_template=NAME_TEMPLATE,
						side_case='lower',
						)
ik_toe_ctrl = ik_toe_controller.ctrls[0]
cmds.parent([ball_ikh], ik_toe_ctrl)

pole_vector_jnt = bb.create_node('joint', base=rig_name, elements=['pv'], side=side, p=joint_positions[1])
cmds.move(0,0,25, pole_vector_jnt, r=True)

ik_pv_controller = bc.Controller(objects = [pole_vector_jnt],
						offset_names = ['Offset'],
						main_ctrl_grp = ik_ctrl_grp,
						shape = 'diamond',
						color = COLOR,
						connection_type = 'None',
						rotate_order = 'xyz',
						shape_rotation = [0, 0, 0],
						name_template=NAME_TEMPLATE,
						side_case='lower',
						)
ik_pv_ctrl = ik_pv_controller.ctrls[0]
cmds.delete(pole_vector_jnt)
cmds.poleVectorConstraint(ik_pv_ctrl, ikh)

setting_jnt = bb.create_node('joint', base=rig_name, elements=['setting'], side=side, p=joint_positions[2])
cmds.move(10,0,0, setting_jnt, r=True)

setting_controller = bc.Controller(objects = [setting_jnt],
						offset_names = ['Offset'],
						main_ctrl_grp = controller_grp,
						shape = 'gear3d',
						color = 'orange',
						scale=0.5,
						connection_type = 'None',
						rotate_order = 'xyz',
						shape_rotation = [0, 0, 0],
						name_template=NAME_TEMPLATE,
						side_case='lower',
						)
setting_ctrl = setting_controller.ctrls[0]
cmds.delete(setting_jnt)

# FKIK SWITCH

bb.fkIk_switch(
	parents_fk = fk_joints,
	parents_ik = ik_joints,
	targets = drv_joints,
	attr_name = fkIk_attr_name,
	features = ['translation', 'rotation', 'scale'],
	ctrl = setting_ctrl,
	ik_ctrl_grp = ik_ctrl_grp,
	fk_ctrl_grp = fk_ctrl_grp,
	setup_name = rig_name,
	default_value=1
	)

# IK STRETCH

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


distant_node = bb.create_node( node_type='distanceBetween', base=rig_name, elements=[feature_stretch], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{base_loc}.worldPosition[0]',  f'{distant_node}.p1')
cmds.connectAttr(f'{end_loc}.worldPosition[0]',  f'{distant_node}.p2')
distance = cmds.getAttr(f'{distant_node}.distance')

dist_perc_mdv = bb.create_node( node_type='multiplyDivide', base=rig_name, elements=['dist', 'perc'], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{distant_node}.distance', f'{dist_perc_mdv}.i1x')
cmds.setAttr( f'{dist_perc_mdv}.i2x', distance)
cmds.setAttr(f'{dist_perc_mdv}.op', 2 )

attr_name = 'auto' + feature_stretch.capitalize()
mannual_attr = 'mannual' + feature_stretch.capitalize()
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
cmds.connectAttr(f'{distant_node}.distance', f'{bend_cdt}.ft')
cmds.setAttr( f'{bend_cdt}.st', distance)
cmds.setAttr(f'{bend_cdt}.op', 2 )
cmds.connectAttr(f'{mannual_mdl}.o', f'{bend_cdt}.ctr')
cmds.connectAttr(f'{ik_end_ctrl}.{mannual_attr}', f'{bend_cdt}.cfr')

for jnt in ik_joints[:2]:
	cmds.connectAttr(f'{bend_cdt}.ocr', f'{jnt}.sy')

### ================ END OF STRETCH ================ ###
########################################################

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
cmds.addAttr( ik_end_ctrl, ln = attr_name, at = 'float', min = 0, max = 1, dv = 1, k = True )

sq_switch = bb.create_node( node_type='blendColors', base=rig_name, elements=[feature_squash], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{ik_end_ctrl}.{attr_name}', f'{sq_switch}.blender')
cmds.connectAttr(f'{one_div_mdv}.ox', f'{sq_switch}.c1r')
cmds.setAttr( f'{sq_switch}.c2r', 1)
cmds.setAttr( f'{sq_switch}.c2', 1,1,1 )

for jnt in ik_joints[:2]:
	cmds.connectAttr(f'{sq_switch}.opr', f'{jnt}.sx')
	cmds.connectAttr(f'{sq_switch}.opr', f'{jnt}.sz')

### ================= END OF SQUASH ================= ###
#########################################################

# FOOT ROLL
foot_ctrl = 'l_leg_ik_ctl'
foot_locators = [ 'l_foot_heel_loc', 'l_foot_tip_loc', 'l_foot_out_loc', 'l_foot_in_loc']
rig_name = 'foot'
ball_ctrl = ik_ball_ctrl

pose_dict = {	'roll': ['l_foot_tip_loc', 'l_foot_heel_loc'],
				'lean': [], # will update this later.
				'tilt': ['l_foot_out_loc', 'l_foot_in_loc'],
				'heelSpin': ['l_foot_heel_loc'],
				'toeSpin': ['l_foot_tip_loc']
			}
foot_ctrl_grp = bb.create_node('group', base=rig_name, elements=['ctrl'], side=side, p=controller_grp)

controller = bc.Controller(objects = foot_locators,
					offset_names = ['Offset'],
					main_ctrl_grp = foot_ctrl_grp,
					shape = 'sphere',
					color = 'light' + COLOR.capitalize(),
					scale=2,
					connection_type = 'None',
					rotate_order = 'xyz',
					shape_rotation = [0, 0, 0],
					name_template=NAME_TEMPLATE,
					side_case='lower',
					fk_chain = True
					)
foot_ctrls = controller.ctrls

foot_ctrl_dict = {}
for i, loc in enumerate(foot_locators):
	foot_ctrl_dict[loc] = foot_ctrls[i]

pose_grp_dict = {}
for pose in pose_dict.keys():
	pose_grp_dict[pose] = []
	for loc in foot_ctrl_dict.keys():
		if loc in pose_dict[pose]:
			grp = bb.create_offset_group(objects=[foot_ctrl_dict[loc]], offset_names=[pose])
			pose_grp_dict[pose].append(grp[foot_ctrl_dict[loc]][0])

foot_roll_attr = 'footRoll'
cmds.addAttr(foot_ctrl, ln = foot_roll_attr, at='enum', en='—————', k =True)
cmds.setAttr(f'{foot_ctrl}.{foot_roll_attr}', l=True)

pose_attrs = {	'roll': [-180, 180],
				'rollLift': [-180, 180],
				'rollStraight': [-180, 180],
				'lean': [-180, 180],
				'tilt': [-180, 180],
				'heelSpin': [-180, 180],
				'toeSpin': [-180, 180]
			}

for attr, value in pose_attrs.items():
	cmds.addAttr(foot_ctrl, ln=attr, min=value[0], max=value[1], dv=0, k=True )

ball_grp = bb.create_offset_group(objects=[ball_ctrl], offset_names=['roll'])
ball_grp = ball_grp[ball_ctrl][0]

##### HARD CODE ######
cmds.parent(['l_ball_ik_offset_grp', 'l_toe_ik_offset_grp'], 'l_foot_in_ctl')
cmds.parent('l_foot_ctrl_grp', 'l_leg_ik_ctl')

#ROLL
axis = 'rx'
bb.set_driven_key(main_ctrl=foot_ctrl, attr = 'roll', driven = f'{ball_grp}.{axis}', values = { -90:0, 0:0,	45:1, 90:0})
bb.set_driven_key(main_ctrl=foot_ctrl, attr = 'roll', driven = 'l_foot_tip_roll_grp.rx', values = {-90:0, 0:0, 45:0, 90:1})
bb.set_driven_key(main_ctrl=foot_ctrl, attr = 'roll', driven = 'l_foot_heel_roll_grp.rx', values = {-90:-90, 0:0, 45:0, 90:0})

ball_key = cmds.listConnections(f'{ball_grp}.{axis}', type='animCurve')[0]

attr = 'rollLift'
roll_lift_mdl = bb.create_node('multDoubleLinear', base=rig_name, elements=[attr], side=side)
cmds.connectAttr(f'{ball_key}.o', f'{roll_lift_mdl}.i1')
cmds.connectAttr(f'{foot_ctrl}.{attr}', f'{roll_lift_mdl}.i2')
cmds.connectAttr(f'{roll_lift_mdl}.o', f'{ball_grp}.{axis}', f=True)


tip_roll_grp = 'l_foot_tip_roll_grp'
tip_key = cmds.listConnections(f'{tip_roll_grp}.{axis}', type='animCurve')[0]
attr = 'rollStraight'
roll_straight_mdl = bb.create_node('multDoubleLinear', base=rig_name, elements=[attr], side=side)
cmds.connectAttr(f'{tip_key}.o', f'{roll_straight_mdl}.i1')
cmds.connectAttr(f'{foot_ctrl}.{attr}', f'{roll_straight_mdl}.i2')
cmds.connectAttr(f'{roll_straight_mdl}.o', f'{tip_roll_grp}.{axis}', f=True)

attr = 'lean'
axis = 'rz'
driven_grp = 'l_ball_ik_roll_grp'
bb.set_driven_key(main_ctrl=foot_ctrl, attr = attr, driven = f'{driven_grp}.{axis}', values = {-180:-180, 0:0, 180:180})

attr = 'tilt'
axis = 'rz'
driven_grp = 'l_foot_out_tilt_grp'
bb.set_driven_key(main_ctrl=foot_ctrl, attr = attr, driven = f'{driven_grp}.{axis}', values = {-180:0, 0:0, 180:-50})
driven_grp = 'l_foot_in_tilt_grp'
bb.set_driven_key(main_ctrl=foot_ctrl, attr = attr, driven = f'{driven_grp}.{axis}', values = {-180:50, 0:0, 180:0})

attr = 'heelSpin'
axis = 'ry'
driven_grp = 'l_foot_heel_heelspin_grp'
bb.set_driven_key(main_ctrl=foot_ctrl, attr = attr, driven = f'{driven_grp}.{axis}', values = {-180:-180, 0:0, 180:180})

attr = 'toeSpin'
axis = 'ry'
driven_grp = 'l_foot_tip_toespin_grp'
bb.set_driven_key(main_ctrl=foot_ctrl, attr = attr, driven = f'{driven_grp}.{axis}', values = {-180:180, 0:0, 180:-180})

base_names =[]
joint_positions = []
for jnt in ik_joints[:3]:
	posi = cmds.xform(jnt, ws=True, q=True, t=True)
	joint_positions.append(posi)
	base_name = parser.get_base_name(jnt)
	base_names.append(base_name)

nurb_crvA = cmds.curve(p=joint_positions, d=1, n='curveA_crv')
nurb_crvA = cmds.rebuildCurve(nurb_crvA, ch=False, rpo=True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=15, d=3, tol=0.01)
cmds.reverseCurve(nurb_crvA)
cmds.matchTransform(nurb_crvA, ik_joints[0], piv=True)
nurb_crvB = cmds.duplicate(nurb_crvA, n='curveB_crv')[0]
cmds.move(2,0,0, nurb_crvA)
cmds.move(-2,0,0, nurb_crvB)

node_name = NAMER.format(base= rig_name, element = ['ribbon'], side = side, suffix = 'nrb' )
nurb = cmds.loft(nurb_crvA, nurb_crvB, ch=False, u=1, c=0, ar=1, d=1, ss=1, rn=0, po=0, rsn=True, n=node_name)[0]
cmds.delete(nurb_crvA,nurb_crvB)

subdivision = cmds.getAttr(f'{nurb}.spansUV')[0]
subdivision = max(subdivision)
nurb_shp = cmds.listRelatives(nurb, s=True)[0]

follicle_grp = bb.create_node('group', base=rig_name, elements=['follicle'], side=side)
cmds.hide(follicle_grp)
for i in range(0, subdivision):
	u_position = ((1/subdivision) * i) + (1/(subdivision*2))
	follicle = bb.create_node('follicle', rig_name, ['Ribbon'], number = f'{i+1:02d}', side = side)
	follicle_shp = cmds.listRelatives(follicle, s=True)[0]
	cmds.connectAttr(f'{nurb_shp}.local', f'{follicle_shp}.inputSurface')
	cmds.connectAttr(f'{nurb_shp}.worldMatrix[0]', f'{follicle_shp}.inputWorldMatrix')
	cmds.connectAttr(f'{follicle_shp}.ot', f'{follicle}.t')
	cmds.connectAttr(f'{follicle_shp}.or', f'{follicle}.r')
	cmds.setAttr( f'{follicle_shp}.parameterU', u_position)
	cmds.setAttr( f'{follicle_shp}.parameterV', 0.5)
	cmds.parent(follicle, follicle_grp)

tweaker_ctrl_grp = bb.create_node('group', rig_name, ['follicle', 'ctrl'], side = side)

up_posi = bb.get_center_position(ik_joints[:2])
lo_posi = bb.get_center_position(ik_joints[1:3])
mid_posi = cmds.xform(ik_joints[1], ws=True, q=True, t=True)
mid_loc = bb.create_node('locator', rig_name, ['tweak', 'mid'], side = side)
cmds.matchTransform(mid_loc, ik_joints[1])

# DRV name -> TWEAKER maybe.
up_joint = bb.create_node('joint', rig_name, ['drv', 'up'], side = side, p=up_posi)
lo_joint = bb.create_node('joint', rig_name, ['drv', 'lo'], side = side, p=lo_posi)
mid_up_joint = bb.create_node('joint', rig_name, ['drv', 'mid', 'up'], side = side, p=mid_posi)
mid_lo_joint = bb.create_node('joint', rig_name, ['drv', 'mid', 'lo'], side = side, p=mid_posi)
cmds.matchTransform(up_joint, ik_joints[0], rot=True)
cmds.matchTransform(lo_joint, ik_joints[1], rot=True)

mid_controller = bc.Controller(objects = [mid_loc],
						offset_names = ['Offset'],
						main_ctrl_grp = tweaker_ctrl_grp,
						shape = 'circle',
						color = 'sky',
						connection_type = 'None',
						rotate_order = 'xyz',
						name_template='hatrig',
						side_case='lower',
						)
mid_ctrl = mid_controller.ctrls[0]
mid_grp = mid_controller.top_grps[0][0]
cmds.delete(mid_loc)

up_controller = bc.Controller(objects = [up_joint],
						offset_names = ['Offset'],
						main_ctrl_grp = tweaker_ctrl_grp,
						shape = 'circle',
						color = 'sky',
						connection_type = 'None',
						rotate_order = 'xyz',
						name_template='hatrig',
						side_case='lower',
						)
up_ctrl = up_controller.ctrls[0]
up_grp = up_controller.top_grps[0][0]

lo_controller = bc.Controller(objects = [lo_joint],
						offset_names = ['Offset'],
						main_ctrl_grp = tweaker_ctrl_grp,
						shape = 'circle',
						color = 'sky',
						connection_type = 'None',
						rotate_order = 'xyz',
						name_template='hatrig',
						side_case='lower',
						)
lo_ctrl = lo_controller.ctrls[0]
lo_grp = lo_controller.top_grps[0][0]

cmds.parent([mid_up_joint, mid_lo_joint], mid_ctrl)
cmds.parent(up_joint, up_ctrl)
cmds.parent(lo_joint, lo_ctrl)

no_twist_up_joint = bb.create_node('joint', base_names[0], ['no', 'twist'], side = side)
cmds.matchTransform(no_twist_up_joint, ik_joints[0])
cmds.aimConstraint(drv_joints[1], no_twist_up_joint, aimVector=[0, 1, 0], upVector=[0, 0, 1], worldUpType= "none")

twist_ankle_joint = bb.create_node('joint', base_names[2], ['twist'], side = side)
cmds.matchTransform(twist_ankle_joint, drv_joints[2])

cmds.matchTransform(up_grp, drv_joints[0], pov = True)
bb.create_constrain(drv_joints[0], up_grp, 'point')
no_twist_orc = bb.create_constrain([drv_joints[0], no_twist_up_joint], up_grp, 'orient')
cmds.setAttr( f'{no_twist_orc}.interpType', 2)

bb.create_constrain(drv_joints[1], lo_grp, 'point')
pac = cmds.parentConstraint([drv_joints[1], twist_ankle_joint], lo_grp, skipTranslate=['x', 'y', 'z'] )
cmds.setAttr( f'{pac}.interpType', 2)

pac = bb.create_constrain(drv_joints[:2], mid_grp, 'parent')
cmds.setAttr( f'{pac}.interpType', 2)

mid_up_pac = bb.create_constrain(drv_joints[0], mid_up_joint, 'parent')
mid_lo_pac = bb.create_constrain(drv_joints[1], mid_lo_joint, 'parent')
cmds.connectAttr(f'{lo_ctrl}.parentInverseMatrix[0]', f'{mid_up_pac}.constraintParentInverseMatrix')
cmds.connectAttr(f'{lo_ctrl}.parentInverseMatrix[0]', f'{mid_lo_pac}.constraintParentInverseMatrix')

cmds.connectAttr(f'{drv_joints[0]}.s{aim_axis}', f'{up_grp}.s{aim_axis}')
cmds.connectAttr(f'{drv_joints[1]}.s{aim_axis}', f'{lo_grp}.s{aim_axis}')






