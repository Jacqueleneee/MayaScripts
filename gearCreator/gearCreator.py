from maya import cmds

def createGear(teeth=10, length=0.3):
	'''
	This function creates a gear with given parameters
	Args:
		teeth: Number of gear teeth
		length: Length of the teeth
	Returns:
		A tuple of the transform, constructor and extrude node
	'''
	# Number of teeth is number of subdivisions x 2
	# Teeth are every other face, sp spans x 2
	spans = teeth * 2

	# polyPipe cmd creates a polygon pipe
	# Param1 - tells how many divisions we'll have along its length
	# expand the list and its members into our variables
	# transform - name of the node created
	# constructor - node that creates the pipe and controls its parameters
	transform, constructor = cmds.polyPipe(subdivisionsAxis=spans)

	# Identify the faces we want of the pipe
	# MEL (ls -sl) returns faces back, // Result: pPipe2.f[40] pPipe2.f[42] pPipe2.f[44] pPipe2.f[46] pPipe2.f[48] pPipe2.f[50] pPipe2.f[52] pPipe2.f[54] pPipe2.f[56] pPipe2.f[58]
	# range(min, max, steps)
	sideFaces = range(spans*2, spans*3, 2)
	print sideFaces

	# Now we have select the identified faces we want
	# Now we clear our selection
	cmds.select(clear=True)

	# Loop through all the faces
	for face in sideFaces:
		# Expands it into something like "pPipe1.f[20]"
		# That says to select the 20th face of the pPipe1 object
		# 'add' param - adds the selection with the previous selection
		cmds.select('%s.f[%s]' % (transform, face), add=True)

	# Extrude the selected faces by the given length
	# Returns the value of the extrude node
	# Gives us back a list, but only want first object back by '[0]'
	extrude = cmds.polyExtrudeFacet(localTranslateZ=length)[0]

	# Return corresponding nodes
	return transform, constructor, extrude

	# Note: When changing number of subdivisions, we also need to change extrude nodes
	# Extrude node is where we can change # of subvisions, but when we do so, it doesnt know what faces to edit


def changeTeeth(constructor, extrude, teeth, length=0.3):
	"""
	Change number of teeth with a given amount of teeth and its length on an existing gear
	This will create a new extrude node
	Args:
		constructor (str): constructor node
		extrude (str): extrude node
		teeth (int): number of teeth to create
		length (int): length of the teeth to create
	"""
	# Number of spans by duplicating the number of teeth
	spans = teeth * 2
	
	# polyPipe cmd used to modify the gear
	# edit="true" - instead of creating a new one, edit its attributes
	# Creates new subdivisions
	cmds.polyPipe(constructor, edit=True,
				  subdivisionsAxis=spans) 


	# Now we must get a list to know what faces to extrude
	# Go through first face, and step up every two values
	sideFaces = range(spans*2, spans*3, 2)
	faceNames = []

	# We want to get a list in the following format: 
	# [u'f[40]', u'f[42]', u'f[44]', u'f[46]', u'f[48]', u'f[50]', u'f[52]', u'f[54]', u'f[56]', u'f[58]']

	# Loop through all the side faces 
	for face in sideFaces:
		# Use string substitution to create the names where 'face' = number of the face
		faceName = 'f[%s]' % (face)
		faceNames.append(faceName)

	# Set the attributes
	# Modify extrude's parameter for which components it affects
	# We use setAttr call instead of recreating the extrude which can be expensive

	# In maya cmds do....
	# listAttr('polyExtrudeFace1') - we are interested in 'inputComponents'
	# getAttr('polyExtrudeFace1.inputComponents') - return face values we have

	# The arguments to changing a list of components is slightly different than a simple setAttr
    # it is:
    #   cmds.setAttr('extrudeNode.inputComponents', numberOfItems, item1, item2, item3, type='componentList')

	# Arg1 - Pass in extrude node since we dont know what the name of extrude while running the funciton
	# Arg2 - How many items in the list we are giving it
	# Arg3 - Needs list of all the faces we will be using by expanding it by *
	# Arg4 - Tell it what kind of type the attribute is
	cmds.setAttr('%s.inputComponents' % (extrude),
					len(faceNames),
					*faceNames,
					type="componentList")	

	# We want to change the length of the teeth
	# 'ltz' - short form for "localTranslateZ"
	cmds.polyExtrudeFacet(extrude, edit=True, ltz=length)
