import bpy


def draw_panel(ctx, layout):
	n = len(ctx.mappings)

	if not ctx.ui_editing_mappings:
		if n == 0:
			row = layout.row()
			row.label(text='No Bone Mappings', icon='INFO')
			row.operator(MappingsEditOperator.bl_idname, text='Create', icon='PRESET_NEW')
		else:
			row = layout.row()
			row.label(text='%i Bone Pairs' % n, icon='GROUP_BONE')
			row.operator(MappingsEditOperator.bl_idname, text='Edit', icon='TOOL_SETTINGS')
			row.operator(MappingsClearOperator.bl_idname, text='', icon='X')
	else:
		row = layout.split(factor=0.63)
		row.label(text='Editing %i Bone Pairs' % n, icon='GROUP_BONE')
		row.operator(MappingsGuessOperator.bl_idname, text='Guess', icon='LIGHT')

		row = layout.row()
		row.template_list('RT_UL_mappings', '', ctx, 'mappings', ctx, 'active_mapping')

		col = row.column(align=True)
		col.operator(MappingsListActionOperator.bl_idname, icon='ADD', text='').action = 'ADD'
		col.operator(MappingsListActionOperator.bl_idname, icon='REMOVE', text='').action = 'REMOVE'

		layout.operator(MappingsApplyOperator.bl_idname, text='Done')


def count_incompatible_mappings(ctx, target):
	count = 0

	for mapping in ctx.mappings:
		if all(bone.name != mapping.source for bone in target.data.bones):
			count += 1

	return count


def warn_incompatible_source_armature(incompat_n):
	bpy.context.window_manager.popup_menu(
		title='Incompatible armature', 
		icon='ERROR',
		draw_func=lambda self, _: (
			self.layout.label(text='Corresponding bones for %i mapping(s) not found.' % incompat_n) +
			self.layout.operator('retarget.use_invalid_source_anyway')
		)
	)



class RT_UL_mappings(bpy.types.UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
		ctx = context.object.retargeting_context
		layout.alert = not item.is_valid()
		layout.prop_search(item, 'source', ctx.get_source_armature(), 'bones', text='', icon='BONE_DATA')
		layout.label(icon='FORWARD')
		layout.prop_search(item, 'target', ctx.get_target_armature(), 'bones', text='', icon='BONE_DATA')

	def draw_filter(self, context, layout):
		pass

	def filter_items(self, context, data, propname):
		flt_flags = []
		flt_neworder = []

		return flt_flags, flt_neworder



class MappingsEditOperator(bpy.types.Operator):
	bl_idname = 'mappings.edit'
	bl_label = 'Create'
	bl_description = 'Map individual bones from the source armature to the target armature'

	def execute(self, context):
		context.object.retargeting_context.ui_editing_mappings = True
		return {'FINISHED'}



class MappingsApplyOperator(bpy.types.Operator):
	bl_idname = 'mappings.apply'
	bl_label = 'Apply'
	bl_description = 'Save and use the created bone mappings'

	def execute(self, context):
		ctx = context.object.retargeting_context

		if any(not mapping.is_valid() for mapping in ctx.mappings):
			bpy.context.window_manager.popup_menu(
				title='Invalid Mappings', 
				icon='ERROR',
				draw_func=lambda self, context: self.layout.label(
					text='There are one or more invalid mappings (marked red).'
				)
			)
			return

		ctx.ui_editing_mappings = False
		return {'FINISHED'}



class MappingsListActionOperator(bpy.types.Operator):
	bl_idname = 'mappings.list_action'
	bl_label = ''
	action: bpy.props.StringProperty()

	def execute(self, context):
		ctx = context.object.retargeting_context

		if self.action == 'ADD':
			ctx.mappings.add()
			ctx.active_mapping = len(ctx.mappings) - 1
		elif self.action == 'REMOVE':
			if len(ctx.mappings) > 0:
				ctx.mappings.remove(ctx.active_mapping)
				ctx.active_mapping =  min(ctx.active_mapping, len(ctx.mappings) - 1)

		return {'FINISHED'}



class MappingsGuessOperator(bpy.types.Operator):
	bl_idname = 'mappings.guess'
	bl_label = 'Guess Bone Mappings'
	bl_description = 'Attempt to map source to target bones automatically based on name and topology'

	def execute(self, context):
		return {'FINISHED'}



class MappingsClearOperator(bpy.types.Operator):
	bl_idname = 'mappings.clear'
	bl_label = 'Reset Bone Mappings'
	bl_description = 'Clears all existing source-target bone mappings'
	bl_options = {'REGISTER', 'INTERNAL'}

	def invoke(self, context, event):
		return context.window_manager.invoke_confirm(self, event)

	def execute(self, context):
		context.object.retargeting_context.reset()
		# todo: clear drivers and iks
		return {'FINISHED'}
	


class MappingsUseInvalidSourceAnywayOperator(bpy.types.Operator):
	bl_idname = 'mappings.use_invalid_source_anyway'
	bl_label = 'Use anyway'
	bl_description = 'Use the incompatible source armature anyways. Target bones that have no corresponding source bone will be ignored'

	def execute(self, context):
		context.object.retargeting_context.handle_source_update(ignore_incompat=True)
		return {'FINISHED'}


classes = (
	RT_UL_mappings,
	MappingsApplyOperator,
	MappingsEditOperator,
	MappingsListActionOperator,
	MappingsGuessOperator,
	MappingsClearOperator,
	MappingsUseInvalidSourceAnywayOperator
)