import compas.geometry as cg

class Inertia():
	"""
	A inertia object is defined by...
	http://docs.ros.org/kinetic/api/geometry_msgs/html/msg/Inertia.html

	Parameters
	----------
	mass: float [Kg]
	center_of_mass : list of 3 float [meters]
	inertia_tensor : 3x3 rotation matrix [kg-m**2]
	gravity_magniture : float [m/s**2]
	"""
	def __init__(self, mass, center_of_mass, inertia_tensor = None, gravity_magniture = 9.8):
		self.mass = mass
		self.center_of_mass = cg.Vector(*center_of_mass)
		self.inertia_tensor = inertia_tensor
		self.gravity_magniture = gravity_magniture
		self.gravity_vector_WCS = cg.Vector(0.0, 0.0, -self.gravity_magniture)