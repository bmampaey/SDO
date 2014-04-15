import paramiko
import os
import logging
import time
paramiko.util.log_to_file('./paramiko.log')


def get_ssh_client(host_name, user_name, password = None, port = 22, timeout = None):
	'''Create and return ssh connection to a host'''
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	if password is None: # We let paramiko try to connect to a authentification agent or find a private key_file in ~/.ssh
		ssh.connect(host_name, port = port, username = user_name, timeout=timeout)
	elif os.path.isfile(password): # If password is a file we assume it is a key_filename
		ssh.connect(host_name, port = port, username = user_name, key_filename=password, timeout=timeout)
	else: # If a private key_file in ~/.ssh needs a password it will be used, otherwise it will use the password directly
		ssh.connect(host_name, port = port, username = user_name, password=password, timeout=timeout)
	return ssh

def sftp_download(sources_destinations, host_name, user_name, password = None, port = 22, timeout = None, window_size = 134217727, log = logging):
	'''mahe a ftp connection to host_name and download the files passed in sources_destinations'''
	log.debug("Connecting to host %s", host_name)
	ssh = get_ssh_client(host_name, user_name, password, port, timeout)
	
	# Increasing the window size may increase the speed but is more risky
	if window_size is not None:
		logging.debug("Setting sftp window size to %s", window_size)
		ssh._transport.window_size = window_size
	
	sftp = ssh.open_sftp()
	local_files = []
	for source, destination in sources_destinations:
		log.debug("Copying %s to %s", source, destination)
		start = time.time()
		try:
			sftp.get(source, destination)
		except Exeption, why:
			local_files.append((destination, why))
		else:
			local_files.append((destination, None))
		log.debug("Download of file %s took %s seconds", source, time.time() - start)
	sftp.close()
	ssh.close()
	return local_files
