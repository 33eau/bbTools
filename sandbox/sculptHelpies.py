
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
def sculpt_tool(*args):
	mel.eval(f'SetMeshSculptTool; toolPropertyWindow;')  
	
def set_brush(brush, *args):
	mel.eval(f'setMeshSculptTool "{brush}"')  
	
def UI():
	BG_COLOR = (0.102, 0.11, 0.141)
	SUB_COLOR = (0.145, 0.149, 0.18)
	ACCENT_COLOR = (0.8, 0.102, 0.702)
	
	if(cmds.window('sculpt_brush',q=1,ex=1)):cmds.deleteUI('sculpt_brush')
	cmds.window( 'sculpt_brush', width=200, t='Sculpt Brush', bgc=BG_COLOR)
	cmds.columnLayout( 'main', adjustableColumn=True )
	cmds.button( label='SCULPT TOOLS', command=sculpt_tool, h=50 )
	cmds.rowLayout('function_type', h=4, bgc=ACCENT_COLOR )
	cmds.setParent('main')
	cmds.gridLayout(nc=2, ag=True, ch = 50, cw=152)
	cmds.button( label='Smooth', command=partial (set_brush, 'Smooth'), h=50, ann='Smooth the surface of a mesh.' )
	cmds.button( label='Relax', command=partial (set_brush, 'Relax'), h=50, ann='Smooth the surface of a mesh without changing its original shape.' )
	cmds.button( label='Grab', command=partial (set_brush, 'Grab'), h=50, ann='Pull a single vertex along a surface in any direction')
	cmds.button( label='Pinch', command=partial (set_brush, 'Pinch'), h=50, ann='Sharpen soft edges' )
	cmds.button( label='Flatten', command=partial (set_brush, 'Pull'), h=50, ann='Level a surface' )
	cmds.button( label='Wax', command=partial (set_brush, 'Wax'), h=50, ann = 'Build up a surface' )
	cmds.button( label='Fill', command=partial (set_brush, 'Fill'), h=50, ann='Fill in the valleys on a surface' )
	cmds.button( label='Smear', command=partial (set_brush, 'Smear'), h=50, ann='Pull a surface in the direction of the stroke' )
	cmds.button( label='Bulge', command=partial (set_brush, 'Bulge'), h=50, ann = 'Inflate an area on a surface' )
	cmds.button( label='Freeze', command=partial (set_brush, 'Freeze'), h=50, ann='Paint areas of a surface to prevent further modification' )
	cmds.showWindow()
		
UI()