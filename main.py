import bpy
from . import savefile
from . import mapping
from . import alignment
from . import corrections
from . import baking


class MainPanel(bpy.types.Panel):
	bl_idname = 'RT_PT_Main'
	bl_label = 'Animation Retargeting'
	bl_category = 'Retarget'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'

	def draw(self, context):
		layout = self.layout

		if context.object != None and context.object.type == 'ARMATURE':
			ctx = context.object.retargeting_context

			split = layout.row().split(factor=0.244)
			split.column().label(text='Target:')
			split.column().label(text=context.object.name, icon='ARMATURE_DATA')

			layout.prop(ctx, 'selected_source', text='Source', icon='ARMATURE_DATA')
			layout.separator()

			if ctx.source == None:
				layout.label(text='Choose a source armature to continue', icon='INFO')
			else:
				savefile.draw_panel(ctx, layout.box())
				layout.separator()
				layout.label(text='Bone Mappings')
				mapping.draw_panel(ctx, layout.box())

				if not ctx.ui_editing_mappings and len(ctx.mappings) > 0:
					layout.separator()
					layout.label(text='Rest Alignment')
					alignment.draw_panel(ctx, layout.box())

					if ctx.get_bone_alignments_count() > 0:
						layout.separator()
						layout.label(text='Corrections')
						corrections.draw_panel(ctx, layout.box())

						layout.separator()
						layout.label(text='Baking')
						baking.draw_panel(ctx, layout.box())

						layout.separator()
						layout.label(text='Options')
						box = layout.box()
						box.prop(ctx, 'setting_disable_drivers', text='Disable Drivers')
						
		else:
			layout.label(text='Select target armature', icon='ERROR')



classes = (
	MainPanel,
)