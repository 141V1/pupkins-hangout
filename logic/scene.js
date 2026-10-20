// Made from scenes/square.scene.json by Pupkins Create: the scene editor writes it on each save, and
// `pupkins-create scene sync` makes it again. Edit the scene, not this file.
// Each name lists the objects the scene gives that logic name, in the scene's order, where they are in it, as
// whole numbers in the logic's units (1000 to a metre): x, y, z, and yaw, a 16-bit turn (65536 a full turn, as
// fixed.TURN, 0 facing +z); sizes: w, h, d (a box), r and h (a round thing, a marker's radius).
export const SCENE = {
  fountain: [
    { id: "fountain-edge", x: 0, y: 0, z: 0, yaw: 0, r: 3200 },
  ],
  spawn: [
    { id: "spawn", x: 0, y: 0, z: 7000, yaw: 0, r: 600 },
  ],
  square: [
    { id: "square", x: 0, y: -100, z: 0, yaw: 0, w: 48000, h: 200, d: 48000 },
  ],
};
