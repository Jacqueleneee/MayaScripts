from Qt import QtWidgets, QtCore, QtGui
import pymel.core as pm 
from functools import partial
# imports to use logger modules and produce portable code
import Qt
# Use logs instead of print statements
import logging
# imports to allow Qt and Maya controls to work together (deal with Maya UI)
from maya import OpenMayaUI as omui
# Save our lights as json
import json
import os
import time


# Basic config. - sets it up so that any logging errors go to STDOutput
logging.basicConfig()
# Get loggers for our lighting manager and set it to lower logger level
logger = logging.getLogger('LightingManager')
logger.setLevel(logging.DEBUG)

if Qt.__binding__=='PySide':
	logger.debug('Using PySide with shiboken')
	from shiboken import wrapInstance
	from Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
	logger.debug('Using PyQt with sip')
	from sip import wrapinstance as wrapInstance
	from Qt.QtCore import pyqtSignal as Signal
else:
	# PySide 2
	logger.debug('Using PySide2 swith shiboken')
	from shiboken2 import wrapInstance
	from Qt.QtCore import Signal





class LightManager(QtWidgets.QWidget):
	"""
	Main class for light manager
	Args:
		dock(bool): specifies whether to display UI dockable or as a window
			
	"""

	# Dictionary of light types for the manager to use
	# Use partials (similar to lambas) but partials get value when you create it
	lightTypes = {
		"Point Light": pm.pointLight,
		"Spot Light": pm.spotLight,
		"Directional Light": pm.directionalLight,
		"Area Light": partial(pm.shadingNode, 'areaLight', asLight=True),
		"Volume Light": partial(pm.shadingNode, 'volumeLight', asLight=True)
	}


	def __init__(self, dock=True):
		# Check if UI should be dockable or not
		if dock:
			# Yes, use function to get the dock
			parent = getDock()
		else:
			# No, remove all instances of the dock so we wont get multiple UIs
			deleteDock()
			# If UI already exists, delete it first
			try:
				pm.deleteUI('lightingManager')
			except:
				logger.debug('No previous UI exists')
			# Create dialog window that our manager will be inside
			# Store as parent for our current UI to be put inside
			parent = QtWidgets.QDialog(parent=getMayaMainWindow())
			parent.setObjectName('lightingManager')
			parent.setWindowTitle('Lighting Manager')
			layout = QtWidgets.QVBoxLayout(parent)

		# Send our parent to be properly initialized
		super(LightManager, self).__init__(parent=parent)

		# Build and populate our UI with exisitng lights
		self.buildUI()
		self.populate()

		# Add Lighting Manager to our parent and show our parent
		# Maya dock automatically shows, but QDialog will not automatically show
		self.parent().layout().addWidget(self)
		if not dock:
			parent.show()


	def buildUI(self):
		"""
		Builds the content of our light widget portion
			
		"""
		layout = QtWidgets.QGridLayout(self)

		# ***** DROPDOWN COMBOBOX to put in our light types (item, row, col)
		self.lightTypeCB = QtWidgets.QComboBox()
		# Populate with items in our lightTypes dictionary
		for lightType in sorted(self.lightTypes):
			self.lightTypeCB.addItem(lightType)
		layout.addWidget(self.lightTypeCB, 0, 0, 1 ,2)

		# ***** CREATE BUTTON to create out light
		createBtn = QtWidgets.QPushButton('Create')
		createBtn.clicked.connect(self.createLight)
		layout.addWidget(createBtn, 0, 2)

		# ***** SCROLL WIDGET for scrolling if too many lights to fit on screen
		scrollWidget = QtWidgets.QWidget()
		# How to behave when window is resized
		# Only take maximum size required for its content and nothing more
		scrollWidget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
		# Allow everything to be arranged vertically
		self.scrollLayout = QtWidgets.QVBoxLayout(scrollWidget)
		# Nest it in a scroll area
		scrollArea = QtWidgets.QScrollArea()
		# Ensure UI can grow or shrink when resizing
		scrollArea.setWidgetResizable(True)
		# Tell scrollArea which widget to use
		scrollArea.setWidget(scrollWidget)
		layout.addWidget(scrollArea, 1, 0, 1, 3)

		# ***** SAVE TO JSON BUTTONS
		saveBtn = QtWidgets.QPushButton('Save')
		saveBtn.clicked.connect(self.saveLights)
		layout.addWidget(saveBtn, 2, 0)

		importBtn = QtWidgets.QPushButton('Import')
		importBtn.clicked.connect(self.importLights)
		layout.addWidget(importBtn, 2, 1)

		# ***** REFRESH BUTTON
		refreshBtn = QtWidgets.QPushButton('Refresh')
		refreshBtn.clicked.connect(self.populate)
		layout.addWidget(refreshBtn, 2, 2)


	def populate(self):
		"""
		Populate UI with correct lights

		"""
		# Clear out our UI - go through every child and remove it
		# For every child of the scroll layout, get the child at position 0 to get its widget
		for child in range(self.scrollLayout.count()):
			widget = self.scrollLayout.takeAt(0).widget()
			print widget
			if widget:
				widget.setVisible(False)
				widget.deleteLater()

		# light will have object for each light type
		for light in pm.ls(type=['areaLight', 'spotLight', 'pointLight', 'directionalLight', 'volumeLight']):
			self.addLight(light)


	def createLight(self, lightType=None, add=True):
		"""
		Create lights in viewport
		Args:
			lightType(str): type of light to be created
			add(bool): Add light as widget in UI
		Return:
			light(obj)
			
		"""
		if not lightType:	
			# Get current text from the drop down - the light we want to create
			lightType = self.lightTypeCB.currentText()
		# Look up lightTypes dictionary to find function to call
		func = self.lightTypes[lightType]

		# Functions are pyMel so they'll return a pymel object
		light = func()
		# Add light to UI if told so
		if add:
			self.addLight(light)

		return light


	def addLight(self, light):
		"""
		Create a LightWidget for the given light and add it to UI
		Args:
			light(obj)
			
		Returns:
			
		"""
		# Create light
		widget = LightWidget(light)

		# Hook signal to the 'soloLight' method
		widget.onSolo.connect(self.soloLight)

		# Add light widget to represent our light to the scroll area
		self.scrollLayout.addWidget(widget)

	def soloLight(self, value):
		"""
		Isolate a single light
		Args:
			value(bool) - value to set our light to 
		
		"""
		# Get all the light widgets 
		lightWidgets = self.findChildren(LightWidget)
		# Loop through list and perform logic
		for widget in lightWidgets:
			# EVery signal lets us know who sent it by querying with sender()
			# If widget is not its sender, disable the widget
			if widget != self.sender():
				widget.disableLight(value)


	def getDirectory(self):
		"""
		Get directory of our library
			
		Returns:
			directory(str) - a path to the directory
			
		"""
		# Write their properities into the directory
		directory = os.path.join( pm.internalVar(userAppDir=True), 'lightManager' )
		# Check if it exists or not
		if not os.path.exists(directory):
			os.mkdir(directory)
		return directory


	def saveLights(self):
		"""
		Save lights into JSON file so that it can be shared as a preset
			
		"""
		# Create dictionary to save our light properties
		properties = {}

		# For each light, get their properties
		for lightWidget in self.findChildren(LightWidget):
			light = lightWidget.light
			transform = light.getTransform()

			properties[str(transform)] = {
				'translate': list(transform.translate.get()),
				'rotation': list(transform.rotate.get()),
				'lightType': pm.objectType(light),
				'intensity': light.intensity.get(),
				'color': light.color.get()
			}
 		# Get directory of where to save to
		directory = self.getDirectory()
		# Save it to file each time with unique month/day identifier
		lightFile = os.path.join(directory, 'lightFile_%s.json' % time.strftime('%m%d'))
		# Write it out to JSON
		with open(lightFile, 'w') as f:
			json.dump(properties, f, indent=4)
			logger.info('Saving file to %s' % lightFile)


	def importLights(self):
		"""
		Imports our lights back in UI/scene
			
		"""
		# Get directory of where to import from
		directory = self.getDirectory()
		# Open a file dialog & read it
		fileName = QtWidgets.QFileDialog.getOpenFileName(self, "Light Browser", directory)
		with open(fileName[0], 'r') as f:
			properties = json.load(f)
		# Read in the JSON info and
		# Go through each dict item to see if they match current light type
		# If yes, then create light, otherwise, skip and log message
		for light, info in properties.items():
			lightType = info.get('lightType')
			for lt in self.lightTypes:
				if ('%sLight' % lt.split()[0].lower()) == lightType:
					break
			else:
				logger.info('Cannot find a corresponding light type for %s (%s) for %s' % (light,lightType,lightType.split()[0]))
				continue
			light = self.createLight(lightType=lt)
			# Assing values to the light from our JSON
			light.intensity.set(info.get('intensity'))
			light.color.set(info.get('color'))
			transform = light.getTransform()
			transform.translate.set(info.get('translate'))
			transform.rotate.set(info.get('rotation'))
			# Refresh our UI
			self.populate()





class LightWidget(QtWidgets.QWidget):
	"""
	The Basic controller for controlling our lights

	Used to display a light
	ex) 
	ui = LightWidget('directionalLight1')
	ui.show()
	"""
	# Signal for solo button - whether light is on solo or not
	# Light widget will emit a bool 
	onSolo = Signal(bool)


	def __init__(self, light):
		# Call __init__ from QWidget to properly initialize our object
		super(LightWidget,self).__init__()

		# If light is a string, convert to PYMEL node
		if isinstance(light, basestring):
			light =  pm.PyNode(light)
		# If light is a transform, convert as shape
		if isinstance(light, pm.nodetypes.Transform):
			light = light.getShape()

		# Store pyMel node on this class and build
		self.light = light
		self.buildUI()


	def buildUI(self):
		"""
		Builds the content of our light widget portion		
		"""
		# Grid layout allow us to position widgets (x,y, space_x, space_y)
		layout = QtWidgets.QGridLayout(self)

		# ****CHECKBOX - Toggle light visibility
		self.name = QtWidgets.QCheckBox(str(self.light.getTransform()))
		self.name.setChecked(self.light.visibility.get())
		self.name.toggled.connect(lambda val: self.light.getTransform().visibility.set(val))
		layout.addWidget(self.name, 0, 0)

		# ***** SOLO BUTTON - Solo the light visibility
		soloBtn = QtWidgets.QPushButton('Solo')
		# Allow 'press' and 'unpress'
		soloBtn.setCheckable(True)
		# Emit signal whenever it is clicked
		# It will emit onSolo signal using val
		soloBtn.toggled.connect(lambda val: self.onSolo.emit(val))
		layout.addWidget(soloBtn, 0, 1)

		# ***** DELETE BUTTON - Delete the light
		deleteBtn = QtWidgets.QPushButton('X')
		deleteBtn.clicked.connect(self.deleteLight)
		deleteBtn.setMaximumWidth(10)
		#deleteBtn.setStyleSheet('background-color: darkred')
		layout.addWidget(deleteBtn, 0, 2)

		# ***** SLIDER for intensity control
		intensity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		intensity.setMinimum(1)
		intensity.setMaximum(1000)
		intensity.setValue(self.light.intensity.get())
		intensity.valueChanged.connect(lambda val: self.light.intensity.set(val))
		layout.addWidget(intensity, 1, 0, 1, 2)

		# ***** COLOR BUTTON to display color of the light
		# Use 'self' because we will need to query it later
		self.colorBtn = QtWidgets.QPushButton()
		self.colorBtn.setMaximumWidth(20)
		self.colorBtn.setMaximumHeight(20)
		# Set color of button itself
		self.setButtonColor()
		self.colorBtn.clicked.connect(self.setColor)
		layout.addWidget(self.colorBtn, 1, 2)


	def disableLight(self, value):
		"""
		Sets/unchecks our checkbox
		Args:
			value(int): takes in a value and converts it to bool to set our checkbox
			
		"""
		self.name.setChecked(not bool(value))


	def deleteLight(self):
		"""
		Delete light from viewport and widget
		"""
		# *** DELETE FROM UI
		# Delete from parent (remove light from UI and tell QT to stop holding onto it)
		self.setParent(None)
		# Hide itself immediately, since it can still hang around
		self.setVisible(False)
		# Tell Qt to delete it later when possible
		self.deleteLater()

		# *** DELETE LIGHT
		pm.delete(self.light.getTransform())


	def setButtonColor(self, color=None):
		"""
		Set color of button
		Args: 
			color(tuple) - parameter to take a color
		"""
		if not color:
			# Get color from the light itself with pymel
			color=self.light.color.get()

		# Get a list of three values - if more or less, we wont be able to continue
		assert len(color) == 3, "You must provide a list of three colors"

		# 3 values in color, extracted into r,g,b
		r, g, b = [c*255 for c in color]

		# Set color of button
		self.colorBtn.setStyleSheet('background-color: rgba(%s, %s, %s, 1.0)' % (r, g, b) )


	def setColor(self):
		"""
		Set color of light itself 
		"""
		# Get color from light
		lightColor = self.light.color.get()
		# Open Maya color editor, and value chosen in there will be assigned to 'color'
		# returns "r g b a"
		color = pm.colorEditor(rgbValue=lightColor)
		# Strip the string into variables and convert to float values
		r,g,b,a = [float(c) for c in color.split()]
		# Convert 'color' to tuple
		color = (r,g,b)
		# Set actual light color and button 
		self.light.color.set(color)
		self.setButtonColor(color)





def getMayaMainWindow():
	# Get memory address of the main window and convert it to something our Python lib will understand
	win = omui.MQtUtil_mainWindow()
	# Convert address into a long integer
	ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
	return ptr

def getDock(name='LightingManagerDock'):
	# Delete dock with same name if it exists
	deleteDock(name)
	# Create a new dock control
	ctrl = pm.workspaceControl(name, dockToMainWindow=('right', 1), label="Lighting Manager")
	# Get the memory address of control
	qtCtrl = omui.MQtUtil_findControl(ctrl)
	# Convert it to an instance and convert it to long and convert to a regular widget
	ptr = wrapInstance(long(qtCtrl), QtWidgets.QWidget)
	return ptr

def deleteDock(name='LightingManagerDock'):
	# Query the workspacw control with the name 
	# If it exists, then delete the UI with the specified name
	if pm.workspaceControl(name, query=True, exists=True):
		pm.deleteUI(name)



