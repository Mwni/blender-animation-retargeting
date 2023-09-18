import bpy
from mathutils import Matrix, Vector, Quaternion
from .mapping import get_intermediate_bones
from .ik import update_ik_controls, clear_ik_controls
from .util import rot_mat, loc_mat, list_to_matrix, extract_loc_axis_from_mat, extract_rot_axis_from_mat
from .log import info


def draw_panel(ctx, layout):
	layout.enabled = not ctx.ui_editing_mappings and not ctx.ui_editing_alignment
	
	if ctx.setting_disable_drivers:
		split = layout.split(factor=0.63)
		split.label(text='Bone Drivers disabled', icon='ERROR')
		split.operator(DriversEnableOperator.bl_idname, text='Enable', icon='CHECKMARK')
	else:
		split = layout.split(factor=0.38)
		status = split.column()
		actions = split.row()

		status.label(text='%i Bone Drivers' % len(ctx.mappings), icon='DRIVER')
		actions.operator(DriversRebuildOperator.bl_idname, text='Rebuild', icon='FILE_REFRESH')
		actions.operator(DriversDisableOperator.bl_idname, text='Disable', icon='X')

		ik_drivers_n = sum([1 if limb.enabled else 0 for limb in ctx.ik_limbs])

		if ik_drivers_n > 0:
			status.label(text='%i IK Drivers' % ik_drivers_n, icon='CON_KINEMATIC')
			actions.scale_y = 2



def update_drivers(ctx):
	if ctx.is_importing:
		return

	if not ctx.setting_disable_drivers and (ctx.get_bone_alignments_count() > 0 or ctx.did_setup_empty_alignment):
		update_ik_controls(ctx)
		clear_drivers(ctx)
		build_drivers(ctx)
	else:
		clear_ik_controls(ctx)
		clear_drivers(ctx)


def clear_drivers(ctx):
	for mapping in ctx.mappings:
		_, dest_pose = ctx.get_data_and_pose_bone('target', mapping.target)
		dest_pose.driver_remove('location')
		dest_pose.driver_remove('rotation_euler')
		dest_pose.matrix_basis = Matrix()

	for limb in ctx.ik_limbs:
		if limb.target_empty != None:
			limb.target_empty.driver_remove('location')
			limb.target_empty.driver_remove('rotation_euler')

	info('cleared drivers')


def create_vars(loc_driver, rot_driver, t, s_source, mapping_source, space, offset=0):
	src_vars = []

	for tt in t:
		for ta in (('W', 'X', 'Y', 'Z') if tt == 'ROT' else ('X', 'Y', 'Z')):
			for driver in (loc_driver, rot_driver):
				var = driver.variables.new()
				var.name = chr(65 + len(src_vars) + offset)
				var.type = 'TRANSFORMS'
				var.targets[0].id = s_source
				var.targets[0].bone_target = mapping_source
				var.targets[0].rotation_mode = 'QUATERNION'
				var.targets[0].transform_space = space
				var.targets[0].transform_type = tt + '_' + ta

			src_vars.append(var.name)

	return src_vars


def build_drivers(ctx):
	bpy.app.driver_namespace['retarget_bone_rot'] = drive_bone_rot
	bpy.app.driver_namespace['retarget_bone_loc'] = drive_bone_loc
	bpy.app.driver_namespace['retarget_ik_rot'] = drive_ik_target_rot
	bpy.app.driver_namespace['retarget_ik_loc'] = drive_ik_target_loc

	for mapping in ctx.mappings:
		_, dest_pose = ctx.get_data_and_pose_bone('target', mapping.target)
		intermediate_bones = get_intermediate_bones(ctx, mapping)

		dest_pose.rotation_mode = 'XYZ'

		loc_drivers = dest_pose.driver_add('location')
		rot_drivers = dest_pose.driver_add('rotation_euler')


		for axis, lfc, rfc in zip(('x','y','z'), loc_drivers, rot_drivers):
			loc_driver = lfc.driver
			rot_driver = rfc.driver

			src_vars = create_vars(loc_driver, rot_driver, ('LOC', 'ROT'), ctx.source, mapping.source, 'LOCAL_SPACE')

			loc_driver.expression = "retarget_bone_loc('%s','%s','%s',[%s])" % (
				axis, 
				ctx.target.name, 
				mapping.target, 
				','.join(src_vars)
			)
			rot_driver.expression = "retarget_bone_rot('%s','%s','%s',[%s],[%s])" % (
				axis, 
				ctx.target.name, 
				mapping.target, 
				','.join(src_vars),
				','.join(['"%s"' % bone for bone in intermediate_bones])
			)

	
	for i, limb in enumerate(ctx.ik_limbs):
		if not limb.enabled:
			continue

		mapping = ctx.get_mapping_for_target(limb.target_bone)

		loc_drivers = limb.target_empty.driver_add('location')
		rot_drivers = limb.target_empty.driver_add('rotation_euler')

		for axis, lfc, rfc in zip(('x','y','z'), loc_drivers, rot_drivers):
			loc_driver = lfc.driver
			rot_driver = rfc.driver

			src_vars = create_vars(loc_driver, rot_driver, ('LOC', 'ROT'), ctx.source, mapping.source, 'WORLD_SPACE')
			ctl_vars = create_vars(loc_driver, rot_driver, ('LOC', 'ROT', 'SCALE'), limb.control_cube, '', 'LOCAL_SPACE', offset=len(src_vars))

			loc_driver.expression = "retarget_ik_loc('%s','%s',%i,[%s])" % (axis, ctx.target.name, i, ','.join(src_vars + ctl_vars))
			rot_driver.expression = "retarget_ik_rot('%s','%s',%i,[%s])" % (axis, ctx.target.name, i, ','.join(src_vars + ctl_vars))

	info('built drivers')



class DriversEnableOperator(bpy.types.Operator):
	bl_idname = 'drivers.enable'
	bl_label = 'Enable Drivers'
	bl_description = 'Build and apply all bone drivers according to the current setup'

	def execute(self, context):
		ctx = context.object.retargeting_context
		ctx.setting_disable_drivers = False
		update_drivers(ctx)
		return {'FINISHED'}


class DriversRebuildOperator(bpy.types.Operator):
	bl_idname = 'drivers.rebuild'
	bl_label = 'Rebuild Drivers'
	bl_description = 'Rebuild and apply all bone drivers. This is useful when there was a change that the addon missed'

	def execute(self, context):
		update_drivers(context.object.retargeting_context)
		return {'FINISHED'}
	

class DriversDisableOperator(bpy.types.Operator):
	bl_idname = 'drivers.disable'
	bl_label = 'Disable Drivers'
	bl_description = 'Clear all existing bone drivers and IK controls'

	def execute(self, context):
		ctx = context.object.retargeting_context
		ctx.setting_disable_drivers = True
		update_drivers(ctx)
		return {'FINISHED'}



### DRIVER EXPRESSIONS 


def drive_bone_mat(name, bone, src_vars, intermediate_bones):
	obj = bpy.data.objects[name]
	ctx = obj.retargeting_context
	mapping = ctx.get_mapping_for_target(bone)

	rest_mat = list_to_matrix(mapping.rest)
	offset_mat = list_to_matrix(mapping.offset)

	src_data, _ = ctx.get_data_and_pose_bone('source', mapping.source)
	src_ref_mat = rot_mat(ctx.source.matrix_world) @ rot_mat(src_data.matrix_local)
	dest_ref_mat = rot_mat(ctx.target.matrix_world) @ rot_mat(rest_mat)
	diff_mat = src_ref_mat.inverted() @ dest_ref_mat

	intermediate_offset = Quaternion()

	if len(intermediate_bones) > 0:
		src_bone = ctx.get_pose_bone('source', mapping.source)
		head_bone = ctx.get_pose_bone('source', intermediate_bones[0])
		tail_bone = ctx.get_pose_bone('source', intermediate_bones[-1])

		if tail_bone.parent:
			base_bone = tail_bone.parent
			base_rest = base_bone.bone.matrix_local.to_quaternion()
			base_pose = base_bone.matrix.to_quaternion()
		else:
			base_rest = Quaternion()
			base_pose = Quaternion()

		head_rest = head_bone.bone.matrix_local.to_quaternion()
		head_pose = head_bone.matrix.to_quaternion()

		based_pose = base_pose.inverted() @ head_pose
		based_rest = base_rest.inverted() @ head_rest

		based_delta = based_rest.inverted() @ based_pose
		mapped_delta = src_bone.bone.matrix.to_quaternion().inverted() @ based_delta @ src_bone.bone.matrix.to_quaternion()

		intermediate_offset = mapped_delta


	scale = ctx.source.matrix_world.to_scale()
	scale_matrix = Matrix.Identity(4)
	scale_matrix[0][0] = scale.x
	scale_matrix[1][1] = scale.y
	scale_matrix[2][2] = scale.z

	mat = Matrix.Translation(Vector(src_vars[0:3]))
	quat = Quaternion(src_vars[3:]) @ intermediate_offset
	mat = mat @ quat.to_matrix().to_4x4()
	mat = scale_matrix @ mat
	mat = diff_mat.inverted() @ mat @ diff_mat
	mat = offset_mat @ mat
	mat = mat

	return mat


def drive_bone_rot(axis, name, bone, src_vars, intermediate_bones):
	mat = drive_bone_mat(name, bone, src_vars, intermediate_bones)
	return extract_rot_axis_from_mat(mat, axis)


def drive_bone_loc(axis, name, bone, src_vars):
	mat = drive_bone_mat(name, bone, src_vars, [])
	return extract_loc_axis_from_mat(mat, axis)


def drive_ik_target_mat(name, index, src_vars):
	mat = Matrix.Translation(Vector(src_vars[0:3]))
	quat = Quaternion(src_vars[3:7])
	mat = mat @ quat.to_matrix().to_4x4()

	src_vars = src_vars[7:]

	ctl_mat = Matrix.Translation(Vector(src_vars[0:3]))
	ctl_quat = Quaternion(src_vars[3:7])
	ctl_mat = ctl_mat @ ctl_quat.to_matrix().to_4x4()
	ctl_scale = Matrix.Scale(src_vars[7], 4, (1, 0, 0))
	ctl_scale @= Matrix.Scale(src_vars[8], 4, (0, 1, 0))
	ctl_scale @= Matrix.Scale(src_vars[9], 4, (0, 0, 1))
	ctl_mat = ctl_mat @ ctl_scale

	obj = bpy.data.objects[name]
	ctx = obj.retargeting_context
	limb = ctx.ik_limbs[index]
	mapping = ctx.get_mapping_for_target(limb.target_bone)
	src_data, _ = ctx.get_data_and_pose_bone('source', mapping.source)

	src_world_mat = loc_mat(ctx.source.matrix_world).inverted() @ ctx.source.matrix_world
	src_ref_mat = ctx.source.matrix_world @ loc_mat(src_data.matrix_local)
	src_rot_mat = rot_mat(ctx.source.matrix_world) @ rot_mat(src_data.matrix_local)
	dest_rest_mat = list_to_matrix(mapping.rest)
	dest_rot_mat = rot_mat(ctx.target.matrix_world) @ rot_mat(dest_rest_mat)
	diff_rot_mat = src_rot_mat.inverted() @ dest_rot_mat

	mat = src_world_mat @ src_ref_mat.inverted() @ loc_mat(dest_rest_mat) @ ctl_mat @ mat @ diff_rot_mat

	return mat


def drive_ik_target_rot(axis, name, index, src_vars):
	mat = drive_ik_target_mat(name, index, src_vars)
	return extract_rot_axis_from_mat(mat, axis)


def drive_ik_target_loc(axis, name, index, src_vars):
	mat = drive_ik_target_mat(name, index, src_vars)
	return extract_loc_axis_from_mat(mat, axis)



classes = (
	DriversEnableOperator,
	DriversRebuildOperator,
	DriversDisableOperator
)