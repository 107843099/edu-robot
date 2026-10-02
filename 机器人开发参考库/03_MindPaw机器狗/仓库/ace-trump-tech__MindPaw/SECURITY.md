# Security Policy

MindPaw controls physical actuators. Do not connect an untrusted network to a
powered robot, expose the AI Gateway to the public internet, or paste provider
keys into firmware, Issues, screenshots, or logs.

Report leaked credentials, unsafe actuator behavior, or a Gateway vulnerability
privately through the repository owner's GitHub profile. Do not publish a
working exploit or secret in a public Issue. Rotate any key that has appeared
in a log immediately.

The Gateway is an experimental research component. It is not a safety-rated
controller; keep a physical power cutoff available and test with the servos
disconnected before changing motion code.
