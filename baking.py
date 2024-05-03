import os
import bpy
from bpy_extras.io_utils import ImportHelper
from .log import info


def draw_panel(ctx, layout):
	layout.enabled = not ctx.ui_editing_mappings and not ctx.ui_editing_alignment and not ctx.setting_disable_drivers
	row = layout.row()
	row.prop(ctx, 'setting_bake_step', text='Frame Step')
	row = layout.row()
	row.prop(ctx, 'setting_bake_linear', text='Linear Interpolation')
	row = layout.row()
	row.prop(ctx, 'setting_bake_mapped_bones_only', text='Bake Mapped Bones Only')
	layout.operator(BakingBakeOperator.bl_idname, icon='RENDER_ANIMATION')
	layout.operator(BakingBatchFBXImportOperator.bl_idname, icon='FILE_FOLDER')


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


def transfer_anim(ctx):
	keyframes = get_keyframes(ctx.source)
	source_action = ctx.source.animation_data.action
	target_action_name = ctx.target.name + '|' + source_action.name.replace(ctx.source.name + '|', '')
	target_action = find_action(target_action_name)

	info('baking %s source animation into action "%s"' % (ctx.source.name, target_action_name))

	if target_action != None:
		while len(target_action.fcurves) > 0:
			info('action "%s" already exists: deleting it' % target_action_name)
			target_action.fcurves.remove(target_action.fcurves[0])
	else:
		target_action = bpy.data.actions.new(target_action_name)

	ctx.target.animation_data.action = target_action

	bpy.ops.object.mode_set(mode='POSE')

	for target_bone in ctx.target.pose.bones:
		if ctx.setting_bake_mapped_bones_only:
			target_bone.bone.select = True if ctx.get_mapping_for_target(target_bone.name) else False
		else:
			target_bone.bone.select = True

	bpy.ops.nla.bake(
		frame_start=int(min(keyframes)),
		frame_end=int(max(keyframes)),
		step=int(ctx.setting_bake_step),
		visual_keying=True,
		use_current_action=True,
		bake_types={'POSE'},
		only_selected=ctx.setting_bake_mapped_bones_only
	)

	if ctx.setting_bake_linear:
		for fc in ctx.target.animation_data.action.fcurves:
			for kp in fc.keyframe_points:
				kp.interpolation = 'LINEAR'

	target_action.use_fake_user = True

	info('bake complete')



class BakingBakeOperator(bpy.types.Operator):
	bl_idname = 'baking.bake'
	bl_label = 'Bake into Action'
	bl_description = 'Inserts animation keyframes transferred from the source based on the configured retargeting'

	def execute(self, context):
		ctx = context.object.retargeting_context
		transfer_anim(ctx)

		ctx.setting_disable_drivers = True
		ctx.update_drivers()
		
		context.window_manager.popup_menu(
			title='Bake Complete',
			icon='INFO',
			draw_func=lambda self, ctx: (
				self.layout.label(text='The retargeted animation has been successfully baked into the target armature. Drivers have been disabled so you can review the result animation')
			)
		)
		return {'FINISHED'}



class BakingBatchFBXImportOperator(bpy.types.Operator, ImportHelper):
	bl_idname = 'baking.batch_import'
	bl_label = 'Batch FBX Import & Bake'
	bl_description = 'Select multiple FBX files having the same source armature, and bake each file\'s animations into an Action on the target armature'
	
	directory: bpy.props.StringProperty(subtype='DIR_PATH')
	files: bpy.props.CollectionProperty(name='File paths', type=bpy.types.OperatorFileListElement)
	filter_glob: bpy.props.StringProperty(
		default='*.fbx',
		options={'HIDDEN'},
		maxlen=255
	)

	ignore_leaf_bones: bpy.props.BoolProperty(
		name='Ignore Leaf Bones',
		description='Ignore leaf bones during FBX import',
		default=False,
	)

	automatic_bone_orientation: bpy.props.BoolProperty(
		name='Automatic Bone Orientation',
		description='Automatically orient bones during FBX import',
		default=False,
	)

	def draw(self, context):
		self.layout.prop(self, 'ignore_leaf_bones')
		self.layout.prop(self, 'automatic_bone_orientation')

	def execute(self, context):
		ctx = context.object.retargeting_context

		bpy.context.window_manager.progress_begin(0, len(self.files) * 2)
		progress = 0

		for file in self.files:
			bpy.ops.import_scene.fbx(
				filepath=os.path.join(self.directory, file.name),
				use_custom_props=True,
				use_custom_props_enum_as_string=True,
				ignore_leaf_bones=self.ignore_leaf_bones,
				automatic_bone_orientation=self.automatic_bone_orientation
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
				imported_source.scale = ctx.source.scale
				bpy.context.view_layer.objects.active = ctx.target
				ctx.target.select_set(True)
				prev = ctx.source
				ctx.selected_source = imported_source
				transfer_anim(ctx)
				ctx.selected_source = prev
				imported_source.animation_data.action = None
				bpy.data.actions.remove(imported_action)

			for obj in imported_objects:
				bpy.data.objects.remove(obj, do_unlink=True)

			bpy.context.window_manager.progress_update(progress)
			progress += 1

		bpy.context.window_manager.progress_end()

		return {'FINISHED'}



classes = (
	BakingBakeOperator,
	BakingBatchFBXImportOperator
)