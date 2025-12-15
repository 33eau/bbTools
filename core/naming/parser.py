import re
from . import templates
import importlib

importlib.reload (templates)

def normalize_side(side):
	# Return only L/R from the provided side letters
	if not side:
		return None
	side = side.strip()
	for key, variants in templates.SIDE_GROUPS.items():
		if side in variants:
			return key
	return None

def format_side(side, style='3upper'):
	base = normalize_side(side)
	if not base:
		return side
	return templates.SIDE_OUTPUT[base][style]

def find_element(full_name, element_list = templates.ELEMENTS):

	if element_list == 'sides':
		pattern_string = r'((?:^|[_])([lr]_)|(LFT|RGT))'
		pattern = re.compile(f'({pattern_string})', re.IGNORECASE)
		match = pattern.search(full_name)
		match = match.group(0) if match else None
	else:
		pattern_string = '|'.join(element_list)
		pattern = re.compile(f'({pattern_string})', re.IGNORECASE)
		match = pattern.findall(full_name)

	if match:
		return match
	else:
		return None

def find_number(full_name, base_number=False):
	pattern = re.compile(r'\d+')
	match = pattern.findall(full_name)
	if match:
		if base_number:
			if len(match) > 1:
				match = match[0]
			else:
				match = ''
		else:
			match = match[-1] if match else ''
		return match
	else:
		return None

def clean_name(full_name, element):
	if not element:
		return full_name
	else:
		if isinstance(element, list):
			for elem in element:
				full_name = full_name.replace(elem, '_', 1)
		else:
			full_name = full_name.replace(element, '_', 1)

	new_name = re.sub('_+','_', full_name).strip('_')
	return new_name

def get_base_name(full_name, base_number = True):
	side = find_element(full_name, 'sides')
	elem = find_element(full_name, element_list = templates.ELEMENTS)
	suffix = get_suffix(full_name) if '_' in full_name else None
	components = [side, elem, suffix]
	num = find_number(full_name, base_number=base_number)
	
	if components:
		for comp in components:
			full_name = clean_name(full_name, comp)
	base_name = full_name
	if num:
		if base_number:
			base_name = full_name+num
		else:
			base_name = clean_name(full_name, num)
	
	return base_name

def get_suffix(full_name):
	suffix = full_name.split('_')[-1]
	return suffix


# full_name = 'l_ball_fk_jnt'
# side = find_element(full_name, 'sides')
# format_side = format_side(side, 'upper')
# print(format_side)


