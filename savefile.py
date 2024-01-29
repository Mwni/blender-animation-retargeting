import bpy
import json
from bpy_extras.io_utils import ExportHelper, ImportHelper
from .util import matrix_to_list


def draw_panel(ctx, layout):
	layout.enabled = not ctx.ui_editing_mappings and not ctx.ui_editing_alignment

	row = layout.row()
	row.operator(SavefileLoadOperator.bl_idname, icon='FILEBROWSER')
	row.operator(SavefileSaveOperator.bl_idname, icon='FILE_TICK')



class SavefileLoadOperator(bpy.types.Operator, ImportHelper):
	bl_idname = 'savefile.load'
	bl_label = 'Load Config'
	bl_description = 'Load bone mappings, alignments and other settings from a file. Can be applied to any armature with identical bone names'

	filter_glob: bpy.props.StringProperty(
		default='*.blend*',
		options={'HIDDEN'},
		maxlen=255
	)

	def execute(self, context):
		with open(self.filepath, 'r') as f:
			load_serialized_state(context.object.retargeting_context, json.load(f))
		return {'FINISHED'}



class SavefileSaveOperator(bpy.types.Operator, ExportHelper):
	bl_idname = 'savefile.save'
	bl_label = 'Save Config'
	filename_ext = '.blend-retarget'
	bl_description = 'Save bone mappings, alignments and other settings from a file. Can be applied to any armature with identical bone names'

	filter_glob: bpy.props.StringProperty(
		default='*.blend-retarget',
		options={'HIDDEN'},
		maxlen=255
	)

	def execute(self, context):
		with open(self.filepath, 'w') as f:
			f.write(
				json.dumps(
					serialize_state(context.object.retargeting_context),
					indent=4
				)
			)

		return {'FINISHED'}



def serialize_state(ctx):
	return {
		'armatures': {
			'source': serialize_armature(ctx.source),
			'target': serialize_armature(ctx.target)
		},
		'mappings': [
			{
				'source': m.source,
				'target': m.target,
				'rest': list(m.rest),
				'offset': list(m.offset)
			}
			for m in ctx.mappings
		], 
		'ik_limbs': [
			{
				'name': l.name,
				'enabled': l.enabled,
				'target_bone': l.target_bone,
				'origin_bone': l.origin_bone,
				'control_transform': list(l.control_transform)
			} 
			for l in ctx.ik_limbs
		], 
		'setting_correct_feet': ctx.setting_correct_feet, 
		'setting_correct_hands': ctx.setting_correct_hands
	}


def serialize_armature(armature):
	return {
		'matrix_world': matrix_to_list(armature.matrix_world),
		'bones': {
			bone.name: {
				'parent': bone.parent.name if bone.parent else None,
				'matrix': matrix_to_list(bone.matrix),
				'matrix_local': matrix_to_list(bone.matrix_local)
			}
			for bone in armature.data.bones
		}
	}


def load_serialized_state(ctx, data):
	ctx.is_importing = True
	ctx.reset()

	for m in data['mappings']:
		mapping = ctx.mappings.add()
		mapping.source = m['source']
		mapping.target = m['target']
		mapping.rest = m['rest']
		mapping.offset = m['offset']

	for l in data['ik_limbs']:
		limb = ctx.ik_limbs.add()
		limb.name = l['name']
		limb.enabled = l['enabled']
		limb.target_bone = l['target_bone']
		limb.origin_bone = l['origin_bone']
		limb.control_transform = l['control_transform']

	ctx.setting_correct_feet = data['setting_correct_feet']
	ctx.setting_correct_hands = data['setting_correct_hands']
	ctx.is_importing = False

	ctx.update_drivers()



classes = (
	SavefileLoadOperator,
	SavefileSaveOperator
)