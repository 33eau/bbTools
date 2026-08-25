import maya.cmds as cmds
from functools import partial
from importlib import reload
from bbTools.core.utils import rig_utils as bb
from bbTools.core.controllers import shape_color
reload(bb)
reload(shape_color)

COLORS = shape_color.COLORS

def set_color_wrapper(color, viewport_checkBox, outliner_checkBox, *args):
	viewport_checked = cmds.checkBox(viewport_checkBox, q=True, value=True)
	outliner_checked = cmds.checkBox(outliner_checkBox, q=True, value=True)

	bb.set_color(color=color, viewport=viewport_checked, outliner=outliner_checked)

def reset_color_wrapper( viewport_checkBox, outliner_checkBox, reset_all, *args):
	viewport_checked = cmds.checkBox(viewport_checkBox, q=True, value=True)
	outliner_checked = cmds.checkBox(outliner_checkBox, q=True, value=True)

	bb.reset_color(viewport=viewport_checked, outliner=outliner_checked, reset_all = reset_all)

def UI():
	window_name = "bbColorPalette"
	if cmds.window(window_name, exists = True):
		cmds.deleteUI(window_name, window = True)
	
	BG_COLOR = (0.145, 0.149, 0.18)
	RESET_ALL_COLOR = (0.8, 0.102, 0.702)
	RESET_COLOR = (0.102, 0.11, 0.141)

	cmds.window(window_name, title='bbColorPalette', w = 400, h = 117, sizeable=True, bgc=BG_COLOR)
	main_layout = cmds.columnLayout(adjustableColumn=False)

	window_type = cmds.rowLayout('windowType', nc = 2, columnWidth2=(200,200),columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 0)])
	
	viewport_checkBox = cmds.checkBox( label='Viewport', align='left', v=True )
	outliner_checkBox = cmds.checkBox( label='Outliner', align='right' )

	cmds.setParent(window_type)

	cmds.gridLayout(nc = 15, nr =5, cellWidthHeight=(30, 30), p=main_layout)
	for col in COLORS.keys():
		cmds.button( label='', bgc = COLORS[col], c = partial( set_color_wrapper, col, viewport_checkBox, outliner_checkBox ), statusBarMessage = col, annotation = col)
	
	cmds.setParent(main_layout)
	reset_type = cmds.rowLayout('resetType', nc = 2, columnWidth2=(223.5,223.5),columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 0)])
	cmds.iconTextButton(style='textOnly',label = 'RESET', c= partial( reset_color_wrapper, viewport_checkBox, outliner_checkBox, reset_all=False), h = 35, fn = 'plainLabelFont', bgc=RESET_COLOR)
	cmds.iconTextButton(style='textOnly',label = 'RESET ALL', c= partial( bb.reset_color, viewport=True, outliner=True, reset_all=True), h = 35, fn = 'boldLabelFont', bgc = RESET_ALL_COLOR)
	
	cmds.showWindow(window_name)

	