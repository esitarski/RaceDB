import init_static
import init_categories
from models import *

def init_data():
	init_static.init_static()
	init_categories.init_categories()
	
def init_data_if_necessary():
	if not Discipline.objects.all().exists():
		init_data()
