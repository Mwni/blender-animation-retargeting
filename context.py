import bpy
from .mapping import count_incompatible_mappings, warn_incompatible_source_armature
from .drivers import update_drivers, clear_drivers
from .ik import update_ik_limbs
from .log import info


class BonePose(bpy.types.PropertyGroup):
	bone: bpy.props.StringProperty()
	matrix: bpy.props.FloatVectorProperty(size=16, default=(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1))



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

	def reset_offset(self):
		self.rest = (1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1)
		self.offset = (1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1)



class IKLimb(bpy.types.PropertyGroup):
	name: bpy.props.StringProperty()
	enabled: bpy.props.BoolProperty(default=False)
	target_bone: bpy.props.StringProperty(update=lambda self, ctx: update_ik_limbs(bpy.ctx.object.retargeting_context))
	origin_bone: bpy.props.StringProperty(update=lambda self, ctx: update_ik_limbs(bpy.ctx.object.retargeting_context))
	target_empty: bpy.props.PointerProperty(type=bpy.types.Object)
	target_empty_child: bpy.props.PointerProperty(type=bpy.types.Object)
	pole_empty: bpy.props.PointerProperty(type=bpy.types.Object)
	control_holder: bpy.props.PointerProperty(type=bpy.types.Object)
	control_cube: bpy.props.PointerProperty(type=bpy.types.Object)
	control_transform: bpy.props.FloatVectorProperty(size=16, default=(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1))



class Context(bpy.types.PropertyGroup):
	selected_source: bpy.props.PointerProperty(
		type=bpy.types.Object,
		poll=lambda self, obj: obj.type == 'ARMATURE' and obj != bpy.context.object,
		update=lambda self, ctx: self.handle_source_change()
	)
	source: bpy.props.PointerProperty(type=bpy.types.Object)
	target: bpy.props.PointerProperty(type=bpy.types.Object)
	target_pose_backup: bpy.props.CollectionProperty(type=BonePose)
	mappings: bpy.props.CollectionProperty(type=BoneMapping)
	did_setup_empty_alignment: bpy.props.BoolProperty(default=False)
	active_mapping: bpy.props.IntProperty()
	ik_limbs: bpy.props.CollectionProperty(type=IKLimb)
	is_importing: bpy.props.BoolProperty(default=False)

	setting_correct_feet: bpy.props.BoolProperty(default=False, update=lambda self, ctx: self.handle_ik_change())
	setting_correct_hands: bpy.props.BoolProperty(default=False, update=lambda self, ctx: self.handle_ik_change())
	setting_disable_drivers: bpy.props.BoolProperty(default=False)
	setting_bake_step: bpy.props.FloatProperty(default=1.0)
	setting_bake_linear: bpy.props.BoolProperty(default=False)
	setting_bake_mapped_bones_only: bpy.props.BoolProperty(default=False)

	ui_editing_mappings: bpy.props.BoolProperty(default=False)
	ui_guessing_mappings: bpy.props.BoolProperty(default=False)
	ui_editing_alignment: bpy.props.BoolProperty(default=False)


	def update_drivers(self):
		update_drivers(self)

	def clear_drivers(self):
		clear_drivers(self)


	def handle_source_change(self, ignore_incompat=False):
		if self.selected_source == None:
			return

		if len(self.mappings) > 0 and not ignore_incompat:
			incompat_n = count_incompatible_mappings(self, self.selected_source)

			if incompat_n > 0:
				warn_incompatible_source_armature(incompat_n)
				return
		
		info('set source armature to %s' % self.selected_source.name)
		self.source = self.selected_source
		self.target = bpy.context.object
		update_drivers(self)


	def handle_ik_change(self):
		if update_ik_limbs(self):
			update_drivers(self)


	def get_source_armature(self):
		return self.source.data


	def get_target_armature(self):
		return self.target.data
	

	def get_bone_alignments_count(self):
		return sum([
			1 if any(a!=b for a,b in zip(m.offset, (1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1))) else 0
			for m in self.mappings
		])
	

	def get_mapping_for_target(self, name):
		for mapping in self.mappings:
			if mapping.target == name:
				return mapping


	def get_ik_limb_by_name(self, name):
		for limb in self.ik_limbs:
			if limb.name == name:
				return limb

		return None
	

	def get_guessing_bones(self):
		return [bone for bone in bpy.context.selected_pose_bones if bone.name in self.target.pose.bones]
		

	def reset(self):
		self.mappings.clear()
		self.ik_limbs.clear()
		self.setting_correct_feet = False
		self.setting_correct_hands = False
		self.did_setup_empty_alignment = True



classes = (
	BonePose,
	BoneMapping,
	IKLimb,
	Context,
)