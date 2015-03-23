from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as user_login
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse

from account.forms import EmailLoginForm

@require_http_methods(["GET", "POST"])
def login(request):
	#import pdb; pdb.set_trace()
	if request.method == 'GET':
		form = EmailLoginForm(request.GET)
	
	elif request.method == 'POST':
		form = EmailLoginForm(request.POST)
	
	if form.is_valid() and "email" in form.cleaned_data:
		username, password = form.cleaned_data["email"].split("@", 1)
		user = authenticate(username=username, password=password)
		if user is None:
			# Register the user
			try:
				User.objects.create_user(username, email=form.cleaned_data["email"], password=password)
			except IntegrityError, why:
				return render(request, 'account/login.html', {"form": EmailLoginForm(), "error": "It seems you have opened an account previously with another email. Please use that email or contact the administrator sdoadmin@oma.be"})
			else:
				user = authenticate(username=username, password=password)
		if user.is_active:
			user_login(request, user)
			if "next" in request.GET:
				return redirect(request.GET["next"])
			else:
				return redirect(reverse("wizard:index"))
		else:
			return render(request, 'account/login.html', {"form": EmailLoginForm(), "error": "Your account is inactive. Please contact the administrator sdoadmin@oma.be"})
	
	else:
		return render(request, 'account/login.html', {"form": EmailLoginForm()})
