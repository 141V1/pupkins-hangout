"""Pupkins Create: animations for our characters posed by hand, in Blender.

Clips are written in JavaScript (anims/<Name>.js, with @pupkins/create/anim) and need no Blender. This file is for the
clips a person poses by hand: `pupkins-create anim open <Name>` runs it to make anims/<Name>.<character>.blend (the
character standing as in the game and an action to animate), and `pupkins-create anim build` runs it in Blender (in
the background) to sample every .blend's clips, frame by frame, for the kit to turn into the clips files the game loads
(client/anims/moki.glb and client/anims/schiffy.glb). A clip made on one character plays on the other too: it is
carried over part by part (the parts are named the same on both characters) and set as far off the floor.

Rig(kind, armature) is a character's rig in Blender: its standing pose as the game shows it, its own axes, its height
and its floor. rig.turn((bend, turn, tilt)), rig.bones_for(part, angles) and rig.pose(turns, move, ground) pose it as
a clip script's poses do: the same parts, angles and floor.
"""
import json
import math
import sys
import traceback
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

PARTS = {
    'moki': {
        'body': 'Hips', 'spine': 'Spine', 'head': 'Head', 'leaf': 'Leaf', 'ear_l': 'Ear_L', 'ear_r': 'Ear_R',
        'shoulder_l': 'LeftShoulder', 'upper_arm_l': 'LeftUpperArm', 'lower_arm_l': 'LeftLowerArm', 'hand_l': 'LeftHand',
        'shoulder_r': 'RightShoulder', 'upper_arm_r': 'RightUpperArm', 'lower_arm_r': 'RightLowerArm', 'hand_r': 'RightHand',
        'upper_leg_l': 'LeftUpperLeg', 'lower_leg_l': 'LeftLowerLeg', 'foot_l': 'LeftFoot',
        'upper_leg_r': 'RightUpperLeg', 'lower_leg_r': 'RightLowerLeg', 'foot_r': 'RightFoot',
        'tail': 'Tail1', 'tail_2': 'Tail2', 'tail_3': 'Tail3',
    },
    'schiffy': {
        'body': 'pelvis', 'spine': 'spine_01', 'chest': 'spine_03', 'neck': 'neck_01', 'head': 'head', 'jaw': 'Jaw_M',
        'ear_l': 'ear_l1', 'ear_r': 'ear_r1',
        'shoulder_l': 'clavicle_l', 'upper_arm_l': 'upperarm_l', 'lower_arm_l': 'lowerarm_l', 'hand_l': 'hand_l',
        'shoulder_r': 'cravicre_r', 'upper_arm_r': 'upperarm_r', 'lower_arm_r': 'rowerarm_r', 'hand_r': 'hand_r',
        'upper_leg_l': 'thigh_l', 'lower_leg_l': 'calf_l', 'foot_l': 'foot_l',
        'upper_leg_r': 'thigh_r', 'lower_leg_r': 'calf_r', 'foot_r': 'foot_r',
        'tail': 'tail01', 'tail_2': 'tail02', 'tail_3': 'tail03',
    },
}
PAIRS = ('shoulder', 'upper_arm', 'lower_arm', 'hand', 'upper_leg', 'lower_leg', 'foot', 'ear')
EVERY_PART = sorted({p for parts in PARTS.values() for p in parts} | set(PAIRS))
PLAY = (('loop', False), ('hold', False), ('interruptible', False), ('full', True))
NAME_OK = 'letters, digits, _ and -, starting with a letter, up to 40 characters'

CLIPS = []        # the clips made so far: { name, action, fps, start, frames, play, source }
SOURCE = None     # the file being read now
SKIPPED = set()   # parts asked for that the character hasn't got: (part, character)


def name_ok(name):
    return 0 < len(name) <= 40 and name[0].isascii() and name[0].isalpha() and all(ch.isascii() and (ch.isalnum() or ch in '_-') for ch in name)


def fcurves_of(action):
    """An action's F-curves, in Blender 4 (action.fcurves) and from Blender 4.4 on (layered actions)."""
    layers = getattr(action, 'layers', None)
    if layers is not None and len(layers):
        return [curve for layer in layers for strip in layer.strips for bag in getattr(strip, 'channelbags', []) for curve in bag.fcurves]
    return list(getattr(action, 'fcurves', []))


def use_action(arm, action):
    """Makes action the armature's active one (from Blender 4.4 on, with its slot), or none."""
    data = arm.animation_data
    data.action = action
    if action is not None and hasattr(data, 'action_slot') and data.action_slot is None and len(getattr(action, 'slots', [])):
        data.action_slot = action.slots[0]


def set_frame(scene, frame):
    whole = math.floor(frame)
    scene.frame_set(int(whole), subframe=float(frame - whole))


def key_frame(arm, action, frame, last):
    """Keys every bone of the pose as it stands into action at frame (each rotation the short way round from last)."""
    use_action(arm, action)
    for p in arm.pose.bones:
        q = p.rotation_quaternion.copy()
        if p.name in last and q.dot(last[p.name]) < 0:
            q.negate()
        p.rotation_quaternion = q
        last[p.name] = q.copy()
        p.keyframe_insert('rotation_quaternion', frame=frame)
        p.keyframe_insert('location', frame=frame)


def moves_bones(action):
    return any(curve.data_path.startswith('pose.bones') for curve in fcurves_of(action))


class Rig:
    """A character's rig in the scene: its armature, its standing pose (where every clip starts), its own axes, its
    height and its floor."""

    def __init__(self, kind, arm):
        if kind not in PARTS:
            raise ValueError(f'no character called {kind!r}')
        self.kind, self.arm, self.parts = kind, arm, PARTS[kind]
        missing = [bone for bone in self.parts.values() if bone not in arm.pose.bones]
        if missing:
            raise RuntimeError(f"this isn't the {kind}'s rig: it has no {', '.join(missing)}")
        scene = bpy.context.scene
        arm.animation_data_create()
        for track in arm.animation_data.nla_tracks:
            track.mute = True
        idle = next((a for a in bpy.data.actions if a.get('pupkins_idle')), None)
        idle = idle or next((a for a in bpy.data.actions if a.name.startswith('PSPS_Idle')), None)
        if idle is None:
            raise RuntimeError(f"the {kind}'s rig has lost its idle clip")
        idle['pupkins_idle'] = True
        for action in bpy.data.actions:
            if action.name.startswith(('PSPS_Idle', 'PSPS_Run')):
                action['pupkins_base'] = True
        use_action(arm, idle)
        set_frame(scene, idle.frame_range[0])
        bpy.context.view_layer.update()
        if kind == 'moki':
            self.settle(scene, idle)
        use_action(arm, None)
        self.base = {p.name: p.matrix_basis.copy() for p in arm.pose.bones}
        self.reset()
        self.idle = {p.name: p.matrix.copy() for p in arm.pose.bones}   # armature space
        # the character's own axes (armature space): up from its hips to its head, its right from its left upper arm to
        # its right one, forward from those two
        bones = arm.data.bones
        up = (bones[self.parts['head']].head_local - bones[self.parts['body']].head_local).normalized()
        right = bones[self.parts['upper_arm_r']].head_local - bones[self.parts['upper_arm_l']].head_local
        right = (right - up * right.dot(up)).normalized()
        self.up, self.left, self.forward = up, -right, up.cross(right)
        self.frame = Matrix((self.left, self.up, self.forward)).transposed().to_quaternion()   # character -> armature
        # the meshes, which of their vertices hang off the tail, its height (all of it) and its floor (its lowest point
        # leaving out the tail), standing
        self.meshes = []
        for obj in scene.objects:
            if obj.type != 'MESH' or obj.parent != arm or not len(obj.data.vertices):
                continue
            groups = [g.name.lower() for g in obj.vertex_groups]
            tail = np.zeros(len(obj.data.vertices), dtype=bool)
            for v in obj.data.vertices:
                best = max(v.groups, key=lambda g: g.weight, default=None)
                tail[v.index] = best is not None and best.group < len(groups) and 'tail' in groups[best.group]
            self.meshes.append((obj, tail))
        every, body, tail = self.heights()
        self.floor = float(body.min()) if body.size else 0.0
        self.height = float(every.max() - every.min()) if every.size else 1.0
        self.tail_low = (float(tail.min()) - self.floor) / self.height if tail.size else 0.0   # (standing, the tail may hang below the feet)

    def settle(self, scene, idle):
        """The Moki's standing pose as the game shows it: its idle's first frame with the game's arm settle (the arms
        eased toward their average over the idle and turned down, the body and head toward their rest)."""
        arm = self.arm
        arms = [p for p in arm.pose.bones if p.name.endswith(('Shoulder', 'UpperArm', 'LowerArm', 'Hand'))]
        sums = {p.name: Vector((0.0, 0.0, 0.0, 0.0)) for p in arms}
        anchors = {}
        first, last = idle.frame_range
        for k in range(48):
            set_frame(scene, first + (last - first) * k / 48)
            for p in arms:
                q = Vector(p.rotation_quaternion)
                anchors.setdefault(p.name, q.copy())
                sums[p.name] += q if q.dot(anchors[p.name]) >= 0 else -q
        set_frame(scene, first)
        bpy.context.view_layer.update()
        use_action(arm, None)   # (the edits below must not be played over)
        for p in arms:
            p.rotation_quaternion = Quaternion(sums[p.name]).normalized().slerp(p.rotation_quaternion.copy(), 0.4)
        for name, motion in (('Hips', 0.35), ('Spine', 0.35), ('Head', 0.3)):
            p = arm.pose.bones.get(name)
            if p:
                p.rotation_quaternion = Quaternion().slerp(p.rotation_quaternion.copy(), motion)
        bpy.context.view_layer.update()
        world = arm.matrix_world.to_quaternion()
        for side in ('Left', 'Right'):
            chain = [arm.pose.bones.get(f'{side}{n}') for n in ('UpperArm', 'LowerArm', 'Hand')]
            if not all(chain):
                continue
            for bone, child, down in ((chain[0], chain[1], 48), (chain[1], chain[2], 62)):
                head = arm.matrix_world @ bone.head
                now = (arm.matrix_world @ child.head - head).normalized()
                level = Vector((now.x, now.y, 0.0))
                if level.length_squared < 1e-8:
                    continue
                level.normalize()
                want = level * math.cos(math.radians(down)) + Vector((0.0, 0.0, -math.sin(math.radians(down))))
                turn = world.inverted() @ Quaternion().slerp(now.rotation_difference(want), 0.94) @ world
                at = bone.head.copy()
                bone.matrix = Matrix.Translation(at) @ turn.to_matrix().to_4x4() @ Matrix.Translation(-at) @ bone.matrix
                bpy.context.view_layer.update()

    def reset(self):
        for p in self.arm.pose.bones:
            p.matrix_basis = self.base[p.name].copy()
        bpy.context.view_layer.update()

    def heights(self):
        """The mesh's heights (armature units, along up) as posed now: every vertex's, the body's (the tail left out)
        and the tail's."""
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        inverse = self.arm.matrix_world.inverted()
        up = np.array(self.up)
        every, tails = [], []
        for obj, tail in self.meshes:
            evaluated = obj.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            co = np.empty(len(mesh.vertices) * 3)
            mesh.vertices.foreach_get('co', co)
            evaluated.to_mesh_clear()
            m = np.array(inverse @ obj.matrix_world)
            every.append((co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]) @ up)
            tails.append(tail if len(tail) == len(every[-1]) else np.zeros(len(every[-1]), dtype=bool))
        if not every:
            return np.zeros(0), np.zeros(0), np.zeros(0)
        every, tails = np.concatenate(every), np.concatenate(tails)
        return every, every[~tails], every[tails]

    def to_character(self, q):
        return self.frame.inverted() @ q @ self.frame

    def from_character(self, q):
        return self.frame @ q @ self.frame.inverted()

    def turn(self, angles):
        """(bend, turn, tilt) degrees about the character's axes -> a rotation in armature space."""
        bend, turn, tilt = (math.radians(float(a)) for a in angles)
        return Quaternion(self.up, turn) @ Quaternion(self.left, bend) @ Quaternion(-self.forward, tilt)

    def bones_for(self, part, angles):
        """[(bone, angles)] for a part (both sides of a pair, mirrored), [] when this character hasn't got it."""
        if part in PAIRS:
            bend, turn, tilt = angles
            return self.bones_for(f'{part}_l', (bend, turn, tilt)) + self.bones_for(f'{part}_r', (bend, -turn, -tilt))
        if part not in EVERY_PART:
            raise ValueError(f"there's no part called {part!r}: the parts are {', '.join(EVERY_PART)}")
        if part not in self.parts:
            SKIPPED.add((part, self.kind))
            return []
        return [(self.parts[part], angles)]

    def ancestor(self, bone, among):
        """The nearest bone above bone that's one of among (bone names), or None."""
        b = self.arm.data.bones[bone].parent
        while b is not None and b.name not in among:
            b = b.parent
        return b.name if b is not None else None

    def pose(self, turns, move=None, ground=None):
        """Sets the whole pose (no action playing): the standing pose, each bone in turns ({bone: armature-space
        rotation}) turned at its joint on top of the bones it hangs from, the hips moved by move (character axes, its
        heights) and, with ground (a height above the floor in its heights: 0 on it), its lowest point (the tail left
        out) set that high."""
        arm = self.arm
        for p in arm.pose.bones:
            p.matrix_basis = self.base[p.name].copy()
        for bone, turn in turns.items():
            at = self.idle[bone].to_quaternion()
            extra = at.inverted() @ turn @ at   # the turn, in the bone's own frame
            loc, rot, scale = self.base[bone].decompose()
            arm.pose.bones[bone].matrix_basis = Matrix.LocRotScale(loc, rot @ extra, scale)
        left, up, forward = (float(m) for m in (move or (0, 0, 0)))
        self.shift((self.left * left + self.up * up + self.forward * forward) * self.height)
        if ground is not None:
            _, body, _ = self.heights()
            if body.size:
                self.shift(self.up * (self.floor + ground * self.height - float(body.min())))

    def shift(self, by):
        """Moves the hips by `by` (armature space)."""
        if by.length_squared < 1e-14:
            return
        hips = self.arm.pose.bones[self.parts['body']]
        frame = (self.idle[hips.name] @ self.base[hips.name].inverted()).to_3x3()   # the hips' basis -> armature
        loc, rot, scale = hips.matrix_basis.decompose()
        hips.matrix_basis = Matrix.LocRotScale(loc + frame.inverted() @ by, rot, scale)

    def capture(self):
        """The pose as it stands, part by part, for another character: each part's turn from the standing pose
        (character axes; whole, the parts it hangs from included), how far the hips moved and how high its lowest
        point is (its heights)."""
        arm = self.arm
        turns = {}
        for part, bone in self.parts.items():
            now = arm.pose.bones[bone].matrix.to_quaternion() @ self.idle[bone].to_quaternion().inverted()
            turns[part] = self.to_character(now)
        hips = self.parts['body']
        moved = arm.pose.bones[hips].matrix.translation - self.idle[hips].translation
        move = tuple(moved.dot(axis) / self.height for axis in (self.left, self.up, self.forward))
        _, body, _ = self.heights()
        air = (float(body.min()) - self.floor) / self.height if body.size else 0.0
        return turns, move, air

    def pose_captured(self, turns, move, air):
        """Poses this character as captured from another (Rig.capture), its lowest point as high off the floor."""
        bones = {self.parts[part]: self.from_character(q) for part, q in turns.items() if part in self.parts}
        relative = {}
        for bone, q in bones.items():
            above = self.ancestor(bone, bones)
            relative[bone] = bones[above].inverted() @ q if above else q
        self.pose(relative, move, ground=air)


# ------------------------------------------------------------------------------------------------ the build
def flat(m):
    """A 4x4 as 16 numbers, column by column (as glTF has them)."""
    return [round(m[row][col], 6) for col in range(4) for row in range(4)]


def sample(rig, made):
    """Each clip's bone poses (armature space), frame by frame, and how high its lowest point is (its heights)."""
    arm, scene = rig.arm, bpy.context.scene
    out = []
    for c in made:
        use_action(arm, c['action'])
        poses = {p.name: [] for p in arm.pose.bones}
        lows, tails = [], []
        for i in range(c['frames'] + 1):
            set_frame(scene, c['start'] + i)
            for p in arm.pose.bones:
                poses[p.name].extend(flat(p.matrix))
            _, body, tail = rig.heights()
            lows.append(round((float(body.min()) - rig.floor) / rig.height, 4) if body.size else 0.0)
            tails.append(round((float(tail.min()) - rig.floor) / rig.height, 4) if tail.size else 0.0)
        use_action(arm, None)
        out.append({'name': c['name'], 'fps': c['fps'], 'frames': c['frames'] + 1, 'play': c['play'], 'source': c['source'],
                    'poses': poses, 'floor': {'body': lows, 'tail': tails}})
    return out


def rest_of(arm):
    """The armature's place in the world and its bones' rest (armature space)."""
    return {'world': flat(arm.matrix_world), 'bones': {b.name: flat(b.matrix_local) for b in arm.data.bones}}


def blend_clips():
    """The clips in an opened .blend: every action that moves bones but the rig's own clips (from its first key)."""
    scene = bpy.context.scene
    fps = scene.render.fps / (scene.render.fps_base or 1)
    made = []
    for action in bpy.data.actions:
        if action.get('pupkins_base') or action.get('pupkins_idle') or (action.users == 0 and not action.use_fake_user):
            continue
        if not moves_bones(action):
            continue
        name = action.name.strip()
        if not name_ok(name):
            raise ValueError(f'the action {name!r}: a clip name is {NAME_OK}')
        first, last = action.frame_range
        made.append({'name': name, 'action': action, 'fps': fps, 'start': float(first), 'frames': max(1, round(last - first)),
                     'play': {key: bool(action.get(key, default)) for key, default in PLAY}, 'source': SOURCE})
    return made


def explain(source):
    """The error that's being handled, short: what it was and its last steps."""
    kind, error, trace = sys.exc_info()
    return f'{source}: {kind.__name__}: {error}\n' + ''.join(traceback.format_tb(trace, limit=-3))


def build(rigs, blends, out):
    """Samples every .blend's clips for every character (rigs: {character: its model .glb}) and writes their poses as
    JSON: on its own character as it is, on the others carried over part by part."""
    global SOURCE
    result = {'rigs': {kind: {'rests': {}, 'clips': []} for kind in rigs}, 'errors': [], 'skipped': []}
    errors = result['errors']

    def fail(message):
        if message not in errors:
            errors.append(message)

    # the .blend files: their clips as they are on their own character, captured part by part for the others
    carried = []
    for blend in blends:
        SOURCE = Path(blend).name
        try:
            bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False)
            kind = bpy.context.scene.get('pupkins_rig')
            if kind not in rigs:
                raise ValueError(f"this .blend isn't one `pupkins-create anim open` made (its character: {kind!r})")
            arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
            rig = Rig(kind, arm)
            made = blend_clips()
            entry = result['rigs'][kind]
            entry['rests'][SOURCE] = rest_of(arm)
            entry['clips'].extend(dict(c, rest=SOURCE) for c in sample(rig, made))
            for c in made:
                use_action(arm, c['action'])
                frames = []
                for i in range(c['frames'] + 1):
                    set_frame(bpy.context.scene, c['start'] + i)
                    frames.append(rig.capture())
                use_action(arm, None)
                carried.append(dict(c, action=None, frames=frames, kind=kind))
        except Exception:
            fail(explain(SOURCE))

    for kind, model in rigs.items():
        if not any(c['kind'] != kind for c in carried):
            continue   # (nothing to carry over to this character)
        try:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=str(model))
            arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
            rig = Rig(kind, arm)
        except Exception:
            fail(explain(f"the {kind}'s rig"))
            continue
        CLIPS.clear()
        for c in carried:
            if c['kind'] == kind:
                continue
            SOURCE = c['source']
            try:
                action = bpy.data.actions.new(c['name'])
                action.use_fake_user = True
                last = {}
                for i, (turns, move, air) in enumerate(c['frames']):
                    use_action(arm, None)
                    rig.pose_captured(turns, move, air)
                    key_frame(arm, action, i, last)
                use_action(arm, None)
                for curve in fcurves_of(action):
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
                CLIPS.append(dict(c, action=action, start=0.0, frames=len(c['frames']) - 1))
                rig.reset()
            except Exception:
                fail(explain(f'{SOURCE} (carried over to the {kind})'))
        entry = result['rigs'][kind]
        names = [c['name'] for c in CLIPS] + [c['name'] for c in entry['clips']]
        twice = sorted({n for n in names if names.count(n) > 1})
        if twice:
            fail(f"two clips are called {', '.join(twice)}: a clip name is one clip's")
        entry['rests']['import'] = rest_of(arm)
        entry['clips'].extend(dict(c, rest='import') for c in sample(rig, CLIPS))
    named = {'moki': 'the Moki', 'schiffy': 'Schiffy'}
    result['skipped'] = sorted({f'{part} ({named.get(kind, kind)} has none)' for part, kind in SKIPPED})
    Path(out).write_text(json.dumps(result, separators=(',', ':')), encoding='utf-8')
    print(f"PUPKINS_ANIM built {sum(len(r['clips']) for r in result['rigs'].values())} clips, {len(errors)} errors")


def open_new(kind, model, name, save, play):
    """A .blend to animate by hand: the character standing as in the game, a new action called name holding that pose
    at frame 0 (30 fps; the timeline runs to frame 30 to start with)."""
    if not name_ok(name):
        raise ValueError(f'a clip name is {NAME_OK}: {name!r}')
    bpy.ops.wm.read_factory_settings(use_empty=False)
    for obj in list(bpy.context.scene.objects):
        if obj.type not in ('CAMERA', 'LIGHT'):
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=str(model))
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    rig = Rig(kind, arm)
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH' and obj.parent is None:
            bpy.data.objects.remove(obj, do_unlink=True)   # (the importer's bone shape)
    scene = bpy.context.scene
    scene['pupkins_rig'] = kind
    scene.render.fps, scene.render.fps_base = 30, 1
    scene.frame_start, scene.frame_end = 0, 30
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    for key, value in play.items():
        action[key] = value
    rig.pose({})
    key_frame(arm, action, 0, {})
    scene.frame_set(0)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.save_as_mainfile(filepath=str(save))
    print(f'PUPKINS_ANIM saved {save}')


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if not args:
        return
    command, rest = args[0], args[1:]

    def values(name):
        out, i = [], 0
        while i < len(rest):
            if rest[i] == f'--{name}':
                i += 1
                while i < len(rest) and not rest[i].startswith('--'):
                    out.append(rest[i])
                    i += 1
            else:
                i += 1
        return out

    def value(name):
        found = values(name)
        return found[0] if found else None

    if command == 'build':
        rigs = dict(pair.split('=', 1) for pair in values('rig'))
        build(rigs, values('blends'), value('out'))
    elif command == 'open':
        play = {key: True for key in values('play')}
        play.setdefault('full', True)
        open_new(value('rig'), value('model'), value('name'), value('save'), play)
    else:
        raise SystemExit(f'pupkins_anim: no command {command!r}')


if __name__ == '__main__':
    main()
