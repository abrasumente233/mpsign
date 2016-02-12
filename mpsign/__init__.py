import pkgutil

__package__ = 'mpsign'
__version__ = pkgutil.get_data(__package__, 'VERSION').decode('ascii').strip()
