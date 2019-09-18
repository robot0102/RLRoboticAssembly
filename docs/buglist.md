# RLRoboticAssembly

### Input Devices

This file describes usage of input devices, used to capture human input for the
purpose of debugging and demonstration.

- During this project, we used a variety of devices, including an 3DConnexion
  SpaceMouse, Xbox controller, random number generator, and the PyBullet GUI
  (described below). We did not use devices that offer haptic feedback.

- There appears to be a bug in using threaded input devices with PyGame on MacOS.
  We recommended that you query your device only as needed.

- By default, human input is captured by sliders added onto the PyBullet GUI. We
  recommend that you replace this with an ergonomic device, such as a joystick or
  game controller.

- The `ActionSlider` class is an input devices that uses the PyBullet GUI to create
  of sliders within the simulation window and that can be adjusted using a mouse
  to control the simulated end-effector. This device does not require any external
  hardware or drivers.


### Notes

- ...


#
