import bpy
from mathutils import Matrix, Vector, Quaternion, Euler
from math import pi
from .utilfuncs import *

def extract_rot_from_mat(mat, axis):
	return getattr(mat.to_quaternion().to_euler(), axis)

def extract_loc_from_mat(mat, axis):
	return getattr(mat.to_translation(), axis)


def bone_mat(name, bone, src):
	mat = Matrix.Translation(Vector(src[0:3]))
	quat = Quaternion(src[3:])
	mat = mat @ quat.to_matrix().to_4x4()

	obj = bpy.data.objects[name]
	s = obj.animation_retarget_state
	mapping = s.get_mapping_for_target(bone)
	rest_mat = data_to_matrix4x4(mapping.rest)
	offset_mat = data_to_matrix4x4(mapping.offset)
	src_arma, src_pose = s.get_pose_and_arma_bone('source', mapping.source)
	dest_arma, dest_pose = s.get_pose_and_arma_bone('target', mapping.target)
	src_ref_mat = rot_mat(s.source.matrix_world) @ rot_mat(src_arma.matrix_local)
	dest_ref_mat = rot_mat(s.target.matrix_world) @ rot_mat(rest_mat)
	diff_mat = src_ref_mat. inverted() @ dest_ref_mat
	scale = s.source.scale[0]

	mat.translation *= scale
	mat = diff_mat.inverted() @ mat @ diff_mat
	mat = offset_mat @ mat

	if s.correct_root_pivot and s.root_bone != '' and dest_arma.name == s.root_bone:
		src_root_mat = s.source.matrix_world @ src_arma.matrix_local
		dest_root_mat = s.target.matrix_world @ rest_mat
		src_root_loc = src_root_mat.to_translation()
		dest_root_loc = dest_root_mat.to_translation()
		root_delta_mat = Matrix.Translation(Vector((0,0,(dest_root_loc[2] - src_root_loc[2]))))

		src_rot_matrix = rot_mat(dest_ref_mat @ rot_mat(mat) @ dest_ref_mat.inverted())
		applied_delta_mat = loc_mat((dest_ref_mat.inverted() @ src_rot_matrix) @ root_delta_mat)
		mat = loc_mat(dest_ref_mat.inverted() @ root_delta_mat).inverted() @ applied_delta_mat @ mat

	return mat

def bone_rot(axis, name, bone, *src):
	mat = bone_mat(name, bone, src)
	return extract_rot_from_mat(mat, axis)

def bone_loc(axis, name, bone, *src):
	mat = bone_mat(name, bone, src)
	return extract_loc_from_mat(mat, axis)


def ik_target_mat(name, index, src):
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
	s = obj.animation_retarget_state
	limb = s.ik_limbs[index]
	mapping = s.get_mapping_for_target(limb.target_bone)
	src_arma, src_pose = s.get_pose_and_arma_bone('source', mapping.source)
	dest_arma, dest_pose = s.get_pose_and_arma_bone('target', mapping.target)

	src_world_mat = loc_mat(s.source.matrix_world).inverted() @ s.source.matrix_world
	src_ref_mat = s.source.matrix_world @ loc_mat(src_arma.matrix_local)
	src_rot_mat = rot_mat(s.source.matrix_world) @ rot_mat(src_arma.matrix_local)
	dest_rest_mat = data_to_matrix4x4(mapping.rest)
	dest_rot_mat = rot_mat(s.target.matrix_world) @ rot_mat(dest_rest_mat)
	diff_rot_mat = src_rot_mat.inverted() @ dest_rot_mat

	mat = src_world_mat @ src_ref_mat.inverted() @ loc_mat(dest_rest_mat) @ ctl_mat @ mat @ diff_rot_mat

	return mat

def ik_target_rot(axis, name, index, *src):
	mat = ik_target_mat(name, index, src)
	return extract_rot_from_mat(mat, axis)

def ik_target_loc(axis, name, index, *src):
	mat = ik_target_mat(name, index, src)
	return extract_loc_from_mat(mat, axis)



def pack_float_array(array, size=6):
	return ''.join([(str(round(x, size)) + ('0' * size))[0:size] for x in array])

def unpack_float_array(s, size=6):
	array = []

	for i in range(0, len(s), size):
		array.append(float(s[i:i+size]))

	return array


def clear():
	s = state()

	for mapping in s.mappings:
		dest_arma, dest_pose = s.get_pose_and_arma_bone('target', mapping.target)
		dest_pose.driver_remove('location')
		dest_pose.driver_remove('rotation_euler')

	for limb in s.ik_limbs:
		if limb.target_empty != None:
			limb.target_empty.driver_remove('location')
			limb.target_empty.driver_remove('rotation_euler')


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


def build():
	bpy.app.driver_namespace['rt_bone_rot'] = bone_rot
	bpy.app.driver_namespace['rt_bone_loc'] = bone_loc
	bpy.app.driver_namespace['rt_ikt_rot'] = ik_target_rot
	bpy.app.driver_namespace['rt_ikt_loc'] = ik_target_loc

	s = state()

	clear()

	for mapping in s.mappings:
		src_arma, src_pose = s.get_pose_and_arma_bone('source', mapping.source)
		dest_arma, dest_pose = s.get_pose_and_arma_bone('target', mapping.target)

		dest_pose.rotation_mode = 'XYZ'

		loc_drivers = dest_pose.driver_add('location')
		rot_drivers = dest_pose.driver_add('rotation_euler')


		for axis, lfc, rfc in zip(('x','y','z'), loc_drivers, rot_drivers):
			loc_driver = lfc.driver
			rot_driver = rfc.driver

			src_vars = create_vars(loc_driver, rot_driver, ('LOC', 'ROT'), s.source, mapping.source, 'LOCAL_SPACE')

			loc_driver.expression = 'rt_bone_loc("%s","%s","%s",%s)' % (axis, s.target.name, mapping.target, ','.join(src_vars))
			rot_driver.expression = 'rt_bone_rot("%s","%s","%s",%s)' % (axis, s.target.name, mapping.target, ','.join(src_vars))




	
	for i, limb in enumerate(s.ik_limbs):
		if not limb.enabled:
			continue

		mapping = s.get_mapping_for_target(limb.target_bone)
		src_arma, src_pose = s.get_pose_and_arma_bone('source', mapping.source)
		dest_arma, dest_pose = s.get_pose_and_arma_bone('target', mapping.target)

		loc_drivers = limb.target_empty.driver_add('location')
		rot_drivers = limb.target_empty.driver_add('rotation_euler')

		for axis, lfc, rfc in zip(('x','y','z'), loc_drivers, rot_drivers):
			loc_driver = lfc.driver
			rot_driver = rfc.driver

			src_vars = create_vars(loc_driver, rot_driver, ('LOC', 'ROT'), s.source, mapping.source, 'WORLD_SPACE')
			ctl_vars = create_vars(loc_driver, rot_driver, ('LOC', 'ROT', 'SCALE'), limb.control_cube, '', 'LOCAL_SPACE', offset=len(src_vars))

			loc_driver.expression = 'rt_ikt_loc("%s","%s",%i,%s)' % (axis, s.target.name, i, ','.join(src_vars + ctl_vars))
			rot_driver.expression = 'rt_ikt_rot("%s","%s",%i,%s)' % (axis, s.target.name, i, ','.join(src_vars + ctl_vars))


classes = []