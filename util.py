import bpy
from mathutils import Matrix


def rot_mat(mat):
	return mat.to_quaternion().to_matrix().to_4x4()


def loc_mat(mat):
	return Matrix.Translation(mat.to_translation()).to_4x4()


def extract_rot_axis_from_mat(mat, axis):
	return getattr(mat.to_quaternion().to_euler(), axis)


def extract_loc_axis_from_mat(mat, axis):
	return getattr(mat.to_translation(), axis)


def list_to_matrix(values):
	return Matrix((values[0:4], values[4:8], values[8:12], values[12:16]))


def matrix_to_list(matrix):
	values = []

	for y in range(0, 4):
		for x in range(0, 4):
			values.append(matrix[y][x])

	return values