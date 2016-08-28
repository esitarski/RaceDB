from django.contrib.auth.models import User

def create_users():
	if not User.objects.filter(username__exact='serve').exists():
		serve = User.objects.create_user('serve', password='serve')

	if not User.objects.filter(username__exact='reg').exists():
		reg = User.objects.create_user('reg', password='reg')
		reg.is_staff = True
		reg.save()
	
	if not User.objects.filter(username__exact='super').exists():
		root = User.objects.create_user('super', password='super')
		root.is_staff = True
		root.is_superuser = True
		root.save()
