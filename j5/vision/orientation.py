"""Orientation classes to represent rotations in space."""

from typing import List, Tuple

from pyquaternion import Quaternion


class Orientation:
    """
    Represents an orientation in 3D space.

    Uses a unit quaternion as an internal representation.
    """

    def __init__(self, orientation: Quaternion):
        self._quaternion = orientation

    @classmethod
    def from_cartesian(cls, x: float, y: float, z: float) -> 'Orientation':
        """Create a coordinate from a cartesian position."""
        q = Quaternion(axis=(1, 0, 0), angle=x)
        q = q.rotate(Quaternion(axis=(0, 1, 0), angle=y))
        q = q.rotate(Quaternion(axis=(0, 0, 1), angle=z))

        return cls(q)

    @property
    def matrix(self) -> List[List[float]]:
        """Get a 3x3 rotation matrix representing the 3D rotation."""
        return self._quaternion.rotation_matrix

    @property
    def yaw_pitch_roll(self) -> Tuple[float, float, float]:
        """
        Get the equivalent yaw-pitch-roll angles in radians.

        Specifically, intrinsic Tait-Bryan angles following the z-y'-x'' convention.

        See pyquaternion for details.
        """
        return self._quaternion.yaw_pitch_roll

    @property
    def yaw(self) -> float:
        """Rotation angle around the z-axis in radians."""
        return self.yaw_pitch_roll[0]

    @property
    def pitch(self) -> float:
        """Rotation angle around the y'-axis in radians."""
        return self.yaw_pitch_roll[1]

    @property
    def roll(self) -> float:
        """Rotation angle around the x''-axis in radians."""
        return self.yaw_pitch_roll[2]

    @property
    def x(self) -> float:
        """Alias to roll."""
        return self.roll

    @property
    def y(self) -> float:
        """Alias to pitch."""
        return self.pitch

    @property
    def z(self) -> float:
        """Alias to yaw."""
        return self.yaw

    def __repr__(self) -> str:
        """
        A string representation.

        Note that the actual parameters used to construct this are not
        used, because this is likely to confuse students.
        """
        return f"Orientation(" \
               f"x_radians={self.x}, " \
               f"y_radians={self.y}, " \
               f"z_radians={self.z}" \
               f")"
