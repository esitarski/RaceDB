from django.db import connection

def migrate_data():
	cursor = connection.cursor()
	try:
		cursor.execute('''ALTER TABLE core_systeminfo ADD COLUMN reg_closure_minutes INTEGER DEFAULT -1''')
	except:
		pass
		
migrate_data()