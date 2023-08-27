import bpy
from . import loadsave
from . import mapping
from . import alignment
from . import corrections
from . import baking
from .utilfuncs import *


class MainPanel(bpy.types.Panel):
	bl_idname = 'RT_PT_Main'
	bl_label = 'Animation Retargeting'
	bl_category = 'Retarget'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'

	def draw(self, context):
		layout = self.layout

		if context.object != None and context.object.type == 'ARMATURE':
			s = state()
			split = layout.row().split(factor=0.244)
			split.column().label(text='Target:')
			split.column().label(text=context.object.name, icon='ARMATURE_DATA')
			layout.prop(s, 'selected_source', text='Source', icon='ARMATURE_DATA')
			layout.separator()

			if s.source == None:
				layout.label(text='Choose a source armature to continue', icon='INFO')
			else:
				loadsave.draw_panel(layout.box())
				layout.separator()
				layout.label(text='Bone Mappings')
				mapping.draw_panel(layout.box())

				if not s.editing_mappings and len(s.mappings) > 0:
					layout.separator()
					layout.label(text='Rest Alignment')
					alignment.draw_panel(layout.box())

					if s.get_alignments_count() > 0:
						layout.separator()
						layout.label(text='Corrections')
						corrections.draw_panel(layout.box())

						layout.separator()
						layout.label(text='Baking')
						baking.draw_panel(layout.box())

						layout.separator()
						layout.label(text='Options')
						box = layout.box()
						box.prop(s, 'disable_drivers', text='Disable Drivers')
						
		else:
			layout.label(text='Select target armature', icon='ERROR')


classes = (
	MainPanel,
)