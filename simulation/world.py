from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight, DirectionalLight,
    LVector4f, LPoint3f,
    CardMaker,
    TextNode
)
from direct.gui.OnscreenText import OnscreenText
import time

from agents.visuals import attach_lod_model


class SimulationWorld(ShowBase):
    """Windowed viewer: draws a Simulation and steps it once per frame."""

    def __init__(self, cfg, simulation):
        ShowBase.__init__(self)

        self.cfg = cfg
        self.sim = simulation
        self._frame_times = []
        self._last_time = time.time()

        self.sim.root.reparentTo(self.render)
        for agent in self.sim.agents:
            attach_lod_model(agent, self.loader, cfg["agents"], cfg["lod"])

        self._setup_camera()
        self._setup_lighting()
        self._setup_ground()

        if self.cfg["simulation"]["fps_overlay"]:
            self._setup_fps_overlay()

        self.taskMgr.add(self._step_simulation, "step_simulation")
        self.taskMgr.add(self._update, "main_update")

    def _setup_camera(self):
        self.accept("q", self.userExit)
        if self.camera is None:
            # window-type none (used by the tests): ShowBase makes no camera.
            return

        self.disableMouse()
        self.camera.setPos(0, -60, 40)
        self.camera.lookAt(LPoint3f(0, 0, 0))

        self.accept("arrow_up",    self._cam_forward)
        self.accept("arrow_down",  self._cam_back)
        self.accept("arrow_left",  self._cam_left)
        self.accept("arrow_right", self._cam_right)

    def _cam_forward(self):
        self.camera.setY(self.camera, 5)

    def _cam_back(self):
        self.camera.setY(self.camera, -5)

    def _cam_left(self):
        self.camera.setX(self.camera, -5)

    def _cam_right(self):
        self.camera.setX(self.camera, 5)

    def _setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor(LVector4f(0.4, 0.4, 0.4, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

        directional = DirectionalLight("directional")
        directional.setColor(LVector4f(0.9, 0.9, 0.8, 1))
        dn = self.render.attachNewNode(directional)
        dn.setHpr(45, -45, 0)
        self.render.setLight(dn)

    def _setup_ground(self):
        size = self.cfg["world"]["size"]
        cm = CardMaker("ground")
        cm.setFrame(-size / 2, size / 2, -size / 2, size / 2)
        ground = self.render.attachNewNode(cm.generate())
        ground.setP(-90)
        c = self.cfg["world"]["ground_color"]
        ground.setColor(c[0], c[1], c[2], c[3])

    def _setup_fps_overlay(self):
        self._fps_text = OnscreenText(
            text="FPS: --",
            pos=(-1.25, 0.92),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )
        self._agent_text = OnscreenText(
            text="Agents: 0",
            pos=(-1.25, 0.86),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )

    def _step_simulation(self, task):
        # Step by the real time elapsed since the previous frame.
        self.sim.step(self.clock.getDt())
        return task.cont

    def _update(self, task):
        now = time.time()
        dt = now - self._last_time
        self._last_time = now

        self._frame_times.append(dt)
        if len(self._frame_times) > 60:
            self._frame_times.pop(0)

        if self.cfg["simulation"]["fps_overlay"] and self._frame_times:
            avg = sum(self._frame_times) / len(self._frame_times)
            fps = int(1.0 / avg) if avg > 0 else 0
            self._fps_text.setText(f"FPS: {fps}")
            self._agent_text.setText(f"Agents: {len(self.sim.agents)}")

        return task.cont
