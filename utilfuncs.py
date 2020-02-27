import bpy
from mathutils import Matrix, Vector

def state():
	return bpy.context.object.animation_retarget_state

def data_to_matrix4x4(values):
	return Matrix((values[0:4], values[4:8], values[8:12], values[12:16]))

def matrix4x4_to_data(matrix):
	values = []

	for y in range(0, 4):
		for x in range(0, 4):
			values.append(matrix[y][x])

	return values


def rot_mat(mat):
	return mat.to_quaternion().to_matrix().to_4x4()

def loc_mat(mat):
	return Matrix.Translation(mat.to_translation()).to_4x4()

def alert_error(title, message):
	def draw(self, context):
		self.layout.label(text=message)

	bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')