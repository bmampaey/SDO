import os, errno
import subprocess

def create_png(fits_file_name, image_file_name, parameters, executable = "fits2png.x", log = None):
	"""Call fits2png to convert a fits file to a png image
		parameters is a dictionary of arguments to pass to fits2png , see "fits2png -h" to get the possible values
	"""
	output_directory = os.path.dirname(image_file_name)
	if not output_directory:
		output_directory = "."
	
	# Create the directory tree for the image
	try:
		os.makedirs(output_directory)
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	output_file = os.path.join(output_directory, os.path.splitext(os.path.basename(fits_file_name))[0] + "." + parameters.get("type", "png"))
	
	# Create the command
	command = [executable, fits_file_name, "-O", output_directory]
	for arg, value in parameters.iteritems():
		command.extend(["--%s" % arg, str(value)])
	if log:
		log.debug("Running command: ", " ".join(command))
	
	# Execute the command
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output, error = process.communicate()
	if log:
		log.debug("Command \"%s\" output: %s; error: %s; returncode:%s", " ".join(command), output, error, process.returncode)
	if process.returncode !=0:
		raise Exception("Error running command %s. output: %s; error: %s; returncode:%s" % (" ".join(command), output, error, process.returncode))
	
	# Rename the output_file to image_file_name
	if output_file != image_file_name:
		os.rename(output_file, image_file_name)
