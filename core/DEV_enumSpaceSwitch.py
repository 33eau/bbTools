def add_enum_space_switch( parent_spaces = ['r_pelvis_ctl'],
							world_space = 'r_global_gimbal_space_grp',
							attr_name = 'follow',
							spaces_name = ['local', 'world'],
							target = 'r_thigh_fk_offset_grp',
							ctrl = 'r_thigh_fk_ctl',
							type = 'orient',
							default_index = 1
						):#25Dec09

	target_name, target_element, target_number, target_side, suffix = NAMER.extract(target) 
	parents = parent_spaces

	if world_space:
		base, element, number, side, suffix = NAMER.extract(world_space) 
		space_grp = NAMER.format(base, ['space'], number, target_side, 'grp' )
		if not cmds.objExists(space_grp):
			space_grp = bb.create_node('group', base, ['space'], number, target_side )
			cmds.matchTransform(space_grp, world_space)

			target_side = parser.find_element(target, 'sides')
			format_side = parser.format_side(target_side, 'upper')
			if format_side == 'R':
				inv_sx_mtx = [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0,0, 0, 0, 1]
				cmds.setAttr(f'{space_grp}.offsetParentMatrix', inv_sx_mtx, type='matrix')
			cmds.parent(space_grp, world_space)
		world_space = space_grp
		parents.append(world_space)

	parent_con = bb.create_constrain(parents, target, type=type, maintain_offset=True)[0][0]
	cmds.setAttr(f'{parent_con}.interpType', 2)

	enum_names = ':'.join(spaces_name)
	cmds.addAttr(ctrl, ln = attr_name, at='enum', en=enum_names, dv=default_index, k=True )
	for i, name in enumerate(spaces_name):
		space_cdt = bb.create_node(node_type='condition', base=target_name, elements=[name], number=target_number, side=target_side )
		cmds.setAttr( f'{space_cdt}.st', i)
		cmds.setAttr( f'{space_cdt}.ctr', 1)
		cmds.setAttr( f'{space_cdt}.cfr', 0)
		cmds.connectAttr(f'{ctrl}.{attr_name}', f'{space_cdt}.ft')
		cmds.connectAttr(f'{space_cdt}.ocr', f'{parent_con}.{parents[i]}W{i}')
		
		
		
		

		
		
		