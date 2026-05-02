path = 'W:/RIG/PROJ/MAYA_PROJ/JINXIE/autoRig/work/face_builder.0007.ma'
cmds.file(path, open=True, f=True)
#006

from bbTools.rigs.face import base
from bbTools.rigs.face import tweaker_rig as tweaker
from bbTools.rigs.face import lips_rig as lips
from bbTools.rigs.face import eyebrow_rig as eb
from bbTools.rigs.face import eyelid_rig as eyelid
from bbTools.core.utils import rig_utils as bb
from bbTools.core.utils import skin_io as skio


reload(base)
reload(tweaker)
reload(lips)
reload(eb)
reload(eyelid)
reload(bb)
reload(skio)

cmds.hide(['tweaker_bp_grp', 'lips_bp_grp', 'eyebrows_bp_grp', 'eyelid_bp_grp', 'l_eyesocket_bp_grp', 'r_eyesocket_bp_grp'])

face_rig = base.FaceModule()
face_rig.build()
cmds.hide(face_rig.mod_grp)

face_tweaker_rig = tweaker.TweakerRig(
				blueprint_grp = 'tweaker_bp_grp', 
				default_shape = 'crossCircle',
				add_jnts = None,
				name = 'tweakers',
				side = None,
				parent_ctrl_grp = face_rig.ctrl_grp,
				parent_mod_grp = face_rig.mod_grp,
				remove_elem = 'bp'
			)
face_tweaker_rig.build()


# ———————— Add Main Cheek controller
cheek_bp_jnts = ['l_cheek_main_bp_jnt', 'r_cheek_main_bp_jnt']
parent_jnt = 'skull_jnt'
parent_ctrl = 'skull_ctl'
base_name = 'cheek'

for cheek_bp_jnt in cheek_bp_jnts:
	side = parser.find_element(cheek_bp_jnt, 'sides')
	ctrl_posi_loc = cheek_bp_jnt.replace('_bp_jnt', '_posi')
	ctrl_jnt_grp, ctrl_jnt = face_rig.create_rig_joint(ctrl_posi_loc, parent_jnt_grp=parent_jnt, rad=0.25, remove_elem = 'bp', add_elem = None)
	rotate_jnt_grp, rotate_jnt = face_rig.create_rig_joint(cheek_bp_jnt, parent_jnt_grp=parent_jnt, rad=0.25, remove_elem = 'bp', add_elem = 'rotate')
	ctrl_grp, ctrl = face_rig.create_controller(ctrl_posi_loc, 'sparkle', 0.5, [90, 0, 0], [0, 0, 0], 'None', ['zro'], color_set = 'sec', ctrl_grp = parent_ctrl)
	rotate_mul_mdv = bb.create_node('multiplyDivide', base_name, ['main'], None, side)
	cmds.setAttr( f'{rotate_mul_mdv}.i2', 5, -15, 0)
	cmds.connectAttr(f'{ctrl}.tx', f'{rotate_mul_mdv}.i1x')
	cmds.connectAttr(f'{ctrl}.ty', f'{rotate_mul_mdv}.i1y')
	cmds.connectAttr(f'{rotate_mul_mdv}.ox', f'{rotate_jnt}.ry')
	cmds.connectAttr(f'{rotate_mul_mdv}.oy', f'{rotate_jnt}.rx')
	cmds.connectAttr(f'{ctrl}.tx', f'{ctrl_jnt}.tx')
	cmds.connectAttr(f'{ctrl}.ty', f'{ctrl_jnt}.ty')
	ctrl_grps = [f'{side}upper_cheek_in_ctrl_grp', f'{side}upper_cheek_mid_ctrl_grp', f'{side}upper_cheek_out_ctrl_grp']
	cmds.parent(ctrl_grps, ctrl )
	jnt_grps = [f'{side}upper_cheek_in_jnt_grp', f'{side}upper_cheek_mid_jnt_grp', f'{side}upper_cheek_out_jnt_grp']
	cmds.parent(jnt_grps, rotate_jnt )


# main_cheek_bp = 'l_cheek_main_bp_jnt'
# ctrl_posi = 'l_cheek_main_posi'
# parent_jnt = 'skull_jnt'
# parent_ctrl = 'skull_ctl'
# ctrl_grps = ['l_upper_cheek_in_ctrl_grp', 'l_upper_cheek_mid_ctrl_grp', 'l_upper_cheek_out_ctrl_grp']

# main_jnt_grp, main_jnt = face_rig.create_rig_joint(main_cheek_bp, parent_jnt_grp='skull_jnt', rad=0.25, remove_elem = 'bp', add_elem = None)
# ctrl_grp, ctrl = face_rig.create_controller(main_jnt, 'sparkle', 0.5, [90, 0, 0], [0, 0, 0], 'None', ['zro'], color_set = 'sec', ctrl_grp = parent_ctrl)
# bb.snap([ctrl_posi], ctrl_grp[0])
# rotate_mul_mdv = bb.create_node('multiplyDivide', 'cheek', ['main'], None, 'l')
# cmds.setAttr( f'{rotate_mul_mdv}.i2', -5, 5, 0)
# cmds.connectAttr(f'{ctrl}.tx', f'{rotate_mul_mdv}.i1x')
# cmds.connectAttr(f'{ctrl}.ty', f'{rotate_mul_mdv}.i1y')
# cmds.connectAttr(f'{rotate_mul_mdv}.ox', f'{main_jnt}.ry')
# cmds.connectAttr(f'{rotate_mul_mdv}.oy', f'{main_jnt}.rx')


lips_rig = lips.LipRig(blueprint_grp = 'lips_bp_grp', 
				default_shape='crossCircle',
				name = 'lips',
				side = None,
				lip_jnts = ['lip_upper_main_bp_jnt', 'lip_lower_main_bp_jnt'],
				corner_jnts = ['l_lip_corner_bp_jnt', 'r_lip_corner_bp_jnt'],
				nurbs = ['lip_upper_nrb', 'lip_lower_nrb'],
				parent_ctrl_grp=face_rig.ctrl_grp,
				parent_mod_grp=face_rig.mod_grp,
				remove_elem='bp',
				surface_rotation = True
			)
lips_rig.build()
lips_rig.ribbon_rig()

lip_nrbs = ['lip_upper_nrb', 'lip_lower_nrb', 'lip_upper_sec_nrb', 'lip_lower_sec_nrb']
cmds.select(lip_nrbs)
skio.import_skinweight(log=False, prompt = False)

lips_rig.lip_zip_rig()


l_eb_rig = eb.EyebrowRig(
				blueprint_grp = 'eyebrows_bp_grp', 
				default_shape='crossCircle',
				name = 'eyebrow',
				side='l',
				eyebrow_jnts = ['l_eyebrow_in_bp_jnt', 
				'l_eyebrow_in_aux_bp_jnt', 'l_eyebrow_mid_aux_bp_jnt', 
				'l_eyebrow_mid_bp_jnt', 'l_eyebrow_out_aux_bp_jnt', 
				'l_eyebrow_out_bp_jnt'],
				eyebrow_main_jnt = 'l_eyebrow_main_bp_jnt',
				curve  = 'l_eyebrow_crv',
				parent_ctrl_grp='skull_ctl',
				parent_mod_grp=face_rig.mod_grp,
				parent_jnt = 'skull_jnt',
				remove_elem='bp'
			)
l_eb_rig.build()

r_eb_rig = eb.EyebrowRig(
				blueprint_grp = 'eyebrows_bp_grp', 
				default_shape='crossCircle',
				name = 'eyebrow',
				side='r',
				eyebrow_jnts = ['r_eyebrow_in_bp_jnt', 
				'r_eyebrow_in_aux_bp_jnt', 'r_eyebrow_mid_aux_bp_jnt', 
				'r_eyebrow_mid_bp_jnt', 'r_eyebrow_out_aux_bp_jnt', 
				'r_eyebrow_out_bp_jnt'],
				eyebrow_main_jnt = 'r_eyebrow_main_bp_jnt',
				curve  = 'r_eyebrow_crv',
				parent_ctrl_grp='skull_ctl',
				parent_mod_grp=face_rig.mod_grp,
				parent_jnt = 'skull_jnt',
				remove_elem='bp'
			)
r_eb_rig.build()

r_eb_rig.add_mid_ctrl(r_eb_rig.ctrls[0], l_eb_rig.ctrls[0], 'eyebrow_mid_ctl')

l_eyesocket_rig = tweaker.TweakerRig(
				blueprint_grp = 'l_eyesocket_bp_grp', 
				default_shape = 'oval',
				add_jnts = None,
				name = 'eyesocket',
				side = 'l',
				parent_ctrl_grp = 'skull_ctl',
				parent_mod_grp = 'skull_jnt',
				remove_elem = 'bp',
				color_set = 'ter',
				scale = 0.02
			)
l_eyesocket_rig.build()

r_eyesocket_rig = tweaker.TweakerRig(
				blueprint_grp = 'r_eyesocket_bp_grp', 
				default_shape = 'oval',
				add_jnts = None,
				name = 'eyesocket',
				side = 'r',
				parent_ctrl_grp = 'skull_ctl',
				parent_mod_grp = 'skull_jnt',
				remove_elem = 'bp',
				color_set = 'ter',
				scale = 0.02
			)
r_eyesocket_rig.build()


l_eyelid_rig = eyelid.EyelidRig(
				blueprint_grp = 'l_eyelid_bp_grp', 
				name = 'eyelid',
				side='l',
				upper_curve = 'l_eyelid_upper_crv',
				lower_curve = 'l_eyelid_lower_crv',
				mid_curve = 'l_eyelid_mid_crv',
				aim_loc = 'l_eyelid_upper_aim_loc',
				parent_ctrl_grp = 'skull_ctl',
				parent_mod_grp = face_rig.mod_grp,
				parent_jnt = 'skull_jnt',
				remove_elem='bp'
			)
l_eyelid_rig.build()

l_eyelid_rig.add_eye_main_ctrl(ctrl_grps = [l_eyelid_rig.ctrl_grp], jnt_grps = [l_eyelid_rig.jnt_grp], color_set = 'sec')

l_eyelid_rig.eyelash_rig(curve=l_eyelid_rig.upper_curve, name='eyelash', side=l_eyelid_rig.side, eyelid_jnts_grp='l_eyelid_upper_jnt_grp')


r_eyelid_rig = eyelid.EyelidRig(
				blueprint_grp = 'r_eyelid_bp_grp', 
				name = 'eyelid',
				side='r',
				upper_curve = 'r_eyelid_upper_crv',
				lower_curve = 'r_eyelid_lower_crv',
				mid_curve = 'r_eyelid_mid_crv',
				aim_loc = 'r_eyelid_upper_aim_loc',
				parent_ctrl_grp = 'skull_ctl',
				parent_mod_grp = face_rig.mod_grp,
				parent_jnt = 'skull_jnt',
				remove_elem='bp'
			)
r_eyelid_rig.build()
r_eyelid_rig.add_eye_main_ctrl(ctrl_grps = [r_eyelid_rig.ctrl_grp], jnt_grps = [r_eyelid_rig.jnt_grp], color_set = 'sec')
r_eyelid_rig.eyelash_rig(curve=r_eyelid_rig.upper_curve, name='eyelash', side=r_eyelid_rig.side, eyelid_jnts_grp='r_eyelid_upper_jnt_grp')


# ———————— Adding Eyesocket follow attrs
eyesocket_data = [
	('r_eyesocket_in_upper_ctl',  ['r_eyesocket_in_ctl', 'r_eyesocket_mid_upper_ctl'],  'follow'),
	('r_eyesocket_out_upper_ctl', ['r_eyesocket_out_ctl', 'r_eyesocket_mid_upper_ctl'], 'follow'),
	('r_eyesocket_in_lower_ctl',  ['r_eyesocket_in_ctl', 'r_eyesocket_mid_lower_ctl'],  'follow'),
	('r_eyesocket_out_lower_ctl', ['r_eyesocket_out_ctl', 'r_eyesocket_mid_lower_ctl'], 'follow'),
	('r_eyesocket_mid_upper_ctl', ['r_eye_main_ctl', 'r_eyebrow_main_ctl'], 'follow_eyebrow'),
	('r_eyesocket_mid_lower_ctl', ['r_eye_main_ctl', 'r_cheek_main_ctl'], 'follow_cheek')
]

for ctrl, parents, attr in eyesocket_data:
	jnt = ctrl.replace('_ctl', '_jnt')
	follow_grp = bb.create_offset_group([ctrl], [attr])[ctrl][0]
	follow_jnt_grp = bb.create_offset_group([jnt], ['jnt_follow'])[jnt][0]
	bb.add_follow_attr(
		parents=parents, 
		target=follow_grp, 
		attr_name=attr, 
		ctrl=ctrl, 
		min=0, max=1, dv=0.5, 
		multiply=False
	)
	bb.direct_connect([follow_grp], [follow_jnt_grp])

##################################
########## LOWER LID WEIGHT
		
# ============ MIRROR CONTROL ==================

r_ctrls = cmds.ls('r_*_ctl')

for ctrl in r_ctrls:
	opp_ctrl = ctrl.replace('r_', 'l_', 1)
	bc.mirror_ctrl(source = opp_ctrl, target = ctrl, world_space = True, mirror = True, color = False)

# ==============================================

from bbTools.core.utils import skin_io as skio
reload(skio)

sk_objs = ['l_eyebrow_crv', 'r_eyebrow_crv', 
'l_eyelid_upper_crv', 'l_eyelid_lower_crv', 'r_eyelid_upper_crv', 'r_eyelid_lower_crv',
'lashesUpper_local_ply', 'lashesLower_local_ply','body_local_ply', 
'gumUpper_ref_ply', 'teethLower_ref_ply', 'gumLower_ref_ply', 'teethUpper_ref_ply', 'tongue_ref_ply', 'piercings_local_ply']


cmds.select(sk_objs)
skio.import_skinweight(log=False, prompt = False)


