from django.views.generic.edit import FormView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

from account.forms import EmailLoginForm

class EmailLoginView(FormView):
	template_name = 'account/login.html'
	form_class = EmailLoginForm
	#TODO replace by url resolver
	success_url = '/wizard/'
	
	def form_valid(self, form):
		username, password = form.cleaned_data["email"].split("@", 1)
		#import pdb; pdb.set_trace()
		user = authenticate(username=username, password=password)
		if user is None:
			# Register the user
			User.objects.create_user(username, email=form.cleaned_data["email"], password=password)
			user = authenticate(username=username, password=password)
		if user.is_active:
			login(self.request, user)
		
		return super(EmailLoginView, self).form_valid(form)
