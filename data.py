import bpy
from . import drivers
from . import ik
from .utilfuncs import *
from .log import info


class BoneMapping(bpy.types.PropertyGroup):
	source: bpy.props.StringProperty()
	target: bpy.props.StringProperty()
	rest: bpy.props.FloatVectorProperty(size=16, default=(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1))
	offset: bpy.props.FloatVectorProperty(size=16, default=(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1))

	def is_valid(self):
		return (self.source != None 
				and self.target != None 
				and len(self.source) > 0 
				and len(self.target) > 0)

	def serialize(self):
		return {
			'source': self.source,
			'target': self.target,
			'rest': list(self.rest),
			'offset': list(self.offset)
		}

	def from_serialized(self, m):
		self.source = m['source']
		self.target = m['target']
		self.rest = m['rest']
		self.offset = m['offset']

	def reset_offset(self):
		self.rest = (1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1)
		self.offset = (1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1)



class BonePose(bpy.types.PropertyGroup):
	bone: bpy.props.StringProperty()
	matrix: bpy.props.FloatVectorProperty(size=16, default=(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1))



class IKLimb(bpy.types.PropertyGroup):
	name: bpy.props.StringProperty()
	enabled: bpy.props.BoolProperty(default=False)
	target_bone: bpy.props.StringProperty(update=lambda self, ctx: state().update_ik_limbs())
	origin_bone: bpy.props.StringProperty(update=lambda self, ctx: state().update_ik_limbs())
	target_empty: bpy.props.PointerProperty(type=bpy.types.Object)
	target_empty_child: bpy.props.PointerProperty(type=bpy.types.Object)
	pole_empty: bpy.props.PointerProperty(type=bpy.types.Object)
	control_holder: bpy.props.PointerProperty(type=bpy.types.Object)
	control_cube: bpy.props.PointerProperty(type=bpy.types.Object)
	control_transform: bpy.props.FloatVectorProperty(size=16, default=(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1))

	def serialize(self):
		return {
			'name': self.name,
			'enabled': self.enabled,
			'target_bone': self.target_bone,
			'origin_bone': self.origin_bone,
			'control_transform': list(self.control_transform)
		}

	def from_serialized(self, l):
		self.name = l['name']
		self.enabled = l['enabled']
		self.target_bone = l['target_bone']
		self.origin_bone = l['origin_bone']
		self.control_transform = l['control_transform']



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
	target_pose_backup: bpy.props.CollectionProperty(type=BonePose)
	mappings: bpy.props.CollectionProperty(type=BoneMapping)
	active_mapping: bpy.props.IntProperty()
	ik_limbs: bpy.props.CollectionProperty(type=IKLimb)
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
			
		info('set source armature to %s' % self.selected_source.name)

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

	def get_data_and_pose_bone(self, t, name):
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

	def update_drivers(self):
		if self.is_importing:
			return

		if not self.disable_drivers and self.get_alignments_count() > 0:
			ik.build()
			drivers.build()
		else:
			self.unleash()


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



classes = (
	BoneMapping,
	BonePose,
	IKLimb,
	State,
)