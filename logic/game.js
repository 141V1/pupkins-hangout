// The world's rules: Fountain Square, a place to hang out. There's nothing to win and no tick to run: it's a presence
// world. Each player's own screen says where they are, which way they face and how fast they're going; the room keeps
// that inside what's described here, then shows it to everyone else in the world. So this file only describes a
// player's state, and the page (client/main.js) moves them. Make it your world: more fields (a hat colour, sitting, a
// held item: up to 16 of them), other emotes, a bigger square. CLAUDE.md has the rest.
import { defineLogic } from '@pupkins/create/logic';
import { SCENE } from './scene.js';

// The square, the fountain and where players come in are laid out in scenes/square.scene.json; the scene editor writes
// their places to logic/scene.js (in millimetres) on each save, so a bigger square there is a bigger square here.
const MM = 1000;
export const SQUARE = SCENE.square[0].w / 2 / MM;   // metres from the centre to the square's edge, on x and z (24)
export const FOUNTAIN = SCENE.fountain[0].r / MM;   // the fountain basin's radius: nobody walks through it (3.2)
const SPAWN = { x: SCENE.spawn[0].x / MM, z: SCENE.spawn[0].z / MM };
export const SPEED = { walk: 2.2, run: 5.2 };   // metres a second (the characters' walk and run look right at these)
export const EMOTES = ['Wave', 'Cheer', 'Jump', 'Cute', 'Yes', 'Bow'];

export default defineLogic({
  mode: 'presence',
  id: 'pupkins-hangout',
  version: 2,   // bump it when the presence changes: players still on the old one are told to reload
  // a player's state, field by field: the room keeps every field inside these (and rounds numbers to their step)
  presence: {
    x: { min: -(SQUARE + 2), max: SQUARE + 2 },
    y: { min: 0, max: 4, step: 0.01 },      // height off the ground (jump)
    z: { min: -(SQUARE + 2), max: SQUARE + 2 },
    yaw: 'angle',                           // which way they face (radians; 0 faces +z, toward the camera)
    speed: { min: 0, max: 6, step: 0.1 },   // how fast they're going: the others' screens animate the walk and run from it
  },
  spawn: SPAWN,                             // where players come in (in front of the fountain), and where R takes you back
  maxSpeed: 6,                              // metres a second: anyone moving faster is held to it
  capacity: 24,                             // players in one world; the next ones go to its twin (plaza-2, ...)
  emotes: EMOTES,
});
