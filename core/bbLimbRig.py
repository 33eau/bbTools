import maya.cmds as cmds
from .utils import rig_utils as bb
from .controllers import creator as bc
from .naming import factory as naming
from .naming import helper as hp
reload(bb )
reload(bc)
reload(naming)
reload(hp)

# IK LIMB RIG with stretch and squash
NAME_TEMPLATE = 'hatrig'
NAMER = naming.get_namer(NAME_TEMPLATE)


limb_joints = ['l_thigh_ik_jnt', 'l_knee_ik_jnt', 'l_ankle_ik_jnt']
base_ctrl = 'l_thigh_ik_ctl'
end_ctrl = 'l_leg_ik_hdl_ctl'
feature_stretch = 'stretch'
feature_squash = 'volume'

rig_name = 'leg'

base, element, number, side, suffix = NAMER.extract(limb_joints[0]) 

ctrls = [base_ctrl, end_ctrl]
position_locators = []
for i, point in enumerate(['start', 'end']):
	loc = bb.create_named_node( node_type='locator', base=rig_name, elements=[feature_stretch, point], number=number, side=side, namer=NAMER)
	cmds.matchTransform(loc, ctrls[i])
	if NAME_TEMPLATE == 'hatrig':
		cmds.parent(loc, ctrls[i])
	else:
		bb.create_constrain( parents=[ctrls[i]], target=loc, type="parent")
	cmds.hide(loc)
	position_locators.append(loc)
base_loc = position_locators[0]
end_loc = position_locators[1]


distant_node = bb.create_named_node( node_type='distanceBetween', base=rig_name, elements=[feature_stretch], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{base_loc}.worldPosition[0]',  f'{distant_node}.p1')
cmds.connectAttr(f'{end_loc}.worldPosition[0]',  f'{distant_node}.p2')
distance = cmds.getAttr(f'{distant_node}.distance')

dist_perc_mdv = bb.create_named_node( node_type='multiplyDivide', base=rig_name, elements=['dist', 'perc'], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{distant_node}.distance', f'{dist_perc_mdv}.i1x')
cmds.setAttr( f'{dist_perc_mdv}.i2x', distance)
cmds.setAttr(f'{dist_perc_mdv}.op', 2 )

attr_name = 'auto' + feature_stretch.capitalize()
mannual_attr = 'mannual' + feature_stretch.capitalize()
#if not cmds.attributeQuery(attr_name, ln=True, node=end_ctrl, exists=True):
cmds.addAttr( end_ctrl, ln = attr_name, at = 'float', min = 0, max = 1, dv = 1, k = True )
cmds.addAttr( end_ctrl, ln = mannual_attr, at = 'float', min = -1, max = 10, dv = 1, k = True )

feature_switch = bb.create_named_node( node_type='blendColors', base=rig_name, elements=[feature_stretch], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{end_ctrl}.{attr_name}', f'{feature_switch}.blender')
cmds.connectAttr(f'{dist_perc_mdv}.ox', f'{feature_switch}.c1r')

mannual_mdl = bb.create_named_node( node_type='multDoubleLinear', base=rig_name, elements=[feature_stretch], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{end_ctrl}.{mannual_attr}', f'{mannual_mdl}.i2')
cmds.connectAttr(f'{feature_switch}.opr', f'{mannual_mdl}.i1')

bend_cdt = bb.create_named_node( node_type='condition', base=rig_name, elements=[feature_stretch], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{distant_node}.distance', f'{bend_cdt}.ft')
cmds.setAttr( f'{bend_cdt}.st', distance)
cmds.setAttr(f'{bend_cdt}.op', 2 )
cmds.connectAttr(f'{mannual_mdl}.o', f'{bend_cdt}.ctr')
cmds.connectAttr(f'{end_ctrl}.{mannual_attr}', f'{bend_cdt}.cfr')

for jnt in limb_joints[:-1]:
	cmds.connectAttr(f'{bend_cdt}.ocr', f'{jnt}.sy')

### ================ END OF STRETCH ================ ###
########################################################

# Squash
power_mdv = bb.create_named_node( node_type='multiplyDivide', base=rig_name, elements=[feature_squash, 'power'], number=number, side=side, namer=NAMER)
cmds.setAttr(f'{power_mdv}.op', 3 )
cmds.setAttr( f'{power_mdv}.i2x', 0.5)
cmds.connectAttr(f'{bend_cdt}.ocr', f'{power_mdv}.i1x')

one_div_mdv = bb.create_named_node( node_type='multiplyDivide', base=rig_name, elements=[feature_squash, 'one', 'div'], number=number, side=side, namer=NAMER)
cmds.setAttr( f'{one_div_mdv}.i1x', 1)
cmds.setAttr(f'{one_div_mdv}.op', 2 )
cmds.connectAttr(f'{power_mdv}.ox', f'{one_div_mdv}.i2x')

attr_name = 'auto' + feature_squash.capitalize()
cmds.addAttr( end_ctrl, ln = attr_name, at = 'float', min = 0, max = 1, dv = 1, k = True )

sq_switch = bb.create_named_node( node_type='blendColors', base=rig_name, elements=[feature_squash], number=number, side=side, namer=NAMER)
cmds.connectAttr(f'{end_ctrl}.{attr_name}', f'{sq_switch}.blender')
cmds.connectAttr(f'{one_div_mdv}.ox', f'{sq_switch}.c1r')
cmds.setAttr( f'{sq_switch}.c2r', 1)

for jnt in limb_joints[:-1]:
	cmds.connectAttr(f'{sq_switch}.opr', f'{jnt}.sx')
	cmds.connectAttr(f'{sq_switch}.opr', f'{jnt}.sz')

### ================= END OF SQUASH ================= ###
#########################################################

