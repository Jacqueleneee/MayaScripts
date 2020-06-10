# Interact with Maya
from maya import cmds
# Interact with our OS
import os
# Use JSON module to write out data
import json
# Allows us to pretty print our data
import pprint

# First, create a directory where we can save our controllers and their data
USERAPPDIR = cmds.internalVar(userAppDir=True)

# Tells python to use your os-specific separator to...
# Join userAppDir with name of our directory
DIRECTORY = os.path.join(USERAPPDIR, 'controllerLibrary')


def createDirectory(directory=DIRECTORY):
	"""
	Creates the given directory if it doesn't exist already
	Args:
		directory (str): The directory to create

	"""
	# If given directory DNE, make it
	if not os.path.exists(directory):
		os.mkdir(directory)


class ControllerLibrary(dict):

	def save(self, name, directory=DIRECTORY, screenshot=True, **info):
		"""
		Saves the scene
		Args:
			self (obj): reference itself
			name (str): name of the file we want to save
			directory (str): the directory to save to

		"""

		# Ensure directory we want to save to exists
		createDirectory(directory)

		# Create the path that we will be saving this to
		path = os.path.join(directory, '%s.ma' % name)

		# Write data to JSON - CREATE DICTIONARY TO SAVE DATA
		infoFile = os.path.join(directory, '%s.json' % name)

		info['name'] = name
		info['path'] = path

		# Saving requires some parameters...
		# rename: rename it to the location we want to save it
		# save: tell it to save
		# type: specify what type to save it as
		# force: if file already exists, you want save and override it-
		cmds.file(rename=path)

		# Saving selected items vs the entire scene
		# If there is a selection, get the list of the selections
		if cmds.ls(selection=True):
			cmds.file(force=True, type='mayaAscii', exportSelected=True)
		else:
			cmds.file(save=True, type='mayaAscii', force=True)

		# Save the path of screenshot into the json dict
		if screenshot:
			info['screenshot'] = self.saveScreenshot(name, directory=directory)



		# Open the file in WRITE mode, and store file in 'f'
		# Use JSON to dump 'info' into f - indent all by 4 spaces
		with open(infoFile, 'w') as f:
			json.dump(info, f, indent=4)

		# Fixes BUG 1 (Save path name in our controller library)	
		self[name] = info


	def find(self, directory=DIRECTORY):
		"""
		Find all saved controllers in the directory
		Args:
			self (obj): reference itself
			directory (str): the directory to look in

		"""
		# Clear dictionary
		self.clear()
		# Check if directory exists
		# If it doesnt exist, there are no controllers saved
		if not os.path.exists(directory):
			return

		# If it does exist, list all files in directory
		files = os.listdir(directory)
		# Filter out only maya files
		mayaFiles = [f for f in files if f.endswith('.ma')]

		# Loop through maya files and get name and store it to dictionary (with file path)
		for ma in mayaFiles:
			# Get the name without the extension
			name, extension = os.path.splitext(ma)
			# Get link to the file path for that file name
			path = os.path.join(directory, ma)

			infoFile = "%s.json" % name
			if infoFile in files:
				infoFile = os.path.join(directory, infoFile)
				# Open the file in READ mode, and store file in 'f'
				# Use JSON to load data and store it in 'info'
				with open(infoFile, 'r') as f:
					info = json.load(f)
			else:
				# If JSON not found, create an empty dict
				info = {}

			# Find screenshot
			screenshot = '%s.jpg' % name
			if screenshot in files:
				info['screenshot'] = os.path.join(directory, name)

			# Populate dict, in case no info is there
			info['name'] = name
			info['path'] = path

			self[name] = info



	def load(self, name):
		"""
		Load controller into the scene
		
		Args:
			self (obj): reference itself
			name (str): Name of file to load

		"""
		# Look up our content using dict method where 'self[name] is a dict'
		path = self[name]['path']
		# Give path to import(i)
		cmds.file(path, i=True, usingNamespaces=False)



	def saveScreenshot(self, name, directory=DIRECTORY):
		"""
		Save screenshot into specified path
		
		Args:
			self (obj): reference itself
			directory (str): directory of where screenshot will be saved

		"""
		path = os.path.join(directory, '%s.jpg' % name)

		# Ensure Maya viewer fits around our controller
		cmds.viewFit()
		# This is in RenderSettings for .jpg
		cmds.setAttr('defaultRenderGlobals.imageFormat', 8)
		# Render it out
		# Ornaments - parts of viewpart are not in scene (overlays)
		cmds.playblast(completeFilename=path, forceOverwrite=True, format='image', width=200, height=200,
						showOrnaments=False, startTime=1, endTime=1, viewer=False)


		return path


#BUG 1 - saved controller wont update unless run .find()
#	- dont always want to run find() everytime we save a controller







	

			







