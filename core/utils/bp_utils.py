# path = r'W:/RIG/PROJ/MAYA_PROJ/JINXIE/autoRig/work/START_FACE.0006.ma'
# cmds.file(path, open=True, f=True)

from importlib import reload
import maya.cmds as cmds
from bbTools.core.utils import rig_utils as bb
from bbTools.core.controllers import creator as bc
from bbTools.core.naming import parser
from bbTools.core.naming import namer_factory as naming
from bbTools.core.naming import current_project
reload(bb)
reload(bc)
reload(parser)
reload(naming)
reload(current_project)

NAME_TEMPLATE = current_project.PROJECT
NAMER = naming.get_namer(NAME_TEMPLATE)
SCALE = 0.1

def create_bp_ctrl( bp_jnt_grp = 'blurprint_jnt_grp', rig_name = 'face'):
	bp_ctrl_grp = bb.create_node('group', 'face', ['bp', 'ctrl'], None, None)
	created_jnt = []
	bp_ctrls = []
	bp_grps = []

	global_ctrl = bc.Controller.create_curve(
							ctrl_name=f'{rig_name}_global_ctrl', 
							shape='arrow1dir',
							color='yellow', 
							line_width=1, 
							scale=SCALE * 100
							)
	global_grp = bb.create_offset_group(global_ctrl, ['Zro'])
	global_grp = global_grp[global_ctrl]
	cmds.parent( global_grp, bp_ctrl_grp )
	jnts = cmds.listRelatives(bp_jnt_grp, ad=True)

	for jnt in jnts:
		parent = cmds.listRelatives(jnt, p=True)[0]
		base, element, number, side, suffix = NAMER.extract(jnt)
		element = element if element else []
		side = parser.find_element(jnt, 'sides')
		side = parser.format_side(side, 'lower')
		opp_side = 'r' if side == 'l' else 'l'
		opp_jnt = NAMER.format(base, element, number, opp_side, suffix)

		grp, ctrl = bb.create_xyz(objs=[jnt], connection_type = 'matrix_parent', scale=SCALE, bp_jnt=True)
		mtxcons_mmt = bb.create_node('multMatrix', base, element, number, side)
		cmds.connectAttr(f'{ctrl}.worldMatrix[0]', f'{mtxcons_mmt}.matrixIn[0]')
		cmds.connectAttr(f'{parent}.worldInverseMatrix[0]', f'{mtxcons_mmt}.matrixIn[1]')
		cmds.connectAttr(f'{mtxcons_mmt}.matrixSum', f'{jnt}.offsetParentMatrix')
		cmds.setAttr(f'{jnt}.rotate', *[0,0,0])
		cmds.setAttr(f'{jnt}.t', *[0,0,0])
		cmds.setAttr(f'{jnt}.jointOrient', *[0, 0, 0])
		
		created_jnt.append(jnt)
		bp_ctrls.append(ctrl)
		bp_grps.append(grp)
		
		if cmds.objExists(opp_jnt):
			mirror_attr = f'{base}Mirror'
			cmds.addAttr( global_ctrl, ln = mirror_attr, at = 'enum', en = 'OFF:ON', dv=1, k = True )

			opp_grp, opp_ctrl = bb.create_xyz(objs=[opp_jnt], connection_type = 'matrix_parent', scale=SCALE, bp_jnt=True)	
			opp_parent = cmds.listRelatives(opp_jnt, p=True)[0]
			opp_mtxcons_mmt = bb.create_node('multMatrix', base, element, number, opp_side)
			cmds.connectAttr(f'{opp_ctrl}.worldMatrix[0]', f'{opp_mtxcons_mmt}.matrixIn[0]')
			cmds.connectAttr(f'{opp_parent}.worldInverseMatrix[0]', f'{opp_mtxcons_mmt}.matrixIn[1]')

			translate_inv_mdv = bb.create_node('multiplyDivide', base, element + ['mirror'], number, None)
			jnt_dcm = bb.create_node('decomposeMatrix', base, element + ['mirror'], number, opp_side)
			cmds.connectAttr(f'{mtxcons_mmt}.matrixSum', f'{jnt_dcm}.inputMatrix')

			t_inv_mdv = bb.create_node('multiplyDivide', base, element + ['tInv'], number, opp_side)
			cmds.setAttr( f'{t_inv_mdv}.i2x', -1)
			cmds.connectAttr(f'{jnt_dcm}.outputTranslate', f'{t_inv_mdv}.i1')

			r_inv_mdv = bb.create_node('multiplyDivide', base, element + ['rInv'], number, opp_side)
			cmds.setAttr( f'{r_inv_mdv}.i2y', -1)
			cmds.connectAttr(f'{jnt_dcm}.outputRotate', f'{r_inv_mdv}.i1')

			mirror_cpm = bb.create_node('composeMatrix', base, element + ['mirror'], number, opp_side)
			cmds.connectAttr(f'{t_inv_mdv}.o', f'{mirror_cpm}.inputTranslate')
			cmds.connectAttr(f'{r_inv_mdv}.o', f'{mirror_cpm}.inputRotate')
			cmds.connectAttr(f'{jnt_dcm}.outputQuat', f'{mirror_cpm}.inputQuat')
			cmds.connectAttr(f'{jnt_dcm}.outputShear', f'{mirror_cpm}.inputShear')
			cmds.connectAttr(f'{jnt_dcm}.outputScale', f'{mirror_cpm}.inputScale')

			mirror_bmt = bb.create_node('blendMatrix', base, element + ['mirror'], number, None)
			cmds.connectAttr(f'{opp_mtxcons_mmt}.matrixSum', f'{mirror_bmt}.inputMatrix')
			cmds.connectAttr(f'{mirror_cpm}.outputMatrix', f'{mirror_bmt}.target[0].targetMatrix')
			cmds.connectAttr(f'{global_ctrl}.{mirror_attr}', f'{mirror_bmt}.target[0].weight')
			cmds.connectAttr(f'{mirror_bmt}.outputMatrix', f'{opp_jnt}.offsetParentMatrix')

			cmds.setAttr(f'{opp_jnt}.rotate', *[0,0,0])
			cmds.setAttr(f'{opp_jnt}.t', *[0,0,0])
			cmds.setAttr(f'{opp_jnt}.jointOrient', *[0, 0, 0])

			ctrl_vis_rev = bb.create_node('reverse', base, element + ['mirror'], number, opp_side)
			cmds.connectAttr(f'{global_ctrl}.{mirror_attr}', f'{ctrl_vis_rev}.ix')
			cmds.connectAttr(f'{ctrl_vis_rev}.ox', f'{opp_grp}.v')	

			created_jnt.append(opp_jnt)
			bp_ctrls.append(opp_ctrl)
			bp_grps.append(opp_grp)
			jnts.remove(opp_jnt)

	for jnt in created_jnt:
		jnt_index = created_jnt.index(jnt)
		parent = cmds.listRelatives(jnt, p=True)[0]
		if parent in created_jnt:
			parent_idx = created_jnt.index(parent)
			cmds.parent(bp_grps[jnt_index], bp_ctrls[parent_idx])
		elif parent == bp_jnt_grp:
			cmds.parent(bp_grps[jnt_index], global_ctrl)

	print(f'Create bp ctrls: {rig_name}')
	return 

