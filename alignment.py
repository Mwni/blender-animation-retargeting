import bpy
from .utilfuncs import *


def draw_panel(layout):
	s = state()
	n = s.get_alignments_count()

	if not s.editing_alignment:
		if n == 0:
			row = layout.row()
			row.label(text='No Rest Alignment', icon='INFO')
			row.operator('retarget_alignment.edit', text='Set Up', icon='POSE_HLT')
		else:
			row = layout.row()
			row.label(text=str(n) + ' Bones with Alignment', icon='POSE_HLT')
			row.operator('retarget_alignment.edit', text='Edit', icon='TOOL_SETTINGS')
			row.operator('retarget_alignment.reset', text='', icon='X')
	else:
		layout.label(text='Editing Rest Pose Alignment', icon='POSE_HLT')

		col = layout.column()
		col.label(text='Align the target\'s pose with the source.', icon='INFO')
		col.label(text='The target should mimic the pose of the source as close as possible.')

		row = layout.row()
		row.operator('retarget_alignment.cancel', text='Cancel', icon='X')
		row.operator('retarget_alignment.apply', text='Apply', icon='CHECKMARK')


def enter_offset():
	s = state()
	s.unleash()
	s.target_pose_backup.clear()

	for bone in s.target.pose.bones:
		bp = s.target_pose_backup.add()
		bp.bone = bone.name
		bp.matrix = matrix4x4_to_data(bone.matrix_basis)

	for bone in s.target.pose.bones:
		for m in s.mappings:
			if m.target == bone.name:
				bone.matrix_basis = data_to_matrix4x4(m.offset)


def restore_poses():
	s = state()

	for bone in s.target.pose.bones:
		for bp in s.target_pose_backup:
			if bp.bone == bone.name:
				bone.matrix_basis = data_to_matrix4x4(bp.matrix)
				break


def store_matrices():
	s = state()

	for bone in s.target.pose.bones:
		for m in s.mappings:
			if m.target == bone.name:
				m.rest = matrix4x4_to_data(bone.matrix)
				m.offset = matrix4x4_to_data(bone.matrix_basis)


def update_rest():
	enter_offset()
	store_matrices()
	restore_poses()
	state().update_drivers()


def leave_edit():
	if handle_edit_change in bpy.app.handlers.depsgraph_update_post:
		bpy.app.handlers.depsgraph_update_post.remove(handle_edit_change)
	s = state()
	s.editing_alignment = False
	s.get_source_armature().pose_position = 'POSE'
	bpy.ops.object.mode_set(mode='OBJECT')
	s.update_drivers()


def handle_edit_change(self, context):
	if bpy.context.object.mode != 'POSE':
		leave_edit()



class EditOperator(bpy.types.Operator):
	bl_idname = 'retarget_alignment.edit'
	bl_label = 'Change Alignment'
	bl_description = 'Set the source to target armature rest pose alignment'

	def execute(self, context):
		s = state()
		s.editing_alignment = True
		s.get_source_armature().pose_position = 'REST'
		bpy.ops.object.mode_set(mode='POSE')

		enter_offset()

		bpy.app.handlers.depsgraph_update_post.append(handle_edit_change)

		return {'FINISHED'}



class ApplyOperator(bpy.types.Operator):
	bl_idname = 'retarget_alignment.apply'
	bl_label = 'Apply Alignment'
	bl_description = 'Use the current pose as reference rest pose when retargeting'

	def execute(self, context):
		store_matrices()
		restore_poses()
		leave_edit()

		return {'FINISHED'}



class CancelOperator(bpy.types.Operator):
	bl_idname = 'retarget_alignment.cancel'
	bl_label = 'Cancel Alignment Change'
	bl_description = 'Discard the current pose and reset to pose before editing'

	def execute(self, context):
		restore_poses()
		leave_edit()

		return {'FINISHED'}



class ResetOperator(bpy.types.Operator):
	bl_idname = 'retarget_alignment.reset'
	bl_label = 'Reset Rest Pose Alignment'
	bl_description = 'Discard configured rest pose and start from scratch.'
	bl_options = {'REGISTER', 'INTERNAL'}

	def invoke(self, context, event):
		return context.window_manager.invoke_confirm(self, event)

	def execute(self, context):
		s = state()

		for mapping in s.mappings:
			mapping.reset_offset()

		s.update_drivers()

		return {'FINISHED'}



classes = (
	EditOperator,
	ApplyOperator,
	CancelOperator,
	ResetOperator
)