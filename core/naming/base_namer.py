import re

class BaseNamer:
	"""
	Abstract base class for all namers.
	Defines the interface for extracting and formatting names.
	"""

	@classmethod
	def extract(full_name):
		"""
		Extract components from a full name string.
		Must return:
			base: str
			element: str
			number: str
			side: str
			suffix: str
		"""
		pass
	@classmethod
	def format(base, element, number, side, suffix):
		"""
		Format a name from components according to the Namer's template.
		"""
		pass
	
	def auto(self, full_name):
		"""
		Universal auto-naming workflow:
		1. Extract components
		2. Format name using subclass template
		"""
		base, element, number, side, suffix = self.extract(full_name)
		name =  self.format(base, element, number, side, suffix)
		# cleanup
		name = self._cleanup_name(name)

		return name
	
	def _cleanup_name(self, name):
		name = re.sub('_+','_', name).strip('_')
		return name