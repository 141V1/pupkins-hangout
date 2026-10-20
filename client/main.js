// The world's page: you walk around the square as your character and see everyone else who's in it. There are no
// rules to run (logic/game.js only says what a player's state holds): this page moves you, tells the world where you
// are with world.publish() every frame (it goes out when it changes, ten times a second at most), and draws everyone
// else where world.peers() says, smoothed between the world's updates. Anything a browser can do is fine here
// (CLAUDE.md lists the few things that aren't).
import { hub, joinWorld, saveName } from '@pupkins/create/client';
import { FREE_RIDERS, loadAvatar, preloadAvatar, readRiderKey, riderKey, saveRider } from '@pupkins/create/avatars';
import game, { EMOTES, FOUNTAIN, SPEED, SQUARE } from '../logic/game.js';
import { createWorld } from './world.js';

const manifest = await fetch('/pupkins.game.json').then((response) => response.json());
const $ = (id) => document.getElementById(id);
const scene = await createWorld($('view'));
const params = new URLSearchParams(location.search);

// ------------------------------------------------------------------ who you are
// A rider key: 'moki' (the free Moki), 'schiffy', or a wallet Moki ('moki#1234': try one with ?as=moki#1234 on the
// address). The world carries everyone's; loadAvatar builds the character from it.
let myRider = readRiderKey();
for (const kind of ['moki', 'schiffy']) preloadAvatar(kind);   // (fetch the characters' files while the menu is up)
function renderRiders() {
  const picks = FREE_RIDERS.some((r) => r.key === myRider) ? FREE_RIDERS : [...FREE_RIDERS, { key: myRider, name: myRider, portrait: null }];
  $('riders').replaceChildren(...picks.map((rider) => {
    const button = document.createElement('button');
    button.className = rider.key === myRider ? 'on' : '';
    if (rider.portrait) { const img = document.createElement('img'); img.src = rider.portrait; img.alt = ''; button.append(img); }
    button.append(rider.name);
    button.addEventListener('click', () => { myRider = riderKey(rider.key); saveRider(myRider); renderRiders(); });
    return button;
  }));
}
renderRiders();
const nameKey = { name: `${manifest.id}:name` };   // (where joinWorld looks for the name you last used)
try { $('name').value = localStorage.getItem(nameKey.name) ?? ''; } catch { /* storage blocked */ }
$('name').addEventListener('input', () => saveName(nameKey, $('name').value.trim()));
// in the hub (on the platform, or npm run dev's hub) you play as the hub's player: their name and the character the
// hub checked is theirs
const fromHub = await hub.player();
if (fromHub) {
  $('name').value = fromHub.name;
  myRider = fromHub.rider;
  renderRiders();
}
$('world').value = params.get('world') ?? '';

// ------------------------------------------------------------------ input
const held = new Set();
addEventListener('keydown', (event) => {
  if (event.target instanceof HTMLInputElement) return;
  held.add(event.code);
  if (event.code.startsWith('Arrow') || event.code === 'Space') event.preventDefault();
  if (event.repeat || !world) return;
  if (event.code === 'Space' && me.y === 0) me.vy = JUMP_SPEED;
  const n = Number(/^Digit([1-9])$/.exec(event.code)?.[1]);
  if (n && EMOTES[n - 1]) emote(EMOTES[n - 1]);
  if (event.code === 'KeyR') backToFountain();
  if (event.code === 'Escape') actions.menu();
});
addEventListener('keyup', (event) => held.delete(event.code));
addEventListener('blur', () => held.clear());
$('emotes').replaceChildren(...EMOTES.map((name, i) => {
  const button = document.createElement('button');
  button.textContent = `${i + 1} ${name}`;
  button.addEventListener('click', () => emote(name));
  return button;
}));
// a phone: drag anywhere on the view to walk, far to run
let drag = null;
const view = $('view');
view.addEventListener('pointerdown', (event) => { drag = { x0: event.clientX, y0: event.clientY, dx: 0, dy: 0, id: event.pointerId }; view.setPointerCapture(event.pointerId); });
view.addEventListener('pointermove', (event) => { if (drag?.id === event.pointerId) { drag.dx = event.clientX - drag.x0; drag.dy = event.clientY - drag.y0; } });
const endDrag = (event) => { if (drag?.id === event.pointerId) drag = null; };
view.addEventListener('pointerup', endDrag);
view.addEventListener('pointercancel', endDrag);
const key = (...codes) => codes.some((code) => held.has(code));

/** Where you're asking to go: { dx, dz } (screen up = away from the camera = -z) and whether you run. */
function wanted() {
  if (drag && Math.hypot(drag.dx, drag.dy) > 18) return { dx: drag.dx, dz: drag.dy, run: Math.hypot(drag.dx, drag.dy) > 80 };
  const dx = (key('KeyD', 'ArrowRight') ? 1 : 0) - (key('KeyA', 'ArrowLeft') ? 1 : 0);
  const dz = (key('KeyS', 'ArrowDown') ? 1 : 0) - (key('KeyW', 'ArrowUp') ? 1 : 0);
  return { dx, dz, run: key('ShiftLeft', 'ShiftRight') };
}

// ------------------------------------------------------------------ you
const me = { x: game.defaults.x, y: 0, z: game.defaults.z, yaw: game.defaults.yaw, speed: 0, vy: 0, avatar: null, tag: null };
const GRAVITY = -18;
const JUMP_SPEED = 7.5;
const turn = (from, to) => Math.atan2(Math.sin(to - from), Math.cos(to - from));
function walk(dt) {
  const { dx, dz, run } = wanted();
  const length = Math.hypot(dx, dz);
  me.speed += ((length ? (run ? SPEED.run : SPEED.walk) : 0) - me.speed) * (1 - Math.exp(-10 * dt));
  if (length) {
    me.yaw += turn(me.yaw, Math.atan2(dx, dz)) * (1 - Math.exp(-14 * dt));
    me.x += (dx / length) * me.speed * dt;
    me.z += (dz / length) * me.speed * dt;
  }
  const r = Math.hypot(me.x, me.z);   // (round the fountain, not through it; and stay on the square)
  if (r < FOUNTAIN + 0.45) { const k = (FOUNTAIN + 0.45) / Math.max(r, 0.001); me.x *= k; me.z *= k; }
  me.x = Math.max(-SQUARE + 0.4, Math.min(SQUARE - 0.4, me.x));
  me.z = Math.max(-SQUARE + 0.4, Math.min(SQUARE - 0.4, me.z));
  // jump
  me.vy += GRAVITY * dt;
  me.y += me.vy * dt;
  if (me.y <= 0) { me.y = 0; me.vy = 0; }
}
function emote(name) {
  if (world?.emote(name)) me.avatar?.emote(name);   // (true when it went out: one a second)
}
function backToFountain() {
  Object.assign(me, { x: game.defaults.x, y: 0, z: game.defaults.z, yaw: game.defaults.yaw, speed: 0, vy: 0 });
  world?.teleport({ x: me.x, y: 0, z: me.z, yaw: me.yaw, speed: 0 });   // (a jump: the others see you appear there)
}

// ------------------------------------------------------------------ everyone else
const cast = new Map();   // id -> { avatar, tag, rider }
function makeTag(you = false) {
  const tag = document.createElement('div');
  tag.className = you ? 'tag you' : 'tag';
  $('tags').append(tag);
  return tag;
}
function addCharacter(rider, onLoad) {
  loadAvatar(rider).then(onLoad).catch((error) => console.warn('[world] no character for', rider, error));
}
function castFor(peer) {
  let c = cast.get(peer.id);
  if (c && c.rider === peer.rider) return c;
  if (c) { c.avatar?.dispose(); c.tag.remove(); }   // (they picked another character)
  c = { avatar: null, tag: makeTag(), rider: peer.rider };
  cast.set(peer.id, c);
  addCharacter(peer.rider, (avatar) => {
    if (cast.get(peer.id) !== c) { avatar.dispose(); return; }   // (gone, or changed again, while it loaded)
    c.avatar = avatar;
    scene.scene.add(avatar.root);
  });
  return c;
}
function dropCast(id) {
  const c = cast.get(id);
  if (!c) return;
  c.avatar?.dispose();
  c.tag.remove();
  cast.delete(id);
}
function placeTag(tag, x, height, z, text) {
  const at = scene.project(x, height + 0.2, z);   // (just over the head: this camera is close)
  tag.hidden = !at;
  if (at) { tag.style.left = `${at.x}px`; tag.style.top = `${at.y}px`; }
  if (tag.textContent !== text) tag.textContent = text;
}

// ------------------------------------------------------------------ the world
let world = null;
function join() {
  const name = $('name').value.trim();
  const worldName = $('world').value.trim() || 'plaza';
  world = joinWorld({ logic: game, game: manifest.id, world: worldName, name, rider: myRider, state: { x: me.x, z: me.z, yaw: me.yaw, speed: 0 } });
  world.on('emote', ({ id, name: emoteName }) => cast.get(id)?.avatar?.emote(emoteName));
  world.on('leave', dropCast);
  world.on('status', (status) => {
    $('status').textContent = { open: '', connecting: 'Joining...', reconnecting: 'Reconnecting...', offline: "Can't reach the world: trying again", full: 'Every world of that name is full: trying again' }[status] ?? status;
  });
  world.on('closed', (reason) => { $('status').textContent = reason; });
  me.tag = makeTag(true);
  addCharacter(myRider, (avatar) => {
    if (!world) { avatar.dispose(); return; }
    me.avatar = avatar;
    scene.scene.add(avatar.root);
  });
  $('menu').hidden = true;
  $('hud').hidden = false;
  $('emotes').hidden = false;
}

const actions = {
  join,
  copy: () => hub.invite({ world: world?.world ?? 'plaza' }),   // (in the hub, the hub's link: players never see the page's own address)
  menu: () => {
    world?.leave();
    world = null;
    for (const id of [...cast.keys()]) dropCast(id);
    me.avatar?.dispose();
    me.avatar = null;
    me.tag?.remove();
    me.tag = null;
    $('status').textContent = '';
    $('menu').hidden = false;
    $('hud').hidden = true;
    $('emotes').hidden = true;
  },
};
document.addEventListener('click', (event) => { const act = event.target.closest('[data-act]')?.dataset.act; if (act) actions[act](); });
hub.ready();   // the menu is up: the hub drops its loading card

// ------------------------------------------------------------------ drawing
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  if (world) {
    walk(dt);
    world.publish({ x: me.x, y: me.y, z: me.z, yaw: me.yaw, speed: me.speed });
    if (me.avatar) {
      me.avatar.root.position.set(me.x, me.y, me.z);
      me.avatar.root.rotation.y = me.yaw;
      me.avatar.setSpeed(me.speed);
      me.avatar.update(dt);
    }
    placeTag(me.tag, me.x, me.y + (me.avatar?.height ?? 1.15), me.z, 'You');
    const here = new Set();
    for (const peer of world.peers()) {
      here.add(peer.id);
      const c = castFor(peer);
      const { x, y, z, yaw, speed } = peer.state;
      if (c.avatar) {
        c.avatar.root.position.set(x, y ?? 0, z);
        c.avatar.root.rotation.y = yaw;
        c.avatar.setSpeed(speed);
        c.avatar.update(dt);
      }
      placeTag(c.tag, x, (y ?? 0) + (c.avatar?.height ?? 1.15), z, peer.name);
    }
    for (const id of [...cast.keys()]) if (!here.has(id)) dropCast(id);
    const label = `${world.world ?? 'joining'} · ${world.count || 1} here`;
    if ($('here').textContent !== label) $('here').textContent = label;
    scene.follow(me.x, me.z, dt);
  } else {
    scene.follow(game.defaults.x, game.defaults.z, dt);
  }
  scene.render(dt);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// an invite link (?world=name) goes straight in
if (params.get('world')) join();
