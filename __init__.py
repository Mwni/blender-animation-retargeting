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


classes = (
	*main.classes, 
	*data.classes,
	*loadsave.classes,
	*mapping.classes,
	*alignment.classes,
	*corrections.classes,
	*drivers.classes,
	*baking.classes,
)


def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Object.animation_retarget_state = bpy.props.PointerProperty(type=data.State)


def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)

	del bpy.types.Object.animation_retarget_state