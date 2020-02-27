import bpy
from mathutils import Matrix, Vector
from .utilfuncs import *

def clear():
	s = state()

	for limb in s.ik_limbs:
		target_bone = s.get_pose_bone('target', limb.target_bone)

		if target_bone:
			for con in target_bone.constraints:
				if con.name == 'Retarget IK':
					target_bone.constraints.remove(con)
					break

		if limb.target_empty_child != None:
			bpy.data.objects.remove(limb.target_empty_child, do_unlink=True)
			limb.target_empty_child = None

		if limb.target_empty != None:
			bpy.data.objects.remove(limb.target_empty, do_unlink=True)
			limb.target_empty = None

		#if limb.pole_empty != None:
		#	bpy.data.objects.remove(limb.pole_empty, do_unlink=True)
		#	limb.pole_empty = None

		if limb.control_cube != None:
			limb.control_transform = matrix4x4_to_data(limb.control_cube.matrix_local)
			bpy.data.objects.remove(limb.control_cube, do_unlink=True)
			limb.control_cube = None

		if limb.control_holder != None:
			bpy.data.objects.remove(limb.control_holder, do_unlink=True)
			limb.control_holder = None


def build():
	s = state()
	aux_collection = next((c for c in bpy.data.collections if c.name == 'Retarget Auxiliary'), None)
	ctl_collection = next((c for c in bpy.data.collections if c.name == 'Retarget Control'), None)

	if aux_collection == None:
		aux_collection = bpy.data.collections.new('Retarget Auxiliary')
		#aux_collection.hide_viewport = True
		bpy.context.scene.collection.children.link(aux_collection)

	if ctl_collection == None:
		ctl_collection = bpy.data.collections.new('Retarget Control')
		bpy.context.scene.collection.children.link(ctl_collection)


	clear()

	h = s.target.dimensions.z

	for limb in s.ik_limbs:
		if not limb.enabled:
			continue

		target_arma_bone, target_bone = s.get_pose_and_arma_bone('target', limb.target_bone)
		mapping = s.get_mapping_for_target(limb.target_bone)

		te = bpy.data.objects.new(limb.target_bone + '-target', None)
		tec = bpy.data.objects.new(limb.target_bone + '-target-child', None)
		te.empty_display_size = h * 0.1
		te.empty_display_type = 'PLAIN_AXES'
		tec.empty_display_size = 0
		tec.empty_display_type = 'PLAIN_AXES'
		aux_collection.objects.link(te)
		aux_collection.objects.link(tec)
		te.parent = s.target
		tec.parent = te

		head = Vector(target_arma_bone.head_local)
		tail = Vector(target_arma_bone.tail_local)
		offset = head - tail

		tec.location.x = 0
		tec.location.y = target_arma_bone.length
		tec.location.z = 0

		#pe = bpy.data.objects.new(limb.target_bone + '-pole', None)
		#pe.empty_display_size = h * 0.1
		#pe.empty_display_type = 'PLAIN_AXES'
		#aux_collection.objects.link(pe)
		#pe.parent = s.target

		ch = bpy.data.objects.new(limb.target_bone + '-transform-holder', None)
		ch.empty_display_size = 0
		ctl_collection.objects.link(ch)
		ch.parent = s.target
		ch.matrix_local = loc_mat(target_arma_bone.matrix_local)

		cc = bpy.data.objects.new(limb.target_bone + '-transform', None)
		cc.empty_display_size = h * 0.1
		cc.empty_display_type = 'CUBE'
		ctl_collection.objects.link(cc)
		cc.parent = ch
		cc.matrix_local = data_to_matrix4x4(limb.control_transform)
		#ce.location.x, ce.location.y, ce.location.z = target_arma_bone.matrix_local.translation

		con = target_bone.constraints.new('IK')
		con.name = 'Retarget IK'
		con.target = tec
		#con.pole_target = pe
		con.use_rotation = True

		tb = target_bone.parent
		tbn = 0

		while tb != None:
			tbn += 1

			tb.lock_ik_x, tb.lock_ik_y, tb.lock_ik_z = tb.lock_rotation

			if tb.name == limb.origin_bone:
				break

			tb = tb.parent

		con.chain_count = tbn + 1


		limb.target_empty = te
		limb.target_empty_child = tec
		#limb.pole_empty = pe
		limb.control_holder = ch
		limb.control_cube = cc

