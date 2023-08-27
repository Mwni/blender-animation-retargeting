import bpy
from mathutils import Matrix, Vector, Quaternion
from .ik import update_ik_controls, clear_ik_controls
from .util import rot_mat, loc_mat, list_to_matrix, extract_loc_axis_from_mat, extract_rot_axis_from_mat
from .log import info


def drive_bone_mat(name, bone, src):
	mat = Matrix.Translation(Vector(src[0:3]))
	quat = Quaternion(src[3:])
	mat = mat @ quat.to_matrix().to_4x4()

	obj = bpy.data.objects[name]
	ctx = obj.retargeting_context
	mapping = ctx.get_mapping_for_target(bone)
	rest_mat = list_to_matrix(mapping.rest)
	offset_mat = list_to_matrix(mapping.offset)
	src_data, src_pose = ctx.get_data_and_pose_bone('source', mapping.source)
	dest_data, dest_pose = ctx.get_data_and_pose_bone('target', mapping.target)
	src_ref_mat = rot_mat(ctx.source.matrix_world) @ rot_mat(src_data.matrix_local)
	dest_ref_mat = rot_mat(ctx.target.matrix_world) @ rot_mat(rest_mat)
	diff_mat = src_ref_mat.inverted() @ dest_ref_mat
	scale = ctx.source.scale[0]

	mat.translation *= scale
	mat = diff_mat.inverted() @ mat @ diff_mat
	mat = offset_mat @ mat

	return mat


def drive_bone_rot(axis, name, bone, *src):
	mat = drive_bone_mat(name, bone, src)
	return extract_rot_axis_from_mat(mat, axis)


def drive_bone_loc(axis, name, bone, *src):
	mat = drive_bone_mat(name, bone, src)
	return extract_loc_axis_from_mat(mat, axis)


def drive_ik_target_mat(name, index, src):
	mat = Matrix.Translation(Vector(src[0:3]))
	quat = Quaternion(src[3:7])
	mat = mat @ quat.to_matrix().to_4x4()

	src = src[7:]

	ctl_mat = Matrix.Translation(Vector(src[0:3]))
	ctl_quat = Quaternion(src[3:7])
	ctl_mat = ctl_mat @ ctl_quat.to_matrix().to_4x4()
	ctl_scale = Matrix.Scale(src[7], 4, (1, 0, 0))
	ctl_scale @= Matrix.Scale(src[8], 4, (0, 1, 0))
	ctl_scale @= Matrix.Scale(src[9], 4, (0, 0, 1))
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


def drive_ik_target_rot(axis, name, index, *src):
	mat = drive_ik_target_mat(name, index, src)
	return extract_rot_axis_from_mat(mat, axis)


def drive_ik_target_loc(axis, name, index, *src):
	mat = drive_ik_target_mat(name, index, src)
	return extract_loc_axis_from_mat(mat, axis)



def update_drivers(ctx):
	if ctx.is_importing:
		return

	if not ctx.setting_disable_drivers and ctx.get_bone_alignments_count() > 0:
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

		dest_pose.rotation_mode = 'XYZ'

		loc_drivers = dest_pose.driver_add('location')
		rot_drivers = dest_pose.driver_add('rotation_euler')


		for axis, lfc, rfc in zip(('x','y','z'), loc_drivers, rot_drivers):
			loc_driver = lfc.driver
			rot_driver = rfc.driver

			src_vars = create_vars(loc_driver, rot_driver, ('LOC', 'ROT'), ctx.source, mapping.source, 'LOCAL_SPACE')

			loc_driver.expression = "retarget_bone_loc('%s','%s','%s',%s)" % (axis, ctx.target.name, mapping.target, ','.join(src_vars))
			rot_driver.expression = "retarget_bone_rot('%s','%s','%s',%s)" % (axis, ctx.target.name, mapping.target, ','.join(src_vars))

	
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

			loc_driver.expression = "retarget_ik_loc('%s','%s',%i,%s)" % (axis, ctx.target.name, i, ','.join(src_vars + ctl_vars))
			rot_driver.expression = "retarget_ik_rot('%s','%s',%i,%s)" % (axis, ctx.target.name, i, ','.join(src_vars + ctl_vars))

	info('built drivers')


classes = []