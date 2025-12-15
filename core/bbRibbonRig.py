import maya.cmds as cmds
from bbTools.core import bbRigUtils as bb
from bbTools.core import bbController as bc
from bbTools.core import bbConstants as constants
from bbTools.core.naming import factory as naming
from bbTools.core.naming import helper as hp
reload(bb )
reload(bc)
reload(constants)
reload(naming)
reload(hp)

NAME_TEMPLATE = 'hatrig'
NAMER = naming.get_namer(NAME_TEMPLATE)
ROTATE_ORDERS = constants.ROTATE_ORDERS
SHAPES = ctrl_shapes.ctrl_shapes

class LimbRig:
	def __init__(self,
					blueprint_joints = None, # ['l_thigh_tmp_jnt', 'l_knee_tmp_jnt', 'l_ankle_tmp_jnt', 'l_ball_tmp_jnt', 'l_ball_tip_tmp_jnt']
					aim_axis = None,
					up_axis = None,
					rig_name = None,
					global_ctrl = None
	):
		pass



		

main_joint = ik_joints[:3]
rig_name = 'leg'
side = side
base_names =[]
joint_positions = []

for jnt in main_joint:
	posi = cmds.xform(jnt, ws=True, q=True, t=True)
	joint_positions.append(posi)
	base_name = hp.get_base_name(jnt)
	base_names.append(base_name)

nurb_crvA = cmds.curve(p=joint_positions, d=1, n='curveA_crv')
nurb_crvA = cmds.rebuildCurve(nurb_crvA, ch=False, rpo=True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=15, d=3, tol=0.01)
cmds.reverseCurve(nurb_crvA)
cmds.matchTransform(nurb_crvA, main_joint[0], piv=True)
nurb_crvB = cmds.duplicate(nurb_crvA, n='curveB_crv')[0]
cmds.move(2,0,0, nurb_crvA)
cmds.move(-2,0,0, nurb_crvB)

node_name = NAMER.format(base= rig_name, element = ['ribbon'], side = side, suffix = 'nrb' )
nurb = cmds.loft(nurb_crvA, nurb_crvB, ch=False, u=1, c=0, ar=1, d=1, ss=1, rn=0, po=0, rsn=True, n=node_name)[0]
cmds.delete(nurb_crvA,nurb_crvB)

subdivision = cmds.getAttr(f'{nurb}.spansUV')[0]
subdivision = max(subdivision)
nurb_shp = cmds.listRelatives(nurb, s=True)[0]

follicle_grp = bb.create_named_node('group', base=rig_name, elements=['follicle'], side=side)
cmds.hide(follicle_grp)
for i in range(0, subdivision):
	u_position = ((1/subdivision) * i) + (1/(subdivision*2))
	follicle = bb.create_named_node('follicle', rig_name, ['Ribbon'], number = f'{i+1:02d}', side = side)
	follicle_shp = cmds.listRelatives(follicle, s=True)[0]
	cmds.connectAttr(f'{nurb_shp}.local', f'{follicle_shp}.inputSurface')
	cmds.connectAttr(f'{nurb_shp}.worldMatrix[0]', f'{follicle_shp}.inputWorldMatrix')
	cmds.connectAttr(f'{follicle_shp}.ot', f'{follicle}.t')
	cmds.connectAttr(f'{follicle_shp}.or', f'{follicle}.r')
	cmds.setAttr( f'{follicle_shp}.parameterU', u_position)
	cmds.setAttr( f'{follicle_shp}.parameterV', 0.5)
	cmds.parent(follicle, follicle_grp)

tweaker_ctrl_grp = bb.create_named_node('group', rig_name, ['follicle', 'ctrl'], side = side)

up_posi = bb.get_center_position(main_joint[:2])
lo_posi = bb.get_center_position(main_joint[1:3])
mid_posi = cmds.xform(main_joint[1], ws=True, q=True, t=True)
mid_loc = bb.create_named_node('locator', rig_name, ['tweak', 'mid'], side = side)
cmds.matchTransform(mid_loc, main_joint[1])

up_joint = bb.create_named_node('joint', rig_name, ['drv', 'up'], side = side, p=up_posi)
lo_joint = bb.create_named_node('joint', rig_name, ['drv', 'lo'], side = side, p=lo_posi)
mid_up_joint = bb.create_named_node('joint', rig_name, ['drv', 'mid', 'up'], side = side, p=mid_posi)
mid_lo_joint = bb.create_named_node('joint', rig_name, ['drv', 'mid', 'lo'], side = side, p=mid_posi)
cmds.matchTransform(up_joint, main_joint[0], rot=True)
cmds.matchTransform(lo_joint, main_joint[1], rot=True)

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

no_twist_up_joint = bb.create_named_node('joint', base_names[0], ['no', 'twist'], side = side)
cmds.matchTransform(no_twist_up_joint, main_joint[0])
cmds.aimConstraint(drv_joints[1], no_twist_up_joint, aimVector=[0, 1, 0], upVector=[0, 0, 1], worldUpType= "none")

twist_ankle_joint = bb.create_named_node('joint', base_names[2], ['twist'], side = side)
cmds.matchTransform(twist_ankle_joint, drv_joints[2])



