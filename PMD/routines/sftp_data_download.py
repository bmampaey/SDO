import paramiko
import os
import time
paramiko.util.log_to_file('./paramiko.log')


def get_ssh_client(host_name, user_name, password = None, port = 22, window_size = 134217727, timeout = None):
	'''Create and return an ssh connection to a host'''
	ssh_client = paramiko.SSHClient()
	ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	if password is None: # We let paramiko try to connect to a authentification agent or find a private key_file in ~/.ssh
		ssh_client.connect(host_name, port = port, username = user_name, timeout=timeout)
	elif os.path.isfile(password): # If password is a file we assume it is a key_filename
		ssh_client.connect(host_name, port = port, username = user_name, key_filename=password, timeout=timeout)
	else: # If a private key_file in ~/.ssh needs a password it will be used, otherwise it will use the password directly
		ssh_client.connect(host_name, port = port, username = user_name, password=password, timeout=timeout)
	
	# Increasing the window size may increase the speed but is more risky
	if window_size is not None:
		ssh_client._transport.window_size = window_size
	
	return ssh_client

def sftp_download(ssh_client, source, destination, log = None):
	'''Download the files passed in sources_destinations using sftp'''
	if log is not None:
		log.debug("Copying %s to %s", source, destination)
		start = time.time()
	
	sftp = ssh_client.open_sftp()
	sftp.get(source, destination)
	
	if log is not None:
		log.debug("Download of file %s took %s seconds", source, time.time() - start)
	
	sftp.close()

