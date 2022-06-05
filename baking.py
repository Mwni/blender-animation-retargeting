import bpy
import os
from bpy_extras.io_utils import ImportHelper
from .utilfuncs import *

def draw_panel(layout):
	s = state()
	row = layout.row()
	row.prop(s, 'bake_step', text='Frame Step')
	row.prop(s, 'bake_linear', text='Linear Interpolation')
	layout.operator('retarget_baking.bake')
	layout.operator('retarget_baking.batch_import')
	pass

def get_keyframes(obj):
	frames = []
	anim = obj.animation_data
	if anim is not None and anim.action is not None:
		for fcu in anim.action.fcurves:
			for keyframe in fcu.keyframe_points:
				x, y = keyframe.co
				if x not in frames:
					frames.append(x)

	return frames

def find_action(name):
	for action in bpy.data.actions:
		if action.name == name:
			return action

	return None



def transfer_anim(context):
	s = state()

	keyframes = get_keyframes(s.source)
	source_action = s.source.animation_data.action
	target_action_name = s.target.name + '|' + source_action.name.replace(s.source.name + '|', '')
	target_action = find_action(target_action_name)

	if target_action != None:
		while len(target_action.fcurves) > 0:
			target_action.fcurves.remove(target_action.fcurves[0])
	else:
		target_action = bpy.data.actions.new(target_action_name)

	s.target.animation_data.action = target_action

	bpy.ops.nla.bake(
		frame_start=int(min(keyframes)),
		frame_end=int(max(keyframes)),
		step=int(s.bake_step),
		visual_keying=True,
		use_current_action=True,
		bake_types={'POSE'},
		only_selected=False
	)

	if s.bake_linear:
		for fc in s.target.animation_data.action.fcurves:
			for kp in fc.keyframe_points:
				kp.interpolation = 'LINEAR'

	target_action.use_fake_user = True


class BakeOperator(bpy.types.Operator):
	bl_idname = 'retarget_baking.bake'
	bl_label = 'Bake into Action'

	def execute(self, context):
		transfer_anim(context)
		return {'FINISHED'}



class BatchImportOperator(bpy.types.Operator, ImportHelper):
	bl_idname = 'retarget_baking.batch_import'
	bl_label = 'Batch Import & Bake'
	directory: bpy.props.StringProperty(subtype='DIR_PATH')
	files: bpy.props.CollectionProperty(name='File paths', type=bpy.types.OperatorFileListElement)
	filter_glob: bpy.props.StringProperty(
		default='*.fbx',
		options={'HIDDEN'},
		maxlen=255
	)

	def execute(self, context):
		s = state()

		bpy.context.window_manager.progress_begin(0, len(self.files) * 2)
		progress = 0

		for file in self.files:
			bpy.ops.import_scene.fbx(
				filepath=os.path.join(self.directory, file.name),
				use_custom_props=True,
				use_custom_props_enum_as_string=True,
				ignore_leaf_bones=False,
				automatic_bone_orientation=True
			)

			bpy.context.window_manager.progress_update(progress)
			progress += 1

			imported_objects = []
			imported_source = None

			for obj in context.selected_objects:
				imported_objects.append(obj)

				if obj.type == 'ARMATURE':
					imported_source = obj


			for obj in imported_objects:
				obj.select_set(False)

			if imported_source != None:
				imported_action = imported_source.animation_data.action
				imported_source.scale = s.source.scale
				bpy.context.view_layer.objects.active = s.target
				s.target.select_set(True)
				prev = s.source
				s.selected_source = imported_source
				transfer_anim(bpy.context)
				s.selected_source = prev
				imported_source.animation_data.action = None
				bpy.data.actions.remove(imported_action)

			for obj in imported_objects:
				bpy.data.objects.remove(obj, do_unlink=True)

			bpy.context.window_manager.progress_update(progress)
			progress += 1

		bpy.context.window_manager.progress_end()

		return {'FINISHED'}

classes = (
	BakeOperator,
	BatchImportOperator
)