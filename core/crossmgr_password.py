from .views_common import *

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CrossMgrPasswordDisplay( request ):
	crossmgr_passwords = CrossMgrPassword.objects.all()
	return render( request, 'crossmgr_password_list.html', locals() )

@autostrip
class CrossMgrPasswordForm( ModelForm ):
	class Meta:
		model = CrossMgrPassword
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', EDIT_BUTTONS )
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col(Field('password', size=32), 4),
				Col(Field('description', size=80), 8),
			),
		)
		addFormButtons( self, button_mask )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CrossMgrPasswordNew( request ):
	return GenericNew( CrossMgrPassword, request, CrossMgrPasswordForm )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CrossMgrPasswordEdit( request, crossMgrPasswordId ):
	return GenericEdit( CrossMgrPassword, request, crossMgrPasswordId, CrossMgrPasswordForm )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CrossMgrPasswordDelete( request, crossMgrPasswordId ):
	return GenericDelete( CrossMgrPassword, request, crossMgrPasswordId, CrossMgrPasswordForm )

#-----------------------------------------------------------------------

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CrossMgrLogDisplay( request ):
	crossmgr_logs = CrossMgrLog.objects.all().order_by('-timestamp')
	return render( request, 'crossmgr_log_list.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CrossMgrLogClear( request ):
	CrossMgrLog.objects.all().delete()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
