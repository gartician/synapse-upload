import synapseclient
import os
import sys
import logging
import argparse

def parse_args():

	# Define program arguments
	parser = argparse.ArgumentParser()

	# input/output file options
	parser.add_argument("-f", "--folder", help = "Input folder for upload to Synapse", required = True, type = str)
	parser.add_argument("-s", "--syn", help = "Synapse project id (syn123) to upload entire folder to", required = True, type = str)
	parser.add_argument("-v", "--verbose", help = "Run the program in verbose mode. Basically prints out folder and file synapse IDs.", type = str)

	args = parser.parse_args()

	return(args)


def setup_log():

	# Set up logging format = '[DATE] [TIME] [LEVEL]: [MSG]'
	FORMAT = '%(asctime)s [%(levelname)s]: %(message)s'
	DATE = "[%Y-%m-%d] [%I:%M:%S]"

	# Set up logging configuration to file and stdout
	logging.basicConfig(
		level = logging.INFO,
		format = FORMAT,
		datefmt = DATE,
		handlers = [
			# logging.FileHandler(logfile, mode = 'w'),
			logging.StreamHandler(sys.stdout)
			]
		)

# mirror local folder structure in synapse
synapse_folder_id = dict()

"""

synapse_folder_id 
	STRUCTURE: {full path to folder: (basename, synID)}

{
	"synapse-example": ("synapse-example", syn0),
	"synapse-example/folder-3": ("folder-3", syn1),
	"synapse-example/folder-3/folder-4": ("folder-4", syn2),
	"synapse-example/folder-3/folder-5": ("folder-5", syn3),
	"synapse-example/folder-3/folder-6": ("folder-6", syn4),
	"synapse-example/folder-2": ("folder-2", syn5)
	"synapse-example/folder-1/folder-4": ("folder-4", syn6)
	"synapse-example/folder-1/folder-5": ("folder-5", syn7)
	"synapse-example/folder-1/folder-6": ("folder-6", syn8)
}

The full path to folder is needed when the same folder name (e.g. folder-4) appears across multiple folders (folder-1 and folder-3).
The synapse ID is obtained after running the synapseclient.Folder() function. 
The synapse ID is the PARENT folder that specifies where to create a folder/upload a file.

"""

def mirror_folders(local_folder: str, project_id: str):

	"""

	This function will faithfully recreate the local, nested directory structure in Synapse.
	Each path will be marked by its own synapse ID using a `synapse_folder_id` dictionary.

	ASSUMPTION: assumes that the parent folder must be listed before the child!
	Please monitor the output of os.walk if there are any problems. 

	GOOD EXAMPLE:
		synapse-example
		synapse-example/folder-3
		synapse-example/folder-3/folder-4
		synapse-example/folder-3/folder-5
		synapse-example/folder-3/folder-6
		synapse-example/folder-2
		synapse-example/folder-1
		synapse-example/folder-1/folder-4
		synapse-example/folder-1/folder-5
		synapse-example/folder-1/folder-6

	BAD EXAMPLE:
		synapse-example/folder-3/folder-4
		synapse-example/folder-3/folder-5
		synapse-example/folder-3/folder-6
		synapse-example/folder-3
		synapse-example/folder-2
		synapse-example/folder-1/folder-4
		synapse-example/folder-1/folder-5
		synapse-example/folder-1/folder-6
		synapse-example/folder-1
		synapse-example

	"""

	for dirpath, dirnames, filenames in os.walk(local_folder):
		
		# create top folder directory
		if os.path.dirname(dirpath) == "":

			top_folder = synapseclient.Folder(dirpath, parent=project_id)
			top_folder = syn.store(top_folder)
			synapse_folder_id[dirpath] = ("", top_folder.id)
		
		# upload all sub-folders
		else:

			# define bname and dname
			bname = os.path.basename(dirpath)
			dname = os.path.dirname(dirpath)

			# specify the parent folder's synapse ID
			parent_folder = synapse_folder_id[dname][1]

			# create the current folder right underneath the parent folder
			logging.info("Creating " + dirpath + " in Synapse")
			g = synapseclient.Folder(bname, parent = parent_folder)
			g = syn.store(g)

			# update folder-synapse ID relationship!
			synapse_folder_id[dirpath] = (bname, g.id)

def upload_files(local_folder):

	"""
	
	Uploads all the files into the respective parent folder using the filename, dirname, and the folder-synapse ID relationship previously formed.

	"""

	for dirpath, dirnames, filenames in os.walk(local_folder):

		if len(filenames) > 0:

			for file in filenames:
				
				# don't upload these files
				if file in [".DS_Store", "CredDB.CEF"]:
					continue

				# define path, name of file, and parent
				full_path = os.path.join(dirpath, file)
				p = synapse_folder_id[dirpath][1]

				# upload the file
				logging.info("Uploading " + os.path.join(full_path) + " to Synapse")
				f = synapseclient.File(path = full_path, name = file, parent = p)
				f = syn.store(f)

if __name__ == "__main__":

	# setup stdout logging
	setup_log()

	# log into Synapse
	logging.info("this program assumes you use a personal access token with a ~/.synapseConfig file to log into Synapse.")
	logging.info("personal access tokens: https://help.synapse.org/docs/Managing-Your-Account.2055405596.html#ManagingYourAccount-PersonalAccessTokens")
	logging.info("~/.synapseConfig configuration: https://help.synapse.org/docs/Client-Configuration.1985446156.html")
	syn = synapseclient.Synapse()
	syn.login()

	# parse args
	args = parse_args()

	# mirror folder directory to synapse
	mirror_folders(local_folder = args.folder, project_id = args.syn)

	# upload files
	upload_files(local_folder = args.folder)

	logging.info(args.folder + " is uploaded to Synapse in " + args.syn)
