import bpy
from .drivers import update_drivers
from .util import matrix_to_list, list_to_matrix


def draw_panel(ctx, layout):
	n = ctx.get_bone_alignments_count()

	if not ctx.ui_editing_alignment:
		if n == 0:
			row = layout.row()
			row.label(text='No Rest Pose Alignment', icon='INFO')
			row.operator(AlignmentEditOperator.bl_idname, text='Set Up', icon='POSE_HLT')
		else:
			row = layout.row()
			row.label(text='%i Bones with Alignment' % n, icon='POSE_HLT')
			row.operator(AlignmentEditOperator.bl_idname, text='Edit', icon='TOOL_SETTINGS')
			row.operator(AlignmentResetOperator.bl_idname, text='', icon='X')
	else:
		layout.label(text='Editing Rest Pose Alignment', icon='POSE_HLT')

		col = layout.column()
		col.label(text='Align the target\'s pose with the source.', icon='INFO')
		col.label(text='The target should mimic the pose of the source as close as possible.')

		row = layout.row()
		row.operator(AlignmentCancelOperator.bl_idname, text='Cancel', icon='X')
		row.operator(AlignmentApplyOperator.bl_idname, text='Apply', icon='CHECKMARK')


def enter_alignment_mode(ctx):
	ctx.ui_editing_alignment = True
	ctx.get_source_armature().pose_position = 'REST'
	bpy.ops.object.mode_set(mode='POSE')

	# todo: s.unleash()
	ctx.target_pose_backup.clear()

	for bone in ctx.target.pose.bones:
		bp = ctx.target_pose_backup.add()
		bp.bone = bone.name
		bp.matrix = matrix_to_list(bone.matrix_basis)

	for bone in ctx.target.pose.bones:
		for m in ctx.mappings:
			if m.target == bone.name:
				bone.matrix_basis = list_to_matrix(m.offset)

	bpy.app.handlers.depsgraph_update_post.append(handle_edit_change)


def store_alignments(ctx):
	for bone in ctx.target.pose.bones:
		for m in ctx.mappings:
			if m.target == bone.name:
				m.rest = matrix_to_list(bone.matrix)
				m.offset = matrix_to_list(bone.matrix_basis)


def leave_alignment_mode(ctx):
	if handle_edit_change in bpy.app.handlers.depsgraph_update_post:
		bpy.app.handlers.depsgraph_update_post.remove(handle_edit_change)

	for bone in ctx.target.pose.bones:
		for bp in ctx.target_pose_backup:
			if bp.bone == bone.name:
				bone.matrix_basis = list_to_matrix(bp.matrix)
				break

	ctx.ui_editing_alignment = False
	ctx.get_source_armature().pose_position = 'POSE'
	bpy.ops.object.mode_set(mode='OBJECT')
	update_drivers(ctx)


def handle_edit_change(self, context):
	if bpy.context.object.mode != 'POSE':
		leave_alignment_mode(context.object.retargeting_context)



class AlignmentEditOperator(bpy.types.Operator):
	bl_idname = 'alignment.edit'
	bl_label = 'Change Alignment'
	bl_description = 'Set the source to target armature rest pose alignment'

	def execute(self, context):
		enter_alignment_mode(context.object.retargeting_context)
		return {'FINISHED'}



class AlignmentApplyOperator(bpy.types.Operator):
	bl_idname = 'alignment.apply'
	bl_label = 'Apply Alignment'
	bl_description = 'Use the current pose as reference rest pose when retargeting'

	def execute(self, context):
		ctx = context.object.retargeting_context
		store_alignments(ctx)
		leave_alignment_mode(ctx)
		return {'FINISHED'}



class AlignmentCancelOperator(bpy.types.Operator):
	bl_idname = 'alignment.cancel'
	bl_label = 'Cancel Alignment Change'
	bl_description = 'Discard the current pose and reset to pose before editing'

	def execute(self, context):
		leave_alignment_mode(context.object.retargeting_context)
		return {'FINISHED'}



class AlignmentResetOperator(bpy.types.Operator):
	bl_idname = 'alignment.reset'
	bl_label = 'Reset Rest Pose Alignment'
	bl_description = 'Discard configured rest pose and start from scratch.'
	bl_options = {'REGISTER', 'INTERNAL'}

	def invoke(self, context, event):
		return context.window_manager.invoke_confirm(self, event)

	def execute(self, context):
		ctx = context.object.retargeting_context

		for mapping in ctx.mappings:
			mapping.reset_offset()

		update_drivers(ctx)
		return {'FINISHED'}



classes = (
	AlignmentEditOperator,
	AlignmentApplyOperator,
	AlignmentCancelOperator,
	AlignmentResetOperator
)