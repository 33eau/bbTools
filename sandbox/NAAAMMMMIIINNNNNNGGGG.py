# import re
# full_name = 'arm08_02_l_ctrl'

# pattern = re.compile(r'\d+')
# match = pattern.findall(full_name)[-1]
# print(match)


# from bbTools.core import bbNaming as bn
# reload(bn)

# name = bn.auto_name('l_spine_01_fk_ctl', template = 'default', side_case = '3upper')
# print(name)


# for jnt in ['spine01FkLFT_ctrl', 'spine02FkLFT_ctrl', 'spine03FkLFT_ctrl', 'spine04FkLFT_ctrl']:
# 	base, elem, side, num, suffix = bn.extract_name(jnt)
# 	elems = [elem]
# 	elems.append('offs') ######## ['Zro', 'Offset', ใดๆ]
# 	group_name = bn.format_name(base+num, side, elems, 'grp', template='hatrig', side_case='lower')
# 	print(group_name)

import sys
path = r"w:\RIG\LIB"
if not path in sys.path:
	sys.path.append(path)
	
from bbTools.core.naming import factory as fc
from bbTools.core.naming import helper as hp
from bbTools.core.naming import config
import importlib
importlib.reload(fc)
importlib.reload(hp)

# namer = fc.get_namer("hatrig")
# result = namer.format("arm", ["fk", 'offset'], "01", "L", "grp")
					#(base, element, number, side, suffix))
#assert result == "armFk01LFT_ctrl"

# old_name = 'armFk01LFT_ctrl'
# namer = fc.get_namer("default")
# new_name = namer.extract(old_name)
# print(new_name)



# full_name = 'spine02__Fk01___LFT_jnt'
# namer = fc.get_namer("default")
# new_name = namer.auto(full_name)
# # new_name= hp.get_base_name(full_name)
# print(new_name)