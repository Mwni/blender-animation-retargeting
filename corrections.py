import bpy
from .utilfuncs import *


def draw_panel(layout):
	s = state()

	layout.prop(s, 'correct_root_pivot', text='Correct Root Pivot')
	if s.correct_root_pivot:
		layout.box().prop_search(s, 'root_bone', s.get_target_armature(), 'bones', text='Root Bone', icon='BONE_DATA')

	layout.prop(s, 'correct_feet', text='Correct Feet Position')
	if s.correct_feet:
		row = layout.box().row()
		draw_limb_section(row.column(), 'Left Foot', 'Left Thigh', s, s.get_ik_limb('left-foot'))
		draw_limb_section(row.column(), 'Right Foot', 'Right Thigh', s, s.get_ik_limb('right-foot'))

	layout.prop(s, 'correct_hands', text='Correct Hands Position')
	if s.correct_hands:
		row = layout.box().row()
		draw_limb_section(row.column(), 'Left Hand', 'Left Upper Arm', s, s.get_ik_limb('left-hand'))
		draw_limb_section(row.column(), 'Right Hand', 'Right Upper Arm', s, s.get_ik_limb('right-hand'))
	


def draw_limb_section(layout, target_label, origin_label, s, prop):
	layout.label(text=origin_label)
	layout.prop_search(prop, 'origin_bone', s.get_target_armature(), 'bones', text='', icon='BONE_DATA')
	layout.label(text=target_label)
	layout.prop_search(prop, 'target_bone', s.get_target_armature(), 'bones', text='', icon='BONE_DATA')



class TransferOperator(bpy.types.Operator):
	bl_idname = 'retarget_anim.transfer'
	bl_label = 'Transfer Animation'

	def execute(self, context):
		return {'FINISHED'}


class AddIKOperator(bpy.types.Operator):
	bl_idname = 'retarget_corrections.add_ik'
	bl_label = 'Add'

	def execute(self, context):
		s = state()
		limb = s.ik_limbs.add()
		return {'FINISHED'}

class RemoveIKOperator(bpy.types.Operator):
	bl_idname = 'retarget_corrections.remove_ik'
	bl_label = 'Remove'

	index: bpy.props.IntProperty()

	def execute(self, context):
		state().ik_limbs.clear()
		return {'FINISHED'}


class ApplyIKOperator(bpy.types.Operator):
	bl_idname = 'retarget_corrections.apply_ik'
	bl_label = 'Apply'

	def execute(self, context):
		state().build_ik()
		return {'FINISHED'}


classes = (
	AddIKOperator,
	RemoveIKOperator,
	ApplyIKOperator
)