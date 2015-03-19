#!/usr/bin/env python
from __future__ import absolute_import
import os, errno
from celery.utils.log import get_task_logger

from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from account.models import UserMessage

from tasks import app

log = get_task_logger("SDO")

@app.task
def delete_file(file_path):
	log.debug("delete_file %s", file_path)
	try:
		os.remove(file_path)
	except OSError as why:
		if why.errno != errno.ENOENT:
			raise

@app.task
def check_file_exists(file_path):
	log.debug("check_file_exists %s", file_path)
	return os.path.exists(file_path)

@app.task
def get_hard_link_count(file_path):
	return os.stat(file_path).st_nlink

@app.task
def create_link(file_path, link_path, soft = False, force = False):
	log.debug("create_link %s -> %s", link_path, file_path)
	
	# Create the directory tree
	try:
		os.makedirs(os.path.dirname(link_path))
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	# If forced and the link exists, remove it first
	if force and os.path.lexists(link_path):
		try:
			os.remove(link_path)
		except OSError, why:
			if why.errno != errno.ENOENT:
				raise
	
	# Make the link
	if soft:
		os.symlink(file_path, link_path)
	else:
		os.link(file_path, link_path)

@app.task
def send_message(subject_template, content_template, user, level = "INFO", kwargs={}, by_mail = False, copy_to_admins = False):
	log.debug("send_message %s, %s, %s", subject, content, user)
	
	subject = render_to_string(subject_template, kwargs)
	content = render_to_string(content_template, kwargs)
	UserMessage.objects.create(user = user, subject = subject, content = content, level = level)
	
	if by_mail == True:
		to = [user.email]
		if copy_to_admins:
			to += [admin[1] for admin in settings.ADMINS]
		
		mail.send_mail(subject.replace("\n", " "), content, None, to)


@app.task
def update_request_status(request, status):
	log.debug("update_request_status %s, %s", request, status)
	
	request.status = status
	request.save()
