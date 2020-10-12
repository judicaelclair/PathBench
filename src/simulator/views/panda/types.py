from typing import Tuple, TypeVar
from numbers import Real, Integral

TColour = Tuple[Integral, Integral, Integral]
Colour = TypeVar('Colour', Real, TColour)

IntPoint3 = Tuple[Integral, Integral, Integral]