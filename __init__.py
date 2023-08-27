bl_info = {
	'name' : 'Animation Retargeting',
	'author' : 'Mwni',
	'description' : 'Retarget animations from one rig to another',
	'version': (1, 1, 0),
	'blender' : (2, 80, 0),
	'location' : '3D View > Tools (Right Side) > Retarget',
	'category' : 'Animation',
	'wiki_url': 'https://github.com/Mwni/blender-animation-retargeting',
    'tracker_url': 'https://github.com/Mwni/blender-animation-retargeting/issues',
}

import bpy
from . import context
from . import main
from . import mapping
from . import alignment
from . import corrections
from . import baking
from . import drivers
from . import ik
from . import savefile
from importlib import reload


modules = [
	context,
	main,
	mapping,
	alignment,
	corrections,
	baking,
	drivers,
	ik,
	savefile,
]


def register():
	for i, module in enumerate(modules):
		modules[i] = reload(module)

	for module in modules:
		for cls in module.classes:
			bpy.utils.register_class(cls)

	bpy.types.Object.retargeting_context = bpy.props.PointerProperty(type=modules[0].Context)


def unregister():
	for module in modules:
		for cls in module.classes:
			bpy.utils.unregister_class(cls)

	del bpy.types.Object.retargeting_context