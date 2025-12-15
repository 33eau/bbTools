import re
from importlib import reload

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
		mid_side = parser.format_side(side, 'upper')
		if mid_side == 'M':
			formatted_side = ''
		if element:
			if len(element) > 1:
				elem_cap = [s.lower() for s in element]
				element_str = '_'.join(elem_cap)
			else:
				element_str = element[0].lower() if element else ''
		else: 
			element_str = ''
		
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
	
	def _cleanup_name(self, name):
		name = re.sub('_+','_', name).strip('_')
		return name