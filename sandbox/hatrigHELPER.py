
import maya.cmds as cmds
from functools import partial
def add_suffix(suffix = None, *args):
	objects = cmds.ls(sl=True)
	for obj in objects:
		if '|' in obj:
			name = obj.split('|')[-1]
			cmds.rename(obj, name + suffix)
			
def remover_word(word = None, *args):
	objects = cmds.ls(sl=True)
	for obj in objects:
		name = obj.split('|')[-1] if '|' in obj else obj
		name = name.replace(word, '')
		cmds.rename(obj, name)
			
def rename_offset_group(*args):
	objects = cmds.ls(sl=True)
	group = objects[-1]
	obj = objects[0]
	cmds.rename(group, obj+'_ofs')

cmds.window( width=300 )
cmds.columnLayout( 'main', adjustableColumn=True )
cmds.button( label='rename group', command=rename_offset_group, h=50 )
cmds.rowLayout('function_type', numberOfColumns=2, columnWidth2=(150,150), adjustableColumn=2, columnAlign=(1, 'center'), columnAttach=[(1, 'both', 0), (2, 'both', 0)] )
cmds.text(l='add')
cmds.text(l='remove')
cmds.setParent('main')
cmds.gridLayout(nc=2, ag=True, ch = 50, cw=152)
cmds.button( label='_offs', command=partial (add_suffix, '_offs'), h=50 )
cmds.button( label='_offs', command=partial (remover_word, '_offs'), h=50 )
cmds.button( label='_ctl', command=partial (add_suffix, '_ctl'), h=50 )
cmds.button( label='_ctl', command=partial (remover_word, '_ctl'), h=50 )
cmds.button( label='_bnd', command=partial (add_suffix, '_bnd'), h=50 )
cmds.button( label='_bnd', command=partial (remover_word, '_bnd'), h=50 )
cmds.button( label='_fk', command=partial (add_suffix, '_fk'), h=50 )
cmds.button( label='_fk', command=partial (remover_word, '_fk'), h=50 )
cmds.button( label='_ik', command=partial (add_suffix, '_ik'), h=50 )
cmds.button( label='_ik', command=partial (remover_word, '_ik'), h=50 )
cmds.showWindow()