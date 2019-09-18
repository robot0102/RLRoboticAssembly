# RLRoboticAssembly

### Bugs, quirks, oddities

This following is a list of bugs, quirks, and oddities that are, at the time of
writing, unresolved. This list is unordered, partial, and evolving.

- The magnitude of force-torque feedback provided by the simulated sensor in
  PyBullet appears to be greater than that which is provided by the real sensor
  in our experiments. In order to correlate the two, we had to increase the real
  world force-torque feedback by a factor of 5 before providing it as input to
  the machine learning policy. The source of this behavior is unknown.

- The magnitude of velocity provided by the simulated robot in PyBullet appears
  to be greater than that which is provided by the real robot in our experiments.
  In order to correlate the two, we had to reduce both the linear and angular
  velocity provided by the policy by a factor of 5. This comes from the PyBullet
  method `p.changeConstraint()`, which is used to control the simulated tool.

- It is possible in PyBullet for two solid objects to intersect. Any velocities
  which are applied to a geometry in PyBullet should not cause that geometries
  to intersect with any other geometry. Both linear velocities and angular
  velocities are affected.

- The collision detection algorithm used in PyBullet places a small bounding box
  around all geometries and bodies for which collision detection is enabled. The
  dimension of this bounding box is 0.001m greater than the dimensions of that
  geometry. In order to account for this, mating surfaces therein must be "pushed
  back" so that the resulting bounding box corresponds with the actual, nominal
  geometry. Typically, we adjusted the geometry of the member held by the tool.
  Note that assemblies that do not implement this will be impossible to assemble.
  Note that the geometry used for visualization will hide the effects of this.

- The velocities provided by the machine learning policy do not ramp away from or
  towards zero at the start or stop point of a task, respectively. The real-world
  motion system must account for this or, otherwise, be capable of starting and
  stopping motion abruptly at these points.

- The distance for a task to be considered complete -- i.e for the tool frame to
  converge with the target frame -- must be positive and nonzero. This should be
  addressed using an `assert` statement elsewhere in the repository.

- Trained policies should reflect the control rate and delays present in your
  system. In order to train a policy that is able to control a system running at
  _n_ Hz, set the private class attribute `Task._time_step` to `1/n` before
  training.


### Notes

- ...


#
