import bpy
from difflib import SequenceMatcher


bone_synonyms = (
	('clavicle', 'shoulder', 'collar'),
	('upperarm', 'uparm', 'shoulder'),
	('lowerarm', 'loarm', 'forearm'),
	('pinky', 'little'),
	('pelvis', 'spine', 'abdomen'),
	('upperleg', 'thigh'),
	('lowerleg', 'shin', 'calf'),
	('foot', 'ankle'),
	('ball', 'toe'),
)


def draw_panel(ctx, layout):
	n = len(ctx.mappings)

	if not ctx.ui_editing_mappings:
		layout.enabled = not ctx.ui_editing_alignment

		if n == 0:
			row = layout.row()
			row.label(text='No Bone Mappings', icon='INFO')
			row.operator(MappingsEditOperator.bl_idname, text='Create', icon='PRESET_NEW')
		else:
			row = layout.row()
			row.label(text='%i Bone Pairs' % n, icon='GROUP_BONE')
			row.operator(MappingsEditOperator.bl_idname, text='Edit', icon='TOOL_SETTINGS')
			row.operator(MappingsClearOperator.bl_idname, text='', icon='X')
	elif ctx.ui_guessing_mappings:
		layout.label(text='Guessing Bone Pairs', icon='LIGHT')

		bones_n = len(ctx.get_guessing_bones())

		if bones_n == 0:
			layout.label(text='Select all bones that should be guessed', icon='INFO')
		else:
			layout.label(text='%i Bones selected for guess' % bones_n, icon='BONE_DATA')
		
		row = layout.row()
		row.operator(MappingsGuessCancelOperator.bl_idname, text='Cancel', icon='X')
		row.operator(MappingsGuessApplyOperator.bl_idname, text='Guess', icon='SHADERFX')
	else:
		row = layout.split(factor=0.63)
		row.label(text='Editing %i Bone Pairs' % n, icon='GROUP_BONE')
		row.operator(MappingsGuessOperator.bl_idname, text='Guess', icon='LIGHT')

		row = layout.row()
		row.template_list('RT_UL_mappings', '', ctx, 'mappings', ctx, 'active_mapping')

		col = row.column(align=True)
		col.operator(MappingsListActionOperator.bl_idname, icon='ADD', text='').action = 'ADD'
		col.operator(MappingsListActionOperator.bl_idname, icon='REMOVE', text='').action = 'REMOVE'

		layout.operator(MappingsApplyOperator.bl_idname, text='Done', icon='CHECKMARK')



def enter_mapping_mode(ctx):
	ctx.ui_editing_mappings = True
	ctx.get_source_armature().pose_position = 'REST'
	ctx.get_target_armature().pose_position = 'REST'
	ctx.source.select_set(True)

	bpy.ops.object.mode_set(mode='POSE')
	bpy.app.handlers.depsgraph_update_post.append(handle_edit_change)


def guess_mappings(ctx):
	source_bones = [bone.name for bone in ctx.source.pose.bones]
	target_bones = [bone.name for bone in ctx.get_guessing_bones()]
	source_sides = guess_group_by_side(source_bones)
	target_sides = guess_group_by_side(target_bones)

	mappings = []

	for side in ('l', 'r', 'x'):
		mappings += guess_map_by_name(source_sides[side], target_sides[side])

	for sbone, tbone in mappings:
		if sbone in [m.source for m in ctx.mappings]:
			continue

		if tbone in [m.target for m in ctx.mappings]:
			continue

		mapping = ctx.mappings.add()
		mapping.source = sbone
		mapping.target = tbone

		ctx.active_mapping = len(ctx.mappings) - 1

	ctx.ui_guessing_mappings = False
	ctx.source.select_set(True)


def guess_map_by_name(source_bones, target_bones):
	mappings_source = []
	mappings_target = []
	matches = []

	for tbone in target_bones:
		for sbone in source_bones:
			sbone_lower, tbone_lower = guess_apply_synonym(sbone.lower(), tbone.lower())
			matcher = SequenceMatcher(None, sbone_lower, tbone_lower)

			if matcher.find_longest_match().size <= 1:
				continue

			matches.append((sbone, tbone, matcher.ratio()))

	matches = sorted(matches, key=lambda m: m[2], reverse=True)

	for sbone, tbone, _ in matches:
		if sbone in mappings_source or tbone in mappings_target:
			continue

		mappings_source.append(sbone)
		mappings_target.append(tbone)

	return list(zip(mappings_source, mappings_target))


def guess_apply_synonym(source_bone, target_bone):
	for synonyms in bone_synonyms:
		for key in synonyms:
			if key not in source_bone:
				continue
			
			other = [s for s in synonyms if s != key]

			for o in other:
				if o in target_bone:
					return source_bone, target_bone.replace(o, key)
				
	return source_bone, target_bone


def guess_group_by_side(bones):
	groups = {
		'l': [],
		'r': [],
		'x': []
	}

	for bone in bones:
		if bone in groups['l'] or bone in groups['r']:
			continue

		found_match = False

		if 'right' in bone.lower():
			for partner in bones:
				if partner == bone:
					continue

				if bone.lower() == partner.lower().replace('left', 'right'):
					groups['r'].append(bone)
					groups['l'].append(partner)
					found_match = True
					break
		else:
			potential_partners = [b for b in bones if b != bone and len(b) == len(bone)]
			
			for i, char in enumerate(bone):
				if char.lower() != 'r':
					continue

				for partner in potential_partners:
					if bone == partner[0:i] + char + partner[i+1:]:
						groups['r'].append(bone)
						groups['l'].append(partner)
						found_match = True
						break

				if found_match:
					break

		if not found_match:
			groups['x'].append(bone)

	return groups


def leave_mapping_mode(ctx):
	if handle_edit_change in bpy.app.handlers.depsgraph_update_post:
		bpy.app.handlers.depsgraph_update_post.remove(handle_edit_change)

	ctx.ui_editing_mappings = False
	ctx.get_source_armature().pose_position = 'POSE'
	ctx.get_target_armature().pose_position = 'POSE'
	ctx.source.select_set(False)

	bpy.ops.object.mode_set(mode='OBJECT')
	

def handle_edit_change(self, context):
	if bpy.context.object.mode != 'POSE':
		leave_mapping_mode(bpy.context.object.retargeting_context)


def get_intermediate_bones(ctx, mapping):
	bone = ctx.source.pose.bones[mapping.source]
	intermediate_bones = []

	while bone.parent and not any(m.source == bone.parent.name for m in ctx.mappings):
		intermediate_bones.append(bone.parent.name)
		bone = bone.parent

	return intermediate_bones


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
		enter_mapping_mode(context.object.retargeting_context)
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

		leave_mapping_mode(context.object.retargeting_context)
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
		ctx = context.object.retargeting_context
		ctx.ui_guessing_mappings = True
		ctx.source.select_set(False)
		return {'FINISHED'}



class MappingsGuessCancelOperator(bpy.types.Operator):
	bl_idname = 'mappings.guess_cancel'
	bl_label = 'Cancel Bone Mappings Guess'
	bl_description = 'Do not continue with attempting to guess bone mappings'

	def execute(self, context):
		context.object.retargeting_context.ui_guessing_mappings = False
		return {'FINISHED'}
	


class MappingsGuessApplyOperator(bpy.types.Operator):
	bl_idname = 'mappings.guess_apply'
	bl_label = 'Apply Bone Mappings Guess'
	bl_description = 'Attempting to guess bone mappings based on the bone selection made'

	def execute(self, context):
		guess_mappings(context.object.retargeting_context)
		return {'FINISHED'}


class MappingsClearOperator(bpy.types.Operator):
	bl_idname = 'mappings.clear'
	bl_label = 'Reset Bone Mappings'
	bl_description = 'Clears all existing source-target bone mappings'
	bl_options = {'REGISTER', 'INTERNAL'}

	def invoke(self, context, event):
		return context.window_manager.invoke_confirm(self, event)

	def execute(self, context):
		ctx = context.object.retargeting_context
		ctx.reset()
		ctx.clear_drivers()
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
	MappingsGuessCancelOperator,
	MappingsGuessApplyOperator,
	MappingsClearOperator,
	MappingsUseInvalidSourceAnywayOperator
)