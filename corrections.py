import bpy


def draw_panel(ctx, layout):
	layout.enabled = not ctx.ui_editing_mappings and not ctx.ui_editing_alignment
	layout.prop(ctx, 'setting_correct_feet', text='Correct Feet Position')
	if ctx.setting_correct_feet:
		row = layout.box().row()
		draw_limb_section(row.column(), 'Left Foot', 'Left Thigh', ctx, ctx.get_ik_limb_by_name('left-foot'))
		draw_limb_section(row.column(), 'Right Foot', 'Right Thigh', ctx, ctx.get_ik_limb_by_name('right-foot'))

	layout.prop(ctx, 'setting_correct_hands', text='Correct Hands Position')
	if ctx.setting_correct_hands:
		row = layout.box().row()
		draw_limb_section(row.column(), 'Left Hand', 'Left Upper Arm', ctx, ctx.get_ik_limb_by_name('left-hand'))
		draw_limb_section(row.column(), 'Right Hand', 'Right Upper Arm', ctx, ctx.get_ik_limb_by_name('right-hand'))
	

def draw_limb_section(layout, target_label, origin_label, ctx, prop):
	layout.label(text=origin_label)
	layout.prop_search(prop, 'origin_bone', ctx.get_target_armature(), 'bones', text='', icon='BONE_DATA')
	layout.label(text=target_label)
	layout.prop_search(prop, 'target_bone', ctx.get_target_armature(), 'bones', text='', icon='BONE_DATA')



classes = []