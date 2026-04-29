# TANK TRACK RIG

path = 'W:/RIG/PROJ/MAYA_PROJ/TANK/scenes/tank_autoRig.ma'
cmds.file(path, open=True, f=True)
from importlib import reload
import maya.cmds as cmds
from bbTools.core.utils import rig_utils as bb
from bbTools.core.naming import namer_factory as naming
from bbTools.core.naming import templates
from bbTools.core.naming import current_project

reload(bb)
reload(naming)
reload(templates)
reload(current_project)

base = 'track'
side = 'l'
main_ctrl = 'trackLFT_ctrl'
aim_axis = 'z'
up_axis = 'x'

first_jnt = 'jnt_l_tracks001'
ik_crv = 'track_iksp_crv'

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)

MAIN_CTRL_SHAPE='triangle'
TWEAKER_CTRL_SHAPE='crossCircle'

AUTO_SPIN_ATTR = 'autoSpin'
OFFSET_ATTR = 'offset'
SPEED_ATTR = 'speed'

jnt_list = cmds.listRelatives( first_jnt ,  type = 'joint', allDescendents = True )
jnt_list.append(first_jnt)
jnt_list.reverse()

if not ik_crv:
	pos_list = []
	for jnt in jnt_list:
		pos = cmds.xform(jnt, q=True, t=True, ws=True)
		pos_list.append(pos)
	ik_crv = cmds.curve(p=pos_list, d=1)
	crv_name = NAMER.format(base, ['Spline'], None, side, templates.TYPE_SUFFIX['nurbsCurve'])
	ik_crv = cmds.rename(ik_crv, crv_name)

ik_name = NAMER.format(base, ['ik'], None, side, '')
ikh_name = NAMER.format(base, ['Spline'], None, side, templates.TYPE_SUFFIX['ikHandle'])
eff_name = NAMER.format(base, ['Spline'], None, side, templates.TYPE_SUFFIX['ikEffector'])

ikh, eff = cmds.ikHandle(sj=jnt_list[0], ee=jnt_list[-1], ccv=False, scv=False, sol='ikSplineSolver', pcv=False, c=ik_crv)
ikh = cmds.rename(ikh, ikh_name)
eff = cmds.rename(eff, eff_name)

# Advance Twist
up_ab_axis = bb.axis_convert(up_axis, 'absolute_letter')
other_axes = 'xyz'.replace(up_ab_axis, '')
fwd_axis_idx = bb.axis_convert(aim_axis, 'ik_twist_index')
up_axis_idx = bb.axis_convert(up_axis, 'ik_twist_up_index')
up_axis_value = -1 if '-' in up_axis else 1
cmds.setAttr( f'{ikh}.dTwistControlEnable', 1)
cmds.setAttr( f'{ikh}.dWorldUpType', 4)
cmds.setAttr( f'{ikh}.dForwardAxis', fwd_axis_idx)
cmds.setAttr( f'{ikh}.dWorldUpAxis', up_axis_idx)
cmds.setAttr( f'{ikh}.dWorldUpVector{up_ab_axis.upper()}', up_axis_value)
cmds.setAttr( f'{ikh}.dWorldUpVectorEnd{up_ab_axis.upper()}', up_axis_value)

ik_crv_shp = cmds.listRelatives(ik_crv, s=True)[0]
ik_crv_cif = bb.create_node('curveInfo', base, ['iksp'], None, side)
cmds.connectAttr(f'{ik_crv_shp}.worldSpace[0]', f'{ik_crv_cif}.inputCurve')

# calculate percentage of the moved distance to 1 full loop (max offset value in .i1x = 1)
perc_mdv = bb.create_node('multiplyDivide', base, ['perc'], None, side)
cmds.setAttr(f'{perc_mdv}.op', 2 )
cmds.setAttr( f'{perc_mdv}.i1x', 1)
cmds.connectAttr(f'{ik_crv_cif}.arcLength', f'{perc_mdv}.i2x')

start_loc = bb.create_node('locator', base, ['start'], None, side)
move_loc = bb.create_node('locator', base, ['move'], None, side)

main_ctrl_pos = cmds.xform(main_ctrl, q=True, t=True, ws=True)
cmds.xform(start_loc, t=[main_ctrl_pos[0], 0, main_ctrl_pos[2]], ws=True)
cmds.xform(move_loc, t=[main_ctrl_pos[0], 0, main_ctrl_pos[2]], ws=True)
bb.create_constrain([main_ctrl], move_loc, 'parent', maintain_offset=True)

start_loc_shp = cmds.listRelatives(start_loc, s=True)[0]
move_loc_shp = cmds.listRelatives(move_loc, s=True)[0]
distance_ddm = bb.create_node('distanceDimShape', base, ['dist'], None, side)
cmds.connectAttr(f'{start_loc_shp}.worldPosition[0]', f'{distance_ddm}.startPoint')
cmds.connectAttr(f'{move_loc_shp}.worldPosition[0]', f'{distance_ddm}.endPoint')

mul_dis_mdl = bb.create_node('multDoubleLinear', base, ['mul', 'dis'], None, side)
cmds.connectAttr(f'{perc_mdv}.ox', f'{mul_dis_mdl}.i1')
cmds.connectAttr(f'{distance_ddm}.distance', f'{mul_dis_mdl}.i2')

start_loc_dcm = bb.create_node('decomposeMatrix', base, ['start'], None, side)
move_loc_dcm = bb.create_node('decomposeMatrix', base, ['move'], None, side)
cmds.connectAttr(f'{start_loc}.matrix', f'{start_loc_dcm}.inputMatrix')
cmds.connectAttr(f'{move_loc}.matrix', f'{move_loc_dcm}.inputMatrix')

fwd_dir_pma = bb.create_node('plusMinusAverage', base, ['fwd', 'dir'], None, side)
cmds.setAttr(f'{fwd_dir_pma}.op', 2 )
cmds.connectAttr(f'{move_loc_dcm}.outputTranslateZ', f'{fwd_dir_pma}.input1D[0]')
cmds.connectAttr(f'{start_loc_dcm}.outputTranslateZ', f'{fwd_dir_pma}.input1D[1]')

dir_cdt = bb.create_node('condition', base, ['dir'], None, side)
cmds.setAttr(f'{dir_cdt}.op', 2 )
cmds.setAttr( f'{dir_cdt}.st', 0)
cmds.setAttr( f'{dir_cdt}.ctr', 1)
cmds.setAttr( f'{dir_cdt}.cfr', -1)
cmds.connectAttr(f'{fwd_dir_pma}.output1D', f'{dir_cdt}.ft')

dir_mul_mdl = bb.create_node('multDoubleLinear', base, ['dir', 'mul'], None, side)
cmds.connectAttr(f'{mul_dis_mdl}.o', f'{dir_mul_mdl}.i1')
cmds.connectAttr(f'{dir_cdt}.ocr', f'{dir_mul_mdl}.i2')

only_fwd_cdt = bb.create_node('condition', base, ['fwd', 'dir'], None, side)
cmds.setAttr(f'{only_fwd_cdt}.op', 1 )
cmds.setAttr( f'{only_fwd_cdt}.st', 0)
cmds.setAttr( f'{only_fwd_cdt}.cfr', 0)
cmds.connectAttr(f'{dir_mul_mdl}.o', f'{only_fwd_cdt}.ctr')
cmds.connectAttr(f'{fwd_dir_pma}.output1D', f'{only_fwd_cdt}.ft')

driver = f'{only_fwd_cdt}.ocr'
driven = f'{ikh}.offset'
cmds.setDrivenKeyframe(driven, cd=driver, itt = 'linear', ott = 'linear', dv=0, v=0 )
cmds.setDrivenKeyframe(driven, cd=driver, itt = 'linear', ott = 'linear', dv=1, v=1 )
key = cmds.listConnections(driven, type='animCurve')[0]
cmds.setAttr( f'{key}.preInfinity', 3)
cmds.setAttr( f'{key}.postInfinity', 3)

# Extra Attribute
bb.attr_separator(main_ctrl)
cmds.addAttr( main_ctrl, ln = AUTO_SPIN_ATTR, at = 'enum', en = 'OFF:ON' , k = True )
cmds.addAttr( main_ctrl, ln = SPEED_ATTR, at = 'float', dv = 1, k = True )
cmds.addAttr( main_ctrl, ln = OFFSET_ATTR, at = 'float', dv = 0, k = True )
cmds.setAttr( f'{main_ctrl}.{AUTO_SPIN_ATTR}', 1)

# Speed Attribute
speed_mdl = bb.create_node('multDoubleLinear', base, [SPEED_ATTR], None, side)
cmds.connectAttr(f'{main_ctrl}.{SPEED_ATTR}', f'{speed_mdl}.i1')
cmds.connectAttr(f'{key}.o', f'{speed_mdl}.i2')

# Offset Attribute
offset_adl = bb.create_node('addDoubleLinear', base, [OFFSET_ATTR], None, side)
cmds.connectAttr(f'{main_ctrl}.{OFFSET_ATTR}', f'{offset_adl}.i1')
cmds.connectAttr(f'{speed_mdl}.o', f'{offset_adl}.i2')

# AutoSpin Switch
switch_mdl = bb.create_node('multDoubleLinear', base, [AUTO_SPIN_ATTR], None, side)	
cmds.connectAttr(f'{main_ctrl}.{AUTO_SPIN_ATTR}', f'{switch_mdl}.i1')
cmds.connectAttr(f'{offset_adl}.o', f'{switch_mdl}.i2')

# Result
cmds.connectAttr(f'{switch_mdl}.o', f'{ikh}.offset', f=True)
bb.create_constrain([main_ctrl], ik_crv, 'pac')



















