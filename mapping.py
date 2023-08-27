import bpy
from .utilfuncs import *


def draw_panel(layout):
	s = state()
	n = len(s.mappings)

	if not s.editing_mappings:
		if n == 0:
			row = layout.row()
			row.label(text='No Bone Mappings', icon='INFO')
			row.operator('retarget_mappings.edit', text='Create', icon='PRESET_NEW')
		else:
			row = layout.row()
			row.label(text=str(n) + ' Bone Pairs', icon='GROUP_BONE')
			row.operator('retarget_mappings.edit', text='Edit', icon='TOOL_SETTINGS')
			row.operator('retarget_mappings.clear', text='', icon='X')
	else:
		layout.label(text='Edit Bone Mappings (%i):' % n, icon='TOOL_SETTINGS')

		row = layout.row()
		row.template_list('RT_UL_mappings', '', s, 'mappings', s, 'active_mapping')
		col = row.column(align=True)
		col.operator('retarget_mappings.list_action', icon='ADD', text='').action = 'ADD'
		col.operator('retarget_mappings.list_action', icon='REMOVE', text='').action = 'REMOVE'
		layout.operator('retarget_mappings.apply', text='Done')



class RT_UL_mappings(bpy.types.UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
		s = state()
		layout.alert = not item.is_valid()
		layout.prop_search(item, 'source', s.get_source_armature(), 'bones', text='', icon='BONE_DATA')
		layout.label(icon='FORWARD')
		layout.prop_search(item, 'target', s.get_target_armature(), 'bones', text='', icon='BONE_DATA')

	def draw_filter(self, context, layout):
		pass

	def filter_items(self, context, data, propname):
		flt_flags = []
		flt_neworder = []

		return flt_flags, flt_neworder



class EditOperator(bpy.types.Operator):
	bl_idname = 'retarget_mappings.edit'
	bl_label = 'Create'
	bl_description = 'Map individual bones from the source armature to the target armature'

	def execute(self, context):
		state().editing_mappings = True
		return {'FINISHED'}



class ApplyOperator(bpy.types.Operator):
	bl_idname = 'retarget_mappings.apply'
	bl_label = 'Apply'
	bl_description = 'Save and use the created bone mappings'

	def execute(self, context):
		s = state()

		if any(not mapping.is_valid() for mapping in s.mappings):
			alert_error('Invalid Mappings', 'There are one or more invalid mappings (marked red).')
			return

		state().editing_mappings = False
		return {'FINISHED'}



class ListActionOperator(bpy.types.Operator):
	bl_idname = 'retarget_mappings.list_action'
	bl_label = ''
	action: bpy.props.StringProperty()

	def execute(self, context):
		s = state()

		if self.action == 'ADD':
			mapping = s.mappings.add()
			s.active_mapping = len(s.mappings) - 1
		elif self.action == 'REMOVE':
			if len(s.mappings) > 0:
				s.mappings.remove(s.active_mapping)
				s.active_mapping =  min(s.active_mapping, len(s.mappings) - 1)


		return {'FINISHED'}



class ClearOperator(bpy.types.Operator):
	bl_idname = 'retarget_mappings.clear'
	bl_label = 'Reset Bone Mappings'
	bl_description = 'Clears all existing source-target bone mappings'
	bl_options = {'REGISTER', 'INTERNAL'}

	def invoke(self, context, event):
		return context.window_manager.invoke_confirm(self, event)

	def execute(self, context):
		state().reset()
		return {'FINISHED'}



class UseInvalidSourceOperator(bpy.types.Operator):
	bl_idname = 'retarget.use_invalid_source'
	bl_label = 'Use anyway'

	def execute(self, context):
		s = state()
		s.editing_mappings = True
		s.selected_source = s.invalid_selected_source
		return {'FINISHED'}



classes = (
	RT_UL_mappings,
	ApplyOperator,
	EditOperator,
	ClearOperator,
	ListActionOperator,
	UseInvalidSourceOperator
)