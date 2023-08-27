bl_info = {
	'name' : 'Animation Retargeting',
	'author' : 'Mwni',
	'description' : 'Retarget animations from one rig to another',
	'version': (1, 0, 0),
	'blender' : (2, 80, 0),
	'location' : '3D View > Tools (Right Side) > Retarget',
	'category' : 'Animation',
	'wiki_url': 'https://github.com/Mwni/blender-animation-retargeting',
    'tracker_url': 'https://github.com/Mwni/blender-animation-retargeting/issues',
}

import bpy
from . import main
from . import data
from . import loadsave
from . import mapping
from . import alignment
from . import corrections
from . import baking
from . import drivers
from . import ik
from importlib import reload


modules = [
	data,
	main,
	loadsave,
	mapping,
	alignment,
	corrections,
	baking,
	drivers,
	ik
]


def register():
	for i, module in enumerate(modules):
		modules[i] = reload(module)

	for module in modules:
		for cls in module.classes:
			bpy.utils.register_class(cls)

	bpy.types.Object.animation_retarget_state = bpy.props.PointerProperty(type=modules[0].State)


def unregister():
	for module in modules:
		for cls in module.classes:
			bpy.utils.unregister_class(cls)

	del bpy.types.Object.animation_retarget_state