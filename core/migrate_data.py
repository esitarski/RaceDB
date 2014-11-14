from django.db import connection

def migrate_data():
	cursor = connection.cursor()
	try:
		cursor.execute('''ALTER TABLE core_systeminfo ADD COLUMN reg_closure_minutes INTEGER DEFAULT -1''')
	except Exception as e:
		# print e
		pass
		
migrate_data()