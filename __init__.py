bl_info = {
	"name" : "Animation Retargeting",
	"author" : "Mwni",
	"description" : "Retarget animations from one rig to another",
	"version": (1, 0, 0),
	"blender" : (2, 80, 0),
	"location" : "3D View > Tools (Right Side) > Retarget",
	"warning" : "",
	"category" : "Animation",
	'wiki_url': 'https://github.com/Mwni/blender-animation-retargeting',
    'tracker_url': 'https://github.com/Mwni/blender-animation-retargeting/issues',
}

from . import addon

def register():
	addon.register()

def unregister():
	addon.unregister()