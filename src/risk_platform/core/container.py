"""Dependency injection wiring.

Binds abstract interfaces (ports) defined in the domain/application layers
to concrete implementations in the infrastructure layer. This is the single
place where the dependency direction is inverted at runtime, keeping inner
layers ignorant of outer layers.
"""
