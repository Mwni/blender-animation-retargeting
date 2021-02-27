bl_info = {
	"name" : "Animation Retargeting",
	"author" : "Mwni",
	"description" : "Retarget animations from one rig to another",
	"version": (1, 0, 0),
	"blender" : (2, 80, 0),
	"location" : "3D View > Tools (Right Side) > Retarget",
	"warning" : "",
	"category" : "Animation",
	'wiki_url': 'https://github.com/Mwni/blender-animation-retargeting',
    'tracker_url': 'https://github.com/Mwni/blender-animation-retargeting/issues',
}


import bpy
from . import data
from . import loadsave
from . import mapping
from . import alignment
from . import corrections
from . import baking
from . import drivers
from . import ik
from .utilfuncs import *



class MainPanel(bpy.types.Panel):
	bl_idname = "RT_PT_Main"
	bl_label = "Animation Retargeting"
	bl_category = "Retarget"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"

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
			layout.label(text='No armature selected', icon='ERROR')





class State(bpy.types.PropertyGroup):
	selected_source: bpy.props.PointerProperty(
		type=bpy.types.Object,
		poll=lambda self, obj: obj.type == 'ARMATURE' and obj != bpy.context.object,
		update=lambda self, ctx: state().update_source()
	)
	invalid_selected_source: bpy.props.PointerProperty(
		type=bpy.types.Object,
	)
	source: bpy.props.PointerProperty(type=bpy.types.Object)
	target: bpy.props.PointerProperty(type=bpy.types.Object)
	target_pose_backup: bpy.props.CollectionProperty(type=data.BonePose)
	mappings: bpy.props.CollectionProperty(type=data.BoneMapping)
	active_mapping: bpy.props.IntProperty()
	ik_limbs: bpy.props.CollectionProperty(type=data.IKLimb)
	root_bone: bpy.props.StringProperty(update=lambda self, ctx: state().update_drivers())
	correct_feet: bpy.props.BoolProperty(default=False, update=lambda self, ctx: state().update_ik_limbs())
	correct_hands: bpy.props.BoolProperty(default=False, update=lambda self, ctx: state().update_ik_limbs())
	correct_root_pivot: bpy.props.BoolProperty(default=False, update=lambda self, ctx: state().update_drivers())
	disable_drivers: bpy.props.BoolProperty(update=lambda self, ctx: state().update_drivers())
	is_importing: bpy.props.BoolProperty(default=False)
	bake_step: bpy.props.FloatProperty(default=1.0)
	bake_linear: bpy.props.BoolProperty(default=False)

	## UI
	editing_mappings: bpy.props.BoolProperty(default=False)
	editing_alignment: bpy.props.BoolProperty(default=False)


	def is_active(self):
		return bpy.context.object.type == 'ARMATURE' and self.source != None

	def update_source(self):
		self.target = bpy.context.object

		if self.selected_source == None:
			return

		if len(self.mappings) > 0:
			compat_n = self.count_compatible_mappings(self.selected_source)
			incompat_n = len(self.mappings) - compat_n

			if incompat_n > 0:
				if self.editing_mappings:
					self.source = self.selected_source

					for mapping in self.mappings:
						if not any(bone.name == mapping.source for bone in self.source.data.bones):
							mapping.source = ''
				else:
					self.invalid_selected_source = self.selected_source
					self.selected_source = self.source

					def draw(self, context):
						self.layout.label(text='Corresponding bones for %i mapping(s) not found.' % incompat_n)
						self.layout.operator('retarget.use_invalid_source')

					bpy.context.window_manager.popup_menu(draw, title='Incompatible armature', icon='ERROR')

				return

		self.source = self.selected_source
		self.update_drivers()


	def count_compatible_mappings(self, target):
		count = 0

		for mapping in self.mappings:
			if any(bone.name == mapping.source for bone in target.data.bones):
				count += 1

		return count


	def get_source_armature(self):
		return self.source.data

	def get_target_armature(self):
		return bpy.context.object.data

	def get_bone_from(self, collection, name):
		return next((bone for bone in collection if bone.name == name), None)

	def get_pose_bone(self, t, name):
		return self.get_bone_from(getattr(self, t).pose.bones, name)

	def get_pose_and_arma_bone(self, t, name):
		return (self.get_bone_from(getattr(self, t).data.bones, name)
				,self.get_bone_from(getattr(self, t).pose.bones, name))

	def get_root_bone(self, t):
		for bone in getattr(self, t+'_armature').bones:
			if bone.parent == None:
				return bone

		return None

	def get_mapping_for_target(self, name):
		for mapping in self.mappings:
			if mapping.target == name:
				return mapping


	def get_alignments_count(self):
		count = 0

		for m in self.mappings:
			if any(a!=b for a,b in zip(m.offset, (1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1))):
				count += 1

		return count

	def get_meshes(self, t):
		obj = getattr(self, t)
		meshes = []

		for child in obj.children:
			if child.type == 'MESH':
				meshes.append(child)

		return meshes

	def get_mesh_baseline(self, t):
		meshes = self.get_meshes(t)
		baseline = 9999999

		for mesh in meshes:
			baseline = min(baseline, bounds(mesh, True).z.min)

		return baseline


	def update_drivers(self):
		if self.is_importing:
			return

		if not self.disable_drivers and self.get_alignments_count() > 0:
			ik.build()
			drivers.build()
		else:
			self.unleash()

	def force_drivers_refresh(self):
		drivers.force_refresh()

	def update_ik_limbs(self):
		if self.is_importing:
			return

		needs_rebuild = False

		for active, name in ((self.correct_feet, 'left-foot'), (self.correct_feet, 'right-foot'), 
							(self.correct_hands, 'left-hand'), (self.correct_hands, 'right-hand')):
			limb = self.get_ik_limb(name)

			if limb == None:
				limb = self.create_ik_limb(name)

			was_enabled = limb.enabled

			limb.enabled = (
				active
				and limb.target_bone != None and limb.target_bone != ''
				and limb.origin_bone != None and limb.origin_bone != ''
			)

			if was_enabled != limb.enabled:
				needs_rebuild = True

		if needs_rebuild:
			self.update_drivers()


	def create_ik_limb(self, name):
		limb = self.ik_limbs.add()
		limb.name = name
		limb.enabled = False

		return limb

	def get_ik_limb(self, name):
		for limb in self.ik_limbs:
			if limb.name == name:
				return limb

		return None

	def build_ik(self):
		ik.build()

	def unleash(self):
		drivers.clear()
		ik.clear()

	def serialize(self):
		mappings = [m.serialize() for m in self.mappings]
		ik_limbs = [l.serialize() for l in self.ik_limbs]

		return {
			'mappings': mappings, 
			'ik_limbs': ik_limbs, 
			'correct_feet': self.correct_feet, 
			'correct_hands': self.correct_hands
		}

	def from_serialized(self, data):
		self.is_importing = True
		self.reset()

		for m in data['mappings']:
			mapping = self.mappings.add()
			mapping.from_serialized(m)

		for l in data['ik_limbs']:
			limb = self.ik_limbs.add()
			limb.from_serialized(l)

		self.correct_feet = data['correct_feet']
		self.correct_hands = data['correct_hands']

		self.is_importing = False

		self.update_drivers()



	def reset(self):
		self.unleash()
		self.mappings.clear()
		self.ik_limbs.clear()
		self.correct_feet = False
		self.correct_hands = False
		self.editing_alignment = False
		self.editing_mappings = False


class UseInvalidOperator(bpy.types.Operator):
	bl_idname = 'retarget.use_invalid_source'
	bl_label = 'Use anyway'


	def execute(self, context):
		s = state()
		s.editing_mappings = True
		s.selected_source = s.invalid_selected_source
		return {'FINISHED'}



classes = (
	MainPanel, 
	*data.classes,
	*loadsave.classes,
	*mapping.classes,
	*alignment.classes,
	*corrections.classes,
	*drivers.classes,
	*baking.classes,
	State,
	UseInvalidOperator
)


def register():
	for clas in classes:
		bpy.utils.register_class(clas)

	bpy.types.Object.animation_retarget_state = bpy.props.PointerProperty(type=State)


def unregister():
	for clas in classes:
		bpy.utils.unregister_class(clas)

	del bpy.types.Object.animation_retarget_state