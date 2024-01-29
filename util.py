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
	if len(values) == 4 * 4:
		size = 4
	elif len(values) == 3 * 3:
		size = 3
	else:
		raise Exception('invalid matrix size when deserializing')
	
	rows = []
	
	for i in range(0, len(values), size):
		rows.append(values[i:i+size])

	return Matrix(rows)


def matrix_to_list(matrix):
	values = []

	for row in matrix:
		for value in row:
			values.append(value)

	return values