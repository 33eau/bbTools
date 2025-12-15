import re
from importlib import reload

from . import base_namer
from . import parser
from . import templates

reload(base_namer)
reload(parser)

BaseNamer = base_namer.BaseNamer

class DefaultNamer(BaseNamer):
	"""
	Default naming convention: 
	e.g., armFk01LFT_ctrl
	'default': '{base}{number}{element}{side}_{suffix}',
	"""
	template = templates.NAME_TEMPLATES["default"]
	side_case = "3upper"

	def extract(self, full_name):
		"""
			Extract components using helpers.
		"""
		base = parser.get_base_name(full_name, base_number = False)
		if '_' in base:
			names = base.split('_')
			names = [s.capitalize() for s in names]
			base = ''.join(names)
		element = parser.find_element(full_name, templates.ELEMENTS)
		number = parser.find_number(full_name)
		side = parser.find_element(full_name, 'sides')
		suffix = parser.get_suffix(full_name)

		return (base, element, number, side, suffix)

	def format(self, base, element, number, side, suffix):
		formatted_side = parser.format_side(side, self.side_case)
		mid_side = parser.format_side(side, 'upper')
		if mid_side == 'M':
			formatted_side = ''
		if element:
			if len(element) > 1:
				elem_cap = [s.capitalize() for s in element]
				element_str = ''.join(elem_cap)
			else:
				element_str = element[0].capitalize() if element else ''
		else:
			element_str = ''

		context = {
			'base': parser.get_base_name(base, base_number = False),
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

