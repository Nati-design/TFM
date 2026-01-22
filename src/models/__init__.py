"""
VRP Models Package

This package contains the core classes for representing
Vehicle Routing Problem instances and solutions.
"""

from .vrp_instance import VRPInstance
from .vrp_solution import VRPSolution

__all__ = ["VRPInstance", "VRPSolution"]
