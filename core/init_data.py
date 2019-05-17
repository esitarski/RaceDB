from .models import *
from . import init_static
from . import init_categories

def init_data():
	init_static.init_static()
	init_categories.init_categories()
	
def init_data_if_necessary():
	if not Discipline.objects.all().exists():
		init_data()
