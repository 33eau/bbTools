path = 'W:/RIG/PROJ/MAYA_PROJ/JINXIE/autoRig/work/face_start.ma'
cmds.file(path, open=True, f=True)


from bbTools.rigs.face import base
from bbTools.rigs.face import tweaker_rig as tweaker
from bbTools.rigs.face import lips_rig as lips
from bbTools.rigs.face import eyebrow_rig as eb
from bbTools.rigs.face import eyelid_rig as eyelid

reload(base)
reload(tweaker)
reload(lips)
reload(eb)
reload(eyelid)

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


lips_rig = lips.LipRig(blueprint_grp = 'lips_bp_grp', 
				default_shape='crossCircle',
				name = 'lips',
				side = None,
				lip_jnts = ['lip_upper_main_bp_jnt', 'lip_lower_main_bp_jnt'],
				corner_jnts = ['l_lip_corner_bp_jnt', 'r_lip_corner_bp_jnt'],
				nurbs = ['lip_upper_nrb', 'lip_lower_nrb'],
				parent_ctrl_grp=face_rig.ctrl_grp,
				parent_mod_grp=face_rig.mod_grp,
				remove_elem='bp'
			)
lips_rig.build()
lips_rig.ribbon_rig()

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
				parent_mod_grp = face_rig.mod_grp,
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
				parent_mod_grp = face_rig.mod_grp,
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
				aim_loc = 'l_eyelid_aim_loc',
				parent_ctrl_grp = 'skull_ctl',
				parent_mod_grp = face_rig.mod_grp,
				remove_elem='bp'
			)
l_eyelid_rig.build()

r_eyelid_rig = eyelid.EyelidRig(
				blueprint_grp = 'r_eyelid_bp_grp', 
				name = 'eyelid',
				side='r',
				upper_curve = 'r_eyelid_upper_crv',
				lower_curve = 'r_eyelid_lower_crv',
				mid_curve = 'r_eyelid_mid_crv',
				aim_loc = 'r_eyelid_aim_loc',
				parent_ctrl_grp = 'skull_ctl',
				parent_mod_grp = face_rig.mod_grp,
				remove_elem='bp'
			)
r_eyelid_rig.build()



		
# ============ MIRROR CONTROL ==================

r_ctrls = cmds.ls('r_*_ctl')

for ctrl in r_ctrls:
	opp_ctrl = ctrl.replace('r_', 'l_', 1)
	bc.mirror_ctrl(source = opp_ctrl, target = ctrl, world_space = True, mirror = True, color = False)

# ==============================================

from bbTools.core.utils import skin_io as skio
reload(skio)

sk_objs = ['l_eyebrow_crv', 'r_eyebrow_crv', 'lip_upper_nrb', 'lip_lower_nrb', 'lip_upper_sec_nrb', 'lip_lower_sec_nrb', 
'l_eyelid_upper_crv', 'l_eyelid_lower_crv', 'r_eyelid_upper_crv', 'r_eyelid_lower_crv',
'lashesUpper_local_ply', 'lashesLower_local_ply', 'body_local_ply', 
'gumUpper_ref_ply', 'teethLower_ref_ply', 'gumLower_ref_ply', 'teethUpper_ref_ply', 'tongue_ref_ply', 'piercings_local_ply']


cmds.select(sk_objs)
skio.import_skinweight(log=False, prompt = False)