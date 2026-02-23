import re
from importlib import reload
import maya.cmds as cmds

from . import base_namer
from . import parser
from . import templates

reload(base_namer)
reload(parser)

BaseNamer = base_namer.BaseNamer

class HatRigNamer(BaseNamer):
	'''
		Default naming convention: 
		e.g., l_arm_fk_01_ctrl
	'''
	template = templates.NAME_TEMPLATES["side_prefix"]
	side_case = 'lower'

	def extract(self, full_name):
		base = parser.get_base_name(full_name, base_number = False)
		element = parser.find_element(full_name, templates.ELEMENTS)
		number = parser.find_number(full_name)
		side = parser.find_element(full_name, 'sides')
		suffix = parser.get_suffix(full_name)

		return (base, element, number, side, suffix)
	
	def format(self, base, element, number=None, side=None, suffix=None):
		
		formatted_side = parser.format_side(side, self.side_case)
		mid_side = parser.format_side(side, self.side_case)
		formatted_side = '' if mid_side == 'M' or mid_side == 'm' else mid_side
		if element is not None:
			if len(element) > 1:
				elem_cap = [s.lower() for s in element]
				element_str = '_'.join(elem_cap)
			else:
				element_str = element[0].lower() if len(list(element)) > 0 else ''

		# split names by upper case
		word_range = []
		for i, letter in enumerate (base):
			if letter.isupper():
				word_range.append(i)
		word_range.append(len(base))

		names = []
		start_idx = 0
		for i, idx in enumerate(word_range):
			end_idx = word_range[i]
			split_name = base[start_idx:end_idx].lower()
			names.append(split_name)
			start_idx = idx

		base = '_'.join(names)
		
		context = {
			'base': base,
			'element': element_str or '',
			'number': str(number) if number is not None else '',
			'side': formatted_side or '',
			'suffix': suffix or ''
		}
		name = self.template.format(**context)
		name = self._cleanup_name(name)

		return name
	
	def auto(self, full_name):
		base, element, number, side, suffix = self.extract(full_name)
		name =  self.format(base, element, number, side, suffix)
		# cleanup
		new_name = self._cleanup_name(name)
		
		cmds.rename(full_name, new_name)
		return name

	def _cleanup_name(self, name):
		name = re.sub('_+','_', name).strip('_')
		return name