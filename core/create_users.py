from django.contrib.auth.models import User

def create_users():
	if not User.objects.filter(username__exact='serve').exists():
		serve = User.objects.create_user('serve', password='serve')
		serve.save()

	if not User.objects.filter(username__exact='reg').exists():
		reg = User.objects.create_user('reg', password='reg')
		reg.is_staff = True
		reg.save()
	
	if not User.objects.filter(username__exact='hub').exists():
		hub = User.objects.create_user('hub', password='hub')
		hub.save()
	
	if not User.objects.filter(username__exact='super').exists():
		root = User.objects.create_user('super', password='super')
		root.is_staff = True
		root.is_superuser = True
		root.save()
	
	if not User.objects.filter(username__exact='support').exists():
		support = User.objects.create_user('support', password=None)
		support.is_staff = True
		support.is_superuser = True
		support.save()
