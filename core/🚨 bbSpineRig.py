cmds.file("W:/RIG/PROJ/MAYA_PROJ/HATRIG/scenes/AUTO_RIG/spine_start.ma", o=True, f=True )
import maya.cmds as cmds
from bbTools.core import bbRigUtils as bb
from bbTools.core import bbController as bc

reload(bb)
reload(bc)


superRoot = bc.SuperRoot(ctrl_scale=30)

spine_joints = ['spineTmp01_jnt', 'spineTmp02_jnt', 'spineTmp03_jnt', 'spineTmp04_jnt', 'spineTmp05_jnt', 'spineTmp06_jnt', 'spineTmp07_jnt', 'spineTmp08_jnt']



rig_name = 'spine'
rig_side = ''
bind_joint_parent = 'BindJoints_grp'
global_ctrl = 'Placement_ctrl'
aim_axis = 'y'
up_axis = 'x'
rig_scale = 5
mid_ctrl_amount = 2

cmds.hide(spine_joints)

module_grp = cmds.group(em=True, n=f'{rig_name}Mod{rig_side}_grp')
controller_grp = cmds.group(em=True, n=f'{rig_name}Ctrl{rig_side}_grp')

ik_mod_grp = cmds.group(em=True, n=f'{rig_name}IkMod{rig_side}_grp', p=module_grp)
ik_ctrl_grp = cmds.group(em=True, n=f'{rig_name}IkCtrl{rig_side}_grp', p=controller_grp)

# Create rig, bind joints
joints = bb.duplicate_joint_chain(top_joint=spine_joints[0], add_elements=['Spline', 'Bind'], remove_element='Tmp', radius = 1.0, color = None)

rig_joints = joints['Spline']
cmds.parent(rig_joints[0], ik_mod_grp)

ikh, eff, ik_crv = cmds.ikHandle(sj=rig_joints[0], ee=rig_joints[-1], sol = 'ikSplineSolver', pcv=False)
ikh = cmds.rename(ikh, f'{rig_name}Spline_ikh')
eff = cmds.rename(eff, f'{rig_name}Spline_eff')
if mid_ctrl_amount >= (len(rig_joints)/2):
	cmds.warning(f'⚠️⚠️ The amount of middle ctrls shouldn\'t be less than half of the amount of blueprint joints. Stretchy ik may pop when using 🚨🚨')
	
cmds.rebuildCurve(ik_crv, ch=False, rpo = True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=mid_ctrl_amount+1, d=1, tol = 0.01 )
ik_crv = cmds.rename(ik_crv, f'{rig_name}Spline_crv')
cmds.parent([ikh, ik_crv], ik_mod_grp)

bind_joints = joints['Bind']
for i, jnt in enumerate(rig_joints):
	cmds.connectAttr(f'{jnt}.t', f'{bind_joints[i]}.t')
	cmds.connectAttr(f'{jnt}.r', f'{bind_joints[i]}.r')
	cmds.connectAttr(f'{jnt}.s', f'{bind_joints[i]}.s')

cv_count = bb.get_cv_count(ik_crv)
cv_joints = []
for cv in range(0, cv_count+1):
	cmds.select(cl=True)
	position = cmds.xform(f'{ik_crv}.cv[{cv}]', ws=True, q = True, t=True)
	cv_joint = cmds.joint(n=f'{rig_name}Crv{cv+1:02d}{rig_side}_jnt', p = position, rad=2)
	cmds.makeIdentity(cv_joint, a=True, r=True)
	cv_joints.append(cv_joint)

base_jnt = cv_joints[0]
top_jnt = cv_joints[-1]
cmds.parent(cv_joints, ik_mod_grp)

baseIk_ctrl = bc.Controller(objects = [base_jnt],
						main_ctrl_grp = ik_ctrl_grp,
						name = f'{rig_name}Base',
						side = rig_side,
						offset_names = ['Zro','Position', 'Offset'],
						shape = 'chest',
						color = 'green',
						scale = rig_scale,
						connection_type = 'None',
						rotate_order = 'zyx',
						shape_rotation = [0,0,180],
						)
base_ctrl = baseIk_ctrl.ctrls[0]
base_grps = baseIk_ctrl.top_grps[0]

topIk_ctrl = bc.Controller(objects = [top_jnt],
						main_ctrl_grp = ik_ctrl_grp,
						name = f'{rig_name}Top',
						side = rig_side,
						offset_names = ['Zro','Position', 'Offset'],
						shape = 'chest',
						color = 'green',
						scale = rig_scale,
						connection_type = 'None',
						rotate_order = 'zyx',
						shape_rotation = [0,0,0],
						)
top_ctrl = topIk_ctrl.ctrls[0]
top_grps = topIk_ctrl.top_grps[0]

# Ctrl Position Attr
attr_name = 'position'
target_grps = [topIk_ctrl.top_grps[0][1], baseIk_ctrl.top_grps[0][1]]
negative_grps = []
for i, ctrl in enumerate([top_ctrl, base_ctrl]):
	target_ctrls = [top_ctrl, base_ctrl]
	print( f'working on {ctrl}')
	target = target_grps[i]
	ctrl_name = bb.get_name(ctrl)
	destination_obj = target_ctrls
	destination_obj.remove(ctrl)
	cmds.matchTransform(target, destination_obj)
	target_position = cmds.xform(target, q =True, t=True, os=True)

	position_bc = cmds.createNode('blendColors', n = f'{ctrl_name}Position{rig_side}_bc')
	if i == 0:
		default = 'color1'
		result = 'color2'
		dv = 1
	else:
		default = 'color2'
		result = 'color1'
		dv = 0
	cmds.setAttr( f'{position_bc}.{default}', 0,0,0)
	cmds.setAttr( f'{position_bc}.{result}', *target_position)
	cmds.setAttr( f'{target}.t', 0, 0, 0)
	cmds.addAttr( ctrl, ln = attr_name, at = 'float', min = 0, max = 1, dv = dv, k = True )
	cmds.connectAttr(f'{ctrl}.{attr_name}', f'{position_bc}.blender')
	cmds.connectAttr(f'{position_bc}.op', f'{target}.t')
	
	negative_grp = cmds.group(em=True, n=f'{ctrl_name}Negative{rig_side}_grp')
	neg_mdv = cmds.createNode('multiplyDivide', n = f'{ctrl_name}Neg{rig_side}_mdv')
	cmds.connectAttr(f'{target}.t', f'{neg_mdv}.i1')
	cmds.setAttr( f'{neg_mdv}.i2', -1,-1,-1)
	cmds.connectAttr(f'{neg_mdv}.o', f'{negative_grp}.t')
	cmds.parent(negative_grp, ctrl)
	negative_grps.append(negative_grp)

topNeg_grp = negative_grps[0]
baseNeg_grp = negative_grps[1]

bb.create_constrain([topNeg_grp], top_jnt, 'psc')
bb.create_constrain([baseNeg_grp], base_jnt, 'psc')

mid_joints = cv_joints[1:-1]
mid_controllers = bc.Controller(objects = mid_joints,
						main_ctrl_grp = ik_ctrl_grp,
						name = rig_name,
						side = rig_side,
						offset_names = ['Zro', 'Space', 'Offset'],
						shape = 'squareRound',
						color = 'lightGreen',
						scale = rig_scale * 0.6,
						connection_type = 'parentScale',
						rotate_order = 'zyx',
						shape_rotation = [0,0,0],
						)

mid_ctrls = mid_controllers.ctrls
mid_grps = mid_controllers.top_grps
cmds.rebuildCurve(ik_crv, ch=False, rpo = True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=(mid_ctrl_amount/2)+1, d=3, tol = 0.01 )
cmds.setAttr('spineSpline_crvShape.dispCV',1)
curve_skc = cmds.skinCluster(cv_joints, ik_crv, tsb = True, mi=3, dr=2, rui=False, nw=0, bindMethod=0, n=f'{rig_name}Curve{rig_side}_skc' )

# Ik stretch
curve_info = cmds.createNode('curveInfo', n=f'{rig_name}Stretch{rig_side}_cif')
curve_shape = cmds.listRelatives(ik_crv, s=True)[0]
cmds.connectAttr(f'{curve_shape}.worldSpace[0]', f'{curve_info}.inputCurve')
original_length = cmds.getAttr(f'{curve_info}.arcLength')

global_scale_mdv = cmds.createNode('multiplyDivide', n = f'{rig_name}StretchScale{rig_side}_mdv')
cmds.connectAttr(f'{curve_info}.arcLength', f'{global_scale_mdv}.i1x')
cmds.connectAttr(f'{global_ctrl}.sy', f'{global_scale_mdv}.i2x')
cmds.setAttr(f'{global_scale_mdv}.op', 2 )

dist_perc_mdv = cmds.createNode('multiplyDivide', n = f'{rig_name}StretchPerc{rig_side}_mdv')
cmds.connectAttr(f'{global_scale_mdv}.ox', f'{dist_perc_mdv}.i1x')
cmds.setAttr( f'{dist_perc_mdv}.i2x', original_length )
cmds.setAttr(f'{dist_perc_mdv}.op', 2 )

strech_attr = 'autoStretch'
cmds.addAttr( top_ctrl, ln = strech_attr, at = 'float', min = 0, max = 1, dv = 1, k = True )
strech_switch_bc = cmds.createNode('blendColors', n = f'{rig_name}StretchSwitch{rig_side}_bc')
cmds.connectAttr(f'{dist_perc_mdv}.ox', f'{strech_switch_bc}.c1r')
cmds.setAttr( f'{strech_switch_bc}.c2r', 1)
cmds.connectAttr(f'{top_ctrl}.{strech_attr}', f'{strech_switch_bc}.blender')

# Squash Volume
volume_sqr_mdv = cmds.createNode('multiplyDivide', n = f'{rig_name}SquashSqr{rig_side}_mdv')
cmds.connectAttr(f'{strech_switch_bc}.opr', f'{volume_sqr_mdv}.i1x')
cmds.setAttr( f'{volume_sqr_mdv}.i2x', 0.5 )
cmds.setAttr(f'{volume_sqr_mdv}.op', 3 )

volume_one_div_mdv = cmds.createNode('multiplyDivide', n = f'{rig_name}Squash{rig_side}_mdv')
cmds.setAttr( f'{volume_one_div_mdv}.i1x', 1)
cmds.connectAttr(f'{volume_sqr_mdv}.ox', f'{volume_one_div_mdv}.i2x')
cmds.setAttr(f'{volume_one_div_mdv}.op', 2 )

squash_attr = 'autoSquash'
cmds.addAttr( top_ctrl, ln = squash_attr, at = 'float', min = 0, max = 1, dv = 1, k = True )
volume_switch_bc = cmds.createNode('blendColors', n = f'{rig_name}SquashSwitch{rig_side}_bc')
cmds.connectAttr(f'{volume_one_div_mdv}.ox', f'{volume_switch_bc}.c1r')
cmds.setAttr( f'{volume_switch_bc}.c2r', 1)
cmds.connectAttr(f'{top_ctrl}.{squash_attr}', f'{volume_switch_bc}.blender')

for rig_joint in rig_joints:
	cmds.connectAttr(f'{strech_switch_bc}.opr', f'{rig_joint}.sy')
	cmds.connectAttr(f'{volume_switch_bc}.opr', f'{rig_joint}.sx')
	cmds.connectAttr(f'{volume_switch_bc}.opr', f'{rig_joint}.sz')

# Space Switch
all_spaces_grp = cmds.group(em=True, n=f'{rig_name}Spaces{rig_side}_grp', p=ik_mod_grp)
follow_type = ['point', 'orient']
follow_attrs = ['followPosition', 'followRotation']
for typ, attr in zip(follow_type, follow_attrs):
	for i, ctrl in enumerate(mid_ctrls):
		target_grp = mid_grps[i][1]
		space_grps = bb.space_switch(parentA = baseNeg_grp, parentB = topNeg_grp , attr = attr, target_grp = target_grp, follow_type = typ, ctrl = ctrl)
		follow_value = (1/(len(mid_ctrls)+1)) * (i+1)
		cmds.setAttr( f'{ctrl}.{attr}', follow_value)
		cmds.parent(space_grps, all_spaces_grp)

