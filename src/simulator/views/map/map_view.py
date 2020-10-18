from time import sleep

from heapq import heappush, heappop
from typing import List, Any, Tuple, Optional, Union

from algorithms.configuration.entities.entity import Entity
from simulator.models.model import Model
from simulator.services.debug import DebugLevel
from simulator.services.services import Services
from simulator.services.event_manager.events.event import Event
from simulator.services.event_manager.events.window_loaded_event import WindowLoadedEvent
from simulator.services.event_manager.events.key_frame_event import KeyFrameEvent
from simulator.services.event_manager.events.take_screenshot_event import TakeScreenshotEvent

from simulator.views.map_displays.entities_map_display import EntitiesMapDisplay
from simulator.views.map_displays.map_display import MapDisplay
from simulator.views.map_displays.numbers_map_display import NumbersMapDisplay
from simulator.views.map_displays.online_lstm_map_display import OnlineLSTMMapDisplay
from simulator.views.view import View
from structures import Point

from simulator.views.panda.gui.view_editor import ViewEditor
from simulator.views.map.camera import Camera
from simulator.views.map.voxel_map import VoxelMap
from simulator.views.map.colour import Colour, TRANSPARENT

from panda3d.core import NodePath
import math

class MapView(View):
    __displays: List[Any]

    __world: NodePath
    __map: VoxelMap
    __cam: Camera
    __vs: ViewEditor
    
    __tc_previous: List[List[List[Colour]]]
    __tc_scratchpad: List[List[List[Colour]]]

    def __init__(self, services: Services, model: Model, root_view: Optional[View]) -> None:
        super().__init__(services, model, root_view)        
        self.__displays = []
        self.__tc_previous = {}
        self.__tc_scratchpad = {}

    def notify(self, event: Event) -> None:
        super().notify(event)
        if isinstance(event, WindowLoadedEvent):
            self.__init()
        elif isinstance(event, KeyFrameEvent):
            if event.is_first:
                self.__tc_reset()
            self.update_view()
        elif isinstance(event, TakeScreenshotEvent):
            self.take_screenshot()

    def __to_point3(self, v: Union[Point, Entity]):
        if isinstance(v, Entity):
            v = v.position
        return Point(*v, 0) if len(v) == 2 else v

    def __init(self):
        base = self._services.window

        # disables the default camera behaviour
        base.disable_mouse()

        base.set_background_color(0, 0, 0.2, 1)

        # Creating the world origin as a dummy node
        self.__world = base.render.attach_new_node("world")

        map_data = {}
        for x in range(0, self._services.algorithm.map.size.width):
            map_data[x] = {}
            for y in range(0, self._services.algorithm.map.size.height):
                map_data[x][y] = {}
                map_data[x][y][0] = not self._services.algorithm.map.is_agent_valid_pos(Point(x, y, 0))

        start_pos = self.__to_point3(self._services.algorithm.map.agent)
        goal_pos = self.__to_point3(self._services.algorithm.map.goal)

        # MAP #
        self.__map = VoxelMap(map_data, self.__world, start_pos=start_pos, goal_pos=goal_pos, artificial_lighting=True)

        # map centering - todo: use tight bounds
        self.__map.root.set_pos(self.__world.getX() - len(self.map.traversables_data) / 2, self.__world.getY() - len(self.map.traversables_data) / 2, self.__world.getZ() - len(self.map.traversables_data) / 2)

        # CAMERA #
        self.__cam = Camera(base, base.cam, self.__world)

        # GUI #
        self.__vs = ViewEditor(base, self.map)

        self.update_view()

    @property
    def map(self) -> str:
        return 'map'

    @map.getter
    def map(self) -> VoxelMap:
        return self.__map

    def __tc_reset(self) -> None:
        self.__tc_scratchpad = {}
        self.__tc_previous = {}
        for x in self.map.traversables_mesh.structure:
            for y in self.map.traversables_mesh.structure[x]:
                for z in self.map.traversables_mesh.structure[x][y]:
                    self.map.traversables_mesh.reset_cube_colour(Point(x, y, z))

    def __get_displays(self) -> None:
        self.__displays = []
        displays: List[MapDisplay] = [EntitiesMapDisplay(self._services)]
        # drop map displays if not compatible with display format
        displays += list(filter(lambda d: self._services.settings.simulator_grid_display or not isinstance(d, NumbersMapDisplay),
                                self._services.algorithm.instance.get_display_info()))
        for display in displays:
            display._model = self._model
            self.add_child(display)
            heappush(self.__displays, (display.z_index, display))

    def __render_displays(self) -> None:
        while len(self.__displays) > 0:
            display: MapDisplay
            _, display = heappop(self.__displays)
            display.render() # update simulated map data (colours)
        
        # update actual viewable map data
        # lazily update mesh data, maybe this is actually slower
        """
        for x in self.__tc_scratchpad:
            if x in self.__tc_previous:
                for y in self.__tc_scratchpad[x]:
                    if y in self.__tc_previous[x]:
                        for z in self.__tc_scratchpad[x][y]:
                            if z in self.__tc_previous[x][y]:
                                def approx_eq(c1, c2):
                                    r1, g1, b1, a1 = c1
                                    r2, g2, b2, a2 = c2
                                    TOLERANCE = 1e-3
                                    return math.isclose(r1, r2, rel_tol=TOLERANCE) and \
                                           math.isclose(g1, g2, rel_tol=TOLERANCE) and \
                                           math.isclose(b1, b2, rel_tol=TOLERANCE) and \
                                           math.isclose(a1, a2, rel_tol=TOLERANCE)

                                if not approx_eq(self.__tc_previous[x][y][z], self.__tc_scratchpad[x][y][z]):
                                    self.map.traversables_mesh.set_cube_colour(Point(x, y, z), self.__tc_scratchpad[x][y][z])
                            else:
                                self.map.traversables_mesh.set_cube_colour(Point(x, y, z), self.__tc_scratchpad[x][y][z])
                    else:
                        for z in self.__tc_scratchpad[x][y]:
                            self.map.traversables_mesh.set_cube_colour(Point(x, y, z), self.__tc_scratchpad[x][y][z])
            else:
                for y in self.__tc_scratchpad[x]:
                    for z in self.__tc_scratchpad[x][y]:
                        self.map.traversables_mesh.set_cube_colour(Point(x, y, z), self.__tc_scratchpad[x][y][z])
        """
        for x in self.__tc_scratchpad:
            for y in self.__tc_scratchpad[x]:
                for z in self.__tc_scratchpad[x][y]:
                    self.map.traversables_mesh.set_cube_colour(Point(x, y, z), self.__tc_scratchpad[x][y][z])

        # for our purposes a simple reset on first frame may suffice
        # i.e. may not need to do the following on each frame
        for x in self.__tc_previous:
            should_reset = x not in self.__tc_scratchpad
            for y in self.__tc_previous[x]:
                if not should_reset:
                    should_reset = y not in self.__tc_scratchpad[x]
                for z in self.__tc_previous[x][y]:
                    if not should_reset:
                        should_reset = z not in self.__tc_scratchpad[x][y]
                    if should_reset:
                        self.map.traversables_mesh.reset_cube_colour(Point(x, y, z))

        self.__tc_previous = self.__tc_scratchpad
        self.__tc_scratchpad = {}

    def render_pos(self, pe: Union[Point, Entity], colour) -> None:
        x, y, z = self.__to_point3(pe)
        if x not in self.__tc_scratchpad:
            self.__tc_scratchpad[x] = {}
        if y not in self.__tc_scratchpad[x]:
            self.__tc_scratchpad[x][y] = {}
        if z not in self.__tc_scratchpad[x][y]:
            self.__tc_scratchpad[x][y][z] = TRANSPARENT
        dst = self.__tc_scratchpad[x][y][z]
        src = list(colour)
        for i in range(len(src)):
            src[i] /= 255
        src = Colour(*src)

        wda = dst.a * (1 - src.a) # weighted dst alpha
        a = src.a + wda
        r = (src.r * src.a + dst.r * wda) / a
        g = (src.g * src.a + dst.g * wda) / a
        b = (src.b * src.a + dst.b * wda) / a
        
        self.__tc_scratchpad[x][y][z] = Colour(r, g, b, a)

    def update_view(self) -> None:
        self.__get_displays()
        self.__render_displays()

    def take_screenshot(self) -> None:
        """
        self._model.save_screenshot(image)
        """
        print("TODO: take_screenshot")