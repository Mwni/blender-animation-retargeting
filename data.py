import bpy
from .utilfuncs import *

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


classes = (
	BoneMapping,
	BonePose,
	IKLimb
)