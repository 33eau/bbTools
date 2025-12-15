# p'Pan's joint rename

side_map_dict = {'Lf':'LFT',
				'Rt':'RGT'
				}

joint_grp = 'JntTmp_Grp'
all_joints = cmds.listRelatives(joint_grp, ad=True, type = 'joint') or []
all_joints.insert(0,'Head_0_Tmp_Jnt')
all_joints.reverse()

for jnt in all_joints:
	side = ''
	for side_key, side_val in side_map_dict.items():
		if side_key in jnt:
			side = side_val
			break
			
	element_list = jnt.split('_')
	base_name = element_list[-4]
	# add padding and plus one
	number = str(int(element_list[-3]) + 1).zfill(2)
	
	# convert to camel case
	base_name = base_name[0].lower() + base_name[1:]
	
	jnt=cmds.rename(jnt, f'{base_name}{number}Tmp{side}_jnt')

