# @pupkins/create

Make games for Pupkins. A game is its **logic** (the rules, a deterministic tick function every player's screen and
the room run identically) and its **page** (drawing, sound, menus, input). Online play, rooms, quick match, rejoining
and CPU stand-ins come with the platform. A game's rooms run in one of four modes: **rollback** (real time: every
screen runs the logic and predicts), **lockstep** (real time for big games: every screen steps the logic a tick at a
time once everyone's input for it is in, so a game can hold armies of units and an input can be a list of numbers),
**turns** (hidden information and turn-by-turn play: only the room runs it, and each screen sees only what its seat
may see) or **presence** (a world to hang out in, many players at once: there are no rules to run, each screen says
where its player is and the world shows everyone else). See "Lockstep games", "Turns games" and "Worlds" below.

```bash
pupkins-create starters        # the games to start from, one line each
pupkins-create new my-game     # a working game to start from (folder "." = this empty one); --starter <id> picks which
npm run dev                    # the game in the hub at http://localhost:5300 (as on the platform), online rooms; pages reload as you edit
npm run edit                   # the same, with the scene editor open: the game's places laid out in the browser
npm run check                  # the checks the platform runs; every failure says how to fix it
npm run playtest               # evidence for a playtest: many bot games' numbers, the page played with screenshots
pupkins-create share           # the game on a public link, for friends to play with you (Ctrl+C ends it)
pupkins-create publish         # the game to the platform: built and checked in a machine of its own, kept by hash
pupkins-create release         # players get the last build that passed, at the game's address (--off takes it off)
pupkins-create logs            # what happened online: faults (call, tick, message), rooms that couldn't start, plays a day
pupkins-create props barrel    # our props (3D things to place) that match, with each one's size; library: to look at them
pupkins-create login          # once: signs you in in your browser, so our characters and props load (and publish works)
pupkins-create logout          # signs this machine out
pupkins-create doctor          # what this machine has for the kit, and what it's missing
```

Our characters (the Moki, Schiffy, wallet Mokis) load once you're signed in. `pupkins-create login` opens the
platform's sign-in page in your browser: sign in with your account, allow the kit, and it finishes on its own (if no
browser opens, open the address it prints, on the same computer). It keeps the sign-in in `~/.pupkins/session.json`
and renews it as it goes. With a key from an invite instead, `pupkins-create login <key>` saves the key (in
`~/.pupkins/key`; `PUPKINS_KEY` overrides both). `pupkins-create logout` signs the machine out. Without a sign-in,
games still run, with no characters. `pupkins-create doctor` says whether this machine has everything: Node.js 22 or
newer, Chrome, the sign-in.

`npm run check` ends in headless Chrome. It opens the game in the hub emulator (as the platform runs it: see "In the
hub" below), presses its play button and plays for about 11 s (keys held and let go, clicks on the view), and any
page or console error fails it, as does anything the platform's guard reports (a wallet reached for, the CSP refusing
something, a service worker). The play button is the one marked
`data-check="play"`, else the starters' **Play vs CPUs** (`data-act="cpu"`), or a world's **Join**. It saves
screenshots in `.pupkins/check/screens/`: the page as it opened (`menu.png`) and three moments of the game
(`play-3.png`, `play-7.png`, `play-12.png`). Look at them to see your game.

`npm run playtest` (`pupkins-create playtest [--games 40] [--seconds 24] [--to-end] [--keys] [--no-browser]`) gathers what a
playtest judges, in `.pupkins/playtest/report.md` (and `report.json`): many games between test players (the logic's
`bot()` at every seat) on the defaults and each option's other values, with how often each seat wins, each seat's
average score (when `result()` gives `scores`, a number a seat), how long games run and how many never end; then the
game played against CPUs in the hub emulator for `--seconds` (with `--to-end`, until the game is over), the page's own
seat played by the game's `bot()` so it gets as far as a CPU does (the playtest sets `window.__pupkinsAutoplay`, which
`playLocal` reads; with `--keys`, or a game with no `bot()`, random keys and clicks instead), a screenshot
every 3 s (every 10 s after the first 30) named by its second (`play-012s.png`) and the end screen (`end.png`), its frame times (the worst, and when),
what the page shows, its errors and what the platform's guard saw. The plugin's **playtest agent** runs it with the
checks and reports bugs, balance, the screens and how it plays, each with its evidence.

### Playing with friends: `share`

`pupkins-create share` puts the game on a public link. Send it to friends: they play in their browser, with you and
each other, from anywhere, in the same rooms `npm run dev` has. The game runs on this machine, and a free quick
tunnel carries the link (its program, cloudflared, is downloaded once into `~/.pupkins`). The link is up while
`share` runs: Ctrl+C ends it, and the next `share` gets a new link. Keep the machine awake while friends play.

- The link serves what the page loads and nothing else of the folder: no dot files (`.env`, `.git`), no packages
  but the SDK.
- Pages don't reload as you edit: friends reload to get your changes, and a reload drops them out of a game.
- Start it in the background, like `npm run dev`, and wait for the line with the link (`... is at https://...`).
  `--port` picks the port if 5300 is taken.

### Sending the game to the platform: `publish`

`pupkins-create publish` sends the game to the platform as you (your sign-in). The platform builds it in a machine of
its own (`npm ci` if the game has packages, `npm run build` if it has a build script, then every check `npm run
check` runs) and keeps the build by its hash. It says each step as it finishes and ends with the build's hash, or
with what failed and why. A build usually takes under a minute.

- It sends the folder but its dot folders and files (`.git`, `.env`, `.pupkins`, `.claude`) and `node_modules`. Up
  to 50 MB packed, 150 MB of files, 25 MB a file, 4,000 files. `--dry-run` lists what would go and sends nothing.
- Packages come from the npm registry only (exact versions in `package-lock.json`; no git or file packages), and they
  install without their install scripts. The machine has no internet but the registry, and that only while packages
  install.
- Each creator gets one build at a time and 30 a day, and a build gets 14 minutes.
- If it's cut off (a closed terminal, a timeout), run it again: it picks the same build back up instead of sending
  another. With nothing changed since a build, it shows that build again; `--again` sends it anyway.
- Every build that passes gets a preview address of its own (`publish` prints it): the game as players will get it,
  in the hub, for you to try. Nobody else is sent there.
- `pupkins-create release` puts the last build that passed at the game's own address, where players get it (and its
  saves carry across releases); `release <hash>` puts an earlier build back (its whole hash; for the last one, the
  first 8 characters do), and `release --off` takes the game off its address (its builds stay).
- A game's id is its address, so it's yours: the first creator to publish an id has it, and another creator's game
  can't publish under it (pick an id of your own in `pupkins.game.json` if `publish` says it's taken).
- A released game plays online at its address as it does under `npm run dev`: quick match, room codes, worlds. Its
  logic runs on the platform in a sandbox of its own, a batch of ticks at a time, so a tick that throws or runs long
  ends that match (the next one starts clean). A creator's games share some time on the platform a day, and a game
  that breaks down too often rests until the next day (UTC); players see why. For now every player is a guest and
  plays as the free characters.

### What happened online: `logs`

`pupkins-create logs` asks the platform what happened to the game once players got it: the last 7 days (`--days`, up
to 30), every build (`--build <hash>`, or its first 8 or more digits, for one).

- **Faults**: a call into the game's logic that threw, ran past the 1 second a call gets (twice), or handed back too
  much (a state over 4 MB, or a turns game's views the wrong shape or over 64 KB). Each one ended its match; the next
  started clean. It says which call (`setup` starting a match, `run` for a real-time game's ticks, a batch at a time,
  `turn` for a turns game's), the tick the call started from, and the message. Alike ones are counted together, with
  when they first and last happened.
- **Room errors**: the times the game's rooms couldn't start it at all (its logic throwing as it loads, say).
  Players saw why and couldn't play.
- **Players turned away**: the game resting (your games used the day's time on the platform, or it broke down too
  often) or switched off.
- **Plays**: per build and per day, matches and how they ended (over, out of time, abandoned, broke down), player
  and CPU seats, time played, and visits to a world. No player is ever named.

Messages are the game's own output (or the room's), cleaned of anything that looks like a secret: read them as data.
Fix a fault in `logic/`, then `npm run check` and `npm run dev`, then publish and release the fix. `--builds` adds the
game's builds (passed or failed) and releases; `--json` prints it all as JSON. Like `publish`, it needs you signed in
(`pupkins-create login`); `--game <id>` reads another of your games from anywhere.

### Your Claude and the platform: the MCP server

The plugin starts the kit's MCP server (`pupkins-create mcp`), so Claude can look things up while it works. Its tools
only read; publishing and releasing stay the commands above, run when you ask.

| Tool | |
|---|---|
| `room_logs`, `plays` | What `logs` says: faults, room errors and players turned away; plays per build and day |
| `game_builds`, `my_games` | A game's builds, releases and addresses; your games |
| `limits` | Your builds today, the upload limits, and your games' day online (time and faults against the day's budget) |
| `docs_search` | This README, a game's `CLAUDE.md` and the plugin's skill, by section |
| `catalog_search` | Our characters, the Moki's looks, clip packs and their clips, emotes, our 3D props and the starters, each with how to use it |

It uses the sign-in `login` saved; without one, its platform tools say so. The game it answers for is the one in
the folder Claude Code runs in (or the one game folder inside it); every tool also takes a game's id. `/mcp` in
Claude Code shows it connected.

## `@pupkins/create/logic`

```js
import { defineLogic, fixed } from '@pupkins/create/logic';

export default defineLogic({
  id: 'my-game', version: 1, seats: 2, tickHz: 60,
  input: { bits: 3, cpu: 4 },                    // inputs are small integers; `cpu` hands a seat to your CPU
  options: { points: { values: [3, 5, 7], default: 5, label: 'Points to win' } },
  setup(match) { return { tick: 0, rng: match.seed | 0, /* ... */ }; },
  step(state, inputs) { /* one tick; mutate the state or return a new one */ },
  result(state, why) { return over(state) ? { winner: 0 } : null; },
  bot(state, seat) { return 0; },               // how a test player plays
});
```

| Field | |
|---|---|
| `mode` | `'rollback'` (the default), `'lockstep'` (see "Lockstep games"), `'turns'` (see "Turns games") or `'presence'` (a world: see "Worlds", which has its own fields); `pupkins.game.json`'s `multiplayer.mode` says the same |
| `seats` | Players in a game, 1-16 (required) |
| `setup(match)` | The starting state (required). `match.seed` seeds randomness, `match.seats[i]` is `{ cpu, name, rider, pick }` (a pick: what that player chose before the game, see "Picks"; null for a CPU), `match.options` the lobby's settings |
| `step(state, inputs)` | One tick (required). `inputs[seat]` is that seat's input this tick (a lockstep game's: a list, or null; a turns game's gets actions instead) |
| `result(state, why)` | `null` while the game goes on, then `{ winner, ... }` (`winner`: a seat, a team, or -1 for a draw). If the room has to stop a game itself, `why` says why and the standing is the result |
| `input` | `{ bits }` or `{ mask }` (default 16 bits), `idle` (no input, default 0), `cpu` (the input that hands a seat to your CPU; empty seats and dropped players get it). A lockstep game's is `{ length }`: see "Lockstep games" |
| `options` | Settings players choose, `{ name: { values, default, label } }`; `setup` reads them from `match.options`. The starters' pages show them in the menu (games on one screen) and in a private room's lobby (any seated player may change them); quick matches use the defaults |
| `teams` | Seats grouped into teams, `[[0, 1], [2, 3]]`: new players join the emptier team |
| `bot(state, seat)` | How a test player plays: `npm run check` and its online test use it. It only reads the state (`check` fails a bot that changes it). `check` also plays a game between CPUs (every seat sending `input.cpu`; in a lockstep game every seat null) and times the slowest tick. A turns game's is `bot(view, seat)`, which also plays its empty seats |
| `cpuSeat(i)` | How an empty seat appears: `{ name, rider }` (default `CPU n`, the free Moki) |
| `tickHz`, `maxTicks` | Ticks a second (default 60; a lockstep game 30, at most 60; a turns game 10, at most 30); the longest game a room allows (default 30 minutes; a turns game an hour) |
| `checksum`, `clone` | Defaults hash and copy the state; override only for speed. Online, the room compares checksums to catch a screen that drifted, so a checksum must cover the whole state (`check` warns when yours misses part of it) |
| `version` | Bump it when a rule changes what a game computes: rooms turn away pages on another version |

`fixed` is whole-number maths that every machine computes identically. An angle is a whole number from 0 to 65535
for a full turn (`fixed.TURN` is 65536), and sine and cosine come back scaled by `fixed.Q14` (16384):

| `fixed.` | Gives |
|---|---|
| `idiv(a, b)` | a / b, rounded toward zero |
| `mulDiv(a, b, c)` | a × b / c, rounded toward zero: scaling by a fraction (keep a × b under 2^53) |
| `isqrt(n)` | the square root of n, rounded down |
| `dist2(ax, ay, bx, by)` | the squared distance between two points: compare it with `r * r`, no root needed |
| `idist(ax, ay, bx, by)` | the distance between two points, rounded down |
| `octile(dx, dy)` | a grid distance: 10 a straight step, 14 a diagonal one |
| `isin(angle)`, `icos(angle)` | sine and cosine × 16384: a step of `len` along an angle is `mulDiv(icos(a), len, Q14)`, `mulDiv(isin(a), len, Q14)` |
| `iatan2(dy, dx)` | the angle of the vector (dx, dy): 0 along +dx, a quarter turn (16384) along +dy (atan2's argument order) |
| `angleDelta(a, b)` | the shortest turn from angle a to angle b, -32768 to 32767 |
| `turnToward(a, b, maxStep)` | angle a turned toward b by at most maxStep |
| `scaleTo(dx, dy, len)` | the vector (dx, dy) made len long, as `[x, y]` (`[0, 0]` for no direction) |
| `rand(state)` | the next random whole number from `state.rng`, 0 to 2^32 - 1 |
| `randInt(state, n)` | a random whole number from 0 to n - 1 (n under 2^21) |
| `randRange(state, lo, hi)` | a random whole number from lo to hi, both included |
| `hashString(text)`, `hashInts(list)` | a 32-bit hash of some text or of a list of whole numbers (for seeds) |

A facing on a top-down ground (x across, z toward the camera, facing 0 along +z) is `yaw = fixed.iatan2(dx, dz)`,
and a step of `speed` along it is `x += mulDiv(isin(yaw), speed, Q14)`, `z += mulDiv(icos(yaw), speed, Q14)`: the 3D
starters do this. `dmath` is the floating-point alternative (`dsqrt`, `dsin`, `dcos`, `datan2`); prefer `fixed`.

The rules for logic: whole numbers; no `Math.random`, `Date`, `performance` or timers; no transcendental `Math`
(`sqrt`, `sin`, `pow`...) and no `**`; no `for...in` and no `sort()` without a comparator; plain objects and arrays in
the state; imports only from `@pupkins/create/logic` and the logic's own files.

## `@pupkins/create/client`

```js
import { playLocal, playOnline, randomRoomCode } from '@pupkins/create/client';

const match = playLocal({ logic, seats: ['me', 'cpu'], input: (state, seat) => bits });
const online = playOnline({ logic, game: 'my-game', quick: true, input: (state, seat) => bits });
// every animation frame: draw(match.state, match.seat)
online.on('end', (result) => showResult(result));
```

- **`playLocal({ logic, seats, input, options, seed, names, riders, picks, load })`**: a game on this screen (a turns
  game: see "Turns games"). `seats`: one entry a
  seat, `'me'` (your `input`), `'cpu'`, or a function `(state, seat) => input` for a second local player. `names`,
  `riders` and `picks` (one entry a seat, optional) are the seats' names, characters and picks; a CPU seat left out
  takes `cpuSeat(i)`'s. Events: `tick`, `end`, `go` (after a `load`), `pause`, `resume`. `match.pause()` and
  `match.resume()` stop and restart its clock (`match.paused`), and the hub's menu pauses it while it's open.
  `match.stop()` ends it.
- **`playOnline({ logic, game, quick | code, input, name, rider, pick, load })`**: a game in a room. `game` is the
  manifest's `id`; `quick: true` finds a quick match, `code` joins a private room (`randomRoomCode()` makes one;
  share `?room=CODE`). Events: `room` (the lobby: `room.seats`, `room.options`, `room.code`), `start`, `go`,
  `tick`, `end`, `status` (the connection), `closed` (the room let you go: a reason), `error`. In a private room's
  lobby, `ready(true)` (everyone seated ready starts the game), `option(name, value)` and `pick(value)`; after a game,
  `rematch()`; `leave()` to go. `match.seat` is your seat (`null` while watching) and `match.rtt` your round trip
  to the room (ms). A turns game also has `act(action)`; a lockstep game has `match.catching`, and `match.stalled`:
  how long (ms) it has been waiting on another player's input (show "waiting" past a moment).
- **`match.alpha`** (`playLocal` and `playOnline`, not a turns game): how far the clock is into the next tick, 0 to 1.
  Draw moving things that far between their last two places and they glide at any frame rate.
- **`joinWorld({ logic, game, world, name, rider, state })`**: a presence world (see "Worlds").

A hidden tab hands its seat to the CPU until it's back, then catches up; a dropped connection reconnects and
rebuilds the game by itself.

**Loading.** A page that has to load before it can play (its characters, models, sounds) passes **`load`**: a
function `(match) => promise`, called when a game starts (`playOnline({ ..., load: (match) => buildCast(match) })`,
the same in `playLocal`). The room holds the game's clock until every seated player's page has finished, then
everyone hears `go` and the game starts together, so nobody starts behind. Show "loading" between `start` and
`go`. The room waits at most 30 seconds: a page still loading then plays as the CPU (its seat sends nothing) until
it's ready. A page that reloads mid-game loads again while it catches up. The 3D starters do this with their
characters.

**Picks.** What a player chose before the game (a character, a deck, a colour, a loadout) is their seat's **pick**: a
whole number or a list of up to 32 (`playOnline({ pick: [2, 7, 7, 9] })`, `online.pick(value)` in the lobby,
`playLocal({ picks })`). It reaches `setup` as `match.seats[seat].pick`, null for a CPU's seat or a player who
picked nothing, and `room.seats` shows everyone's in the lobby. Check it in `setup`: any value may arrive (a deck of
cards the player doesn't have, say), so turn what isn't allowed into a default. Picks are public: a secret choice is a
turns game's action.

## In the hub: `hub`, and `npm run dev`'s hub emulator

On pupkins.gg a game runs inside the hub's page: the hub's bar on top (the player, the menu, report), the game in
a frame under it. The frame is the game's own origin on a domain of its own, sandboxed, under the platform's
Content-Security-Policy, with the platform's guard script first in the page. `npm run dev` runs the same on this
machine: **the hub emulator** at `http://localhost:5300/`, the game's own origin at `http://127.0.0.1:5300/` (the
page on its own, for a quick look or a second player in another tab). A game that works in the emulator works on the
platform.

```js
import { hub } from '@pupkins/create/client';

const me = await hub.player();   // { name, rider }: the hub's player and the character the hub checked is theirs (null on a page on its own)
hub.ready();                     // the menu is up: the hub drops its loading card (check warns when a game never says so)
hub.invite({ room: code });      // the hub copies its own link to this game and room ({ world: name } for a world)
hub.on('pause', fn);             // the hub's menu opened over the game ('resume': it closed)
await hub.token();               // the player's game token: what this game's rooms take as who's in a seat (null on a page on its own)
hub.fullscreen();                // the hub fills the screen with the game and its bar
hub.exit();                      // back to the hub
```

`playLocal` pauses itself while the hub's menu is open; an online game goes on (the others are still playing). On a
page on its own every call still works: `player()` is `null`, `invite()` copies the page's own link (and returns it),
`fullscreen()` asks the browser. The starters use all of it.

What the frame allows, set by the platform (`check` names what it finds):
- **Scripts from the game's own files only.** The import map is the one inline script a page may have; any other
  inline `<script>`, `eval` and `new Function` are refused (`check` fails on them), and so are scripts from other
  sites: bundle what you use.
- **Connections** to the game's own origin (its rooms), the platform (`https://pupkins.gg/v1/` and its assets)
  and the page's own `blob:` and `data:`. Pictures, sounds and fonts come from the game's files or our assets.
- **No dialogs, forms, popups or fullscreen of its own.** `alert`, `confirm` and `prompt` show nothing; a `<form>`
  never submits (not even a submit event: use a button's click or a key); `window.open` and `target="_blank"` open
  nothing; `hub.fullscreen()` asks the hub. Pointer lock, gamepads, sound and motion sensors work. (`check` warns.)
- **No wallets, no service workers.** The guard hides any wallet extension's `window.ethereum` (and the like) and its
  EIP-6963 announcements, refuses service workers, and reports reaching for either, as it reports what the CSP refused
  and the page's uncaught errors: the emulator's **Log** button lists them, `npm run dev` prints them, and `check`
  fails on them. Games never ask players for their wallet.
- **Its own storage.** `localStorage` and IndexedDB are the game's own, kept across its versions (and apart from the
  same game's page opened on its own).
- **Its own address**, which players never see: an invite link comes from `hub.invite()`.

The emulator's bar has the player's name and character (`hub.player()`: changing them restarts the game as them),
**Menu** (the game hears `pause`, then `resume`), **Fullscreen**, **Report** and **Log** (what the game and the hub
said to each other, and what the guard saw). `?page=client/other.html` on its address shows another page of the
game's; any other query (`?room=`, `?world=`, `?as=`) goes on to the game.

**The player's game token.** The hub hands the game a short-lived token for its player (it names the game, the build,
the player as this game sees them, their name and their character, signed by the hub), and a fresh one before it runs
out. `playOnline` and `joinWorld` send it with every connection, so there's nothing to do: the room seats the token's
player, with the name and character the hub signed (whatever the page's own `name` and `rider` say), a second tab of
theirs takes over their seat, and a wallet Moki is only the one the hub checked is theirs (the free riders anyone can
switch to). A room on the platform turns away a connection without a token. The emulator does the same with a key of
its own: in it, each browser tab is one player; the page on its own has no token and plays as before.

## Lockstep games: big real-time games (`mode: 'lockstep'`)

A rollback game predicts the other players and rewinds when it guessed wrong: it copies the state every tick and
replays the last few, which is fine for a handful of players but too much for an army. A **lockstep** game steps each
tick once, on every screen, as soon as every player's input for it is in. There's nothing to predict, so a game can
hold hundreds of units (an RTS, a battle of summons, a herd), and an input can be a list of numbers: an order.

```js
export default defineLogic({
  mode: 'lockstep', seats: 4, tickHz: 30,
  input: { length: 3 },                                      // an input: a list of up to 3 whole numbers
  setup(match) { /* ... */ },
  step(state, inputs) {
    for (let seat = 0; seat < inputs.length; seat += 1) {
      const order = inputs[seat] ?? cpuOrder(state, seat);   // null: nobody is playing this seat, so the CPU does
      if (order.length >= 2) { /* [x, z, flags]: send the squad there */ }   // ([]: no order this tick)
    }
  },
  bot: cpuOrder,                                             // the checks' test player
});
```

- **Inputs** are lists of up to `input.length` whole numbers (default 16, at most 256), `[]` for nothing this tick.
  The page's `input(state, seat)` returns one (a single number is a list of one; anything else is `[]`). They're
  frozen: `step` reads them, never changes them.
- **`null` is a seat nobody is playing**: an empty seat, a player who dropped, one whose tab is hidden. Play it with
  your CPU, as the starter does, or leave it standing. A page may return `null` itself to hand its seat to the CPU for
  a while (an autopilot). `check` plays a game with null at every seat.
- **Delay.** Each screen sends its input a few ticks ahead, so it reaches the others in time: the room picks the first
  delay from the players' round trips (50 to 400 ms), then each screen moves its own as its connection changes, and
  paces itself to stay level with the others. There's nothing for the game to do, but a lockstep game feels the delay
  that a rollback game hides: it suits orders (point and go, build, cast) more than split-second aiming.
- **Coming back.** A screen that drops or reloads gets the inputs it missed and steps through them, a slice each
  frame; `match.catching` is true meanwhile (show "catching up", and skip sounds and bursts for those ticks: `if
  (match.catching) return;` in your `tick` handler). Its seat is null, the CPU's, until it's level, so nobody waits.
- The logic's rules are a rollback game's (whole numbers, randomness from the state). A lockstep game never copies its
  state, so `clone` isn't used. The room steps its own copy as the referee: it decides the result, and its checksums
  catch a screen that drifted, which then rebuilds by itself.

## Turns games: hidden information, turn by turn

In a rollback or lockstep game every screen runs the whole state, so nothing in it can be secret. A card game, secret
picks or a hidden board need `mode: 'turns'`: only the room runs the logic, and each screen gets its seat's **view**.
The state and the match's seed never leave the room. Play on the room's clock still ticks (`tickHz`, default 10), so
turn timers are ticks in the state.

```js
export default defineLogic({
  mode: 'turns', seats: 4, tickHz: 10,
  setup(match) { /* deal: randomness from match.seed, kept in the state */ },
  step(state, actions) {   // every tick, with the actions that came in since the last: [{ seat, action }], often none
    for (const { seat, action } of actions) { /* is it this seat's turn, and is the move allowed? then play it */ }
    /* a turn's clock: count it down, and move on when it runs out */
  },
  view(state, seat) {      // what this seat may see (seat -1: someone watching); build a new object
    return { hand: state.hands[seat]?.slice() ?? [], counts: state.hands.map((h) => h.length), turn: state.turn };
  },
  bot(view, seat) { return null; },   // an action, or null to wait: plays empty seats and dropped players, and the checks
  result(state, why) { return null; },
});
```

- **Actions** are a whole number or a list of up to 16 of them (never text): `match.act(7)`, `match.act([7, 2])`. The
  room drops anything else, and more than 4 from one seat in a tick. `step` decides whether an action is allowed: an
  action out of turn, or a card the seat doesn't hold, is simply ignored.
- **`view(state, seat)`** is the only thing a screen ever sees of the state (default: all of it). The room sends each
  screen its seat's view whenever it changes, so put what just happened in the state (events) and pass on in the view
  what that seat may know: "Ann drew a card", never which card.
- **The CPU is `bot(view, seat)`**: the room calls it every tick for each seat nobody's in (or whose player dropped),
  with a copy of that seat's view, so it plays fair. It's also how `npm run check` plays the game.
- **The page** draws `match.state`, which is your view (`'tick'` fires when a new one arrives), and moves with
  `match.act(action)`, online and against CPUs alike. `playLocal` also takes several seats for players on one screen:
  `match.act(action, seat)` and `match.view(seat)`; a function seat is a bot, `(view, seat) => action`.
- The logic's rules are the same as a rollback game's (whole numbers, randomness from the state), so `check` can replay
  a game and prove it. A turns room doesn't wait on screens: a hidden tab keeps its seat and its turn's clock runs.

## Worlds: a place to hang out (`mode: 'presence'`)

A hangout, a lobby, a social space: a world where everyone simply is, with no rules to run. Each player's screen owns
its player's state (where they are, which way they face, what they're doing) and tells the world; the world keeps it
inside what the logic allows and shows it to everyone else. A world holds up to 200 players (24 by default); when it's
full, newcomers go on to its twin (`plaza-2`, up to `plaza-8`).

```js
export default defineLogic({
  mode: 'presence',
  presence: {                          // a player's state, field by field (up to 16)
    x: { min: -26, max: 26 },          // a number kept between min and max, rounded to its step (default 0.01)
    z: { min: -26, max: 26 },
    yaw: 'angle',                      // radians, kept between -pi and pi
    say: ['none', 'hi', 'gg'],         // one of these words (the first is where everyone starts): chat is set phrases
    lantern: 'bool',
  },
  spawn: { x: 0, z: 7 },               // where players come in; a jump back here is always allowed (a respawn)
  maxSpeed: 6,                         // x, y and z units a second: anyone faster is held to it (leave it out for teleports)
  capacity: 24,                        // players in one world
  emotes: ['Wave', 'Cheer', 'Jump'],   // the emotes players may send (default: the characters' six)
});
```

```js
import { joinWorld } from '@pupkins/create/client';

const world = joinWorld({ logic, game: 'my-world', world: 'plaza', name, rider, state: { x: 0, z: 7 } });
// every animation frame:
world.publish({ x, z, yaw, anim });   // goes out when it changes, ten times a second at most
for (const p of world.peers()) draw(p.id, p.name, p.rider, p.state, p.emote);   // everyone else, smoothed
world.on('emote', ({ id, name }) => playEmote(id, name));
```

- **`world.publish(state)`**: any of presence's fields (one left out keeps its last value). The world cleans it the
  way the logic says: a number outside its range is clamped, a word the field doesn't list is ignored.
- **`world.peers()`**: everyone else, as `{ id, name, rider, state, emote }` (`emote`: `{ name, at }` for a few seconds
  after one), drawn 200 ms behind the world's clock, between its updates, so they move smoothly: numbers slide, angles
  turn the short way round, words change when they did. `world.peer(id)` is one of them. Events: `join` (a peer),
  `leave` (an id), `emote` (`{ id, name }`), `profile` (a peer's new name or character), `welcome`, `status`,
  `closed`.
- **`world.emote(name)`** plays one of the world's emotes for everyone (one a second: it returns false otherwise).
  **`world.teleport(state)`** is a jump the others snap to instead of sliding there (a respawn, a door).
  **`world.profile({ name, rider })`** changes how you look; **`world.leave()`** goes.
- `world.world` is the world you're in (`plaza`, or `plaza-2` when it was full) and `world.count` how many are there,
  you included. A dropped connection comes back by itself, as the same player; a hidden tab stays in the world.
- A world keeps no secrets and decides nothing: a game with rules and winners is a rollback, lockstep or turns game.
  With no `step` there's nothing to replay, so `npm run check` walks test players through the world instead (one of
  them too fast, one dropping and coming back) and checks everyone ends up seeing everyone where they really are.

## `@pupkins/create/avatars`: our characters

Players can play as themselves: the free Moki, Schiffy, or a Moki from their wallet. Every seat carries its
player's **rider key**: `'moki'`, `'schiffy'` or `'moki#<token id>'` (`match.seats[i].rider` in the logic's
`setup`, `room.seats[i].rider` in a lobby; `playOnline({ rider })` sends this player's). `loadAvatar(key)` builds
that character, rigged and animated, in our toon look. three.js comes with the kit (0.180; every starter's import
map has `three` and `three/addons/`).

```js
import * as THREE from 'three';
import { loadAvatar, readRiderKey } from '@pupkins/create/avatars';

const me = await loadAvatar(readRiderKey());           // this browser's pick, 'moki' until one is saved
scene.add(me.root);                                    // feet at the origin, facing +Z at rotation.y = 0
// every frame: me.root.position.set(x, 0, z); me.root.rotation.y = yaw; me.setSpeed(metresPerSecond); me.update(dt);
me.emote('Wave');                                      // returns how long it plays, in seconds
```

| The avatar | |
|---|---|
| `root` | The `THREE.Group` to place and turn. `height`: its height in metres (the Moki 1.15, Schiffy 1.2) |
| `setSpeed(mps)` | Idle, walk and run blend on one stride clock, with the feet planted while they touch the ground. Each kind looks best at its `moveSpeed` (`AVATAR_KINDS`: the Moki walks at 1.2 m/s and runs at 5.2) |
| `emote(name)` | `Wave`, `Cheer`, `Jump`, `Cute`, `Yes`, `Bow` (`AVATAR_EMOTES`); `busy` is how long the current one still runs. `play(name, options)` plays any clip by name: `Idle`, `Walk`, `Run`, those six, the actions pack's 25 (sitting, sleeping, knockouts, attacks, work, swimming: below) and clips you make in Blender (below) |
| `lookAt(target, weight)` | Turns the head toward a point (`THREE.Vector3`); `lookAt(null)` lets go |
| `update(dt)` | Every frame, with the seconds since the last. Avatars far from the camera or off screen update less often by themselves |
| `rider`, `fellBack` | `{ key, name, tokenId }`; `fellBack` is true when a look couldn't be dressed and the free Moki stands in |
| `packs`, `model`, `armSettle(mixer)` | Clip packs asked for with `loadAvatar(key, { clips: ['actions', 'hoops', './anims/{rig}.glb'] })` (`CLIP_PACKS`, or a clips file of your game's own). The actions pack's clips and your own play through the avatar (`play('Sit')`). `packs.hoops.clips` is a `Map` of `THREE.AnimationClip`s (39 basketball moves, 10 signature ones: Stepback, Shammgod, three dunks, the elbow hang, two celebrations; and 5 talk gestures: Talk, Point, Shrug, Clap, HandsOnHips) for a mixer of your own on `model`. A mixer playing the rig's own clips on the Moki applies `armSettle(mixer).apply(0..1)` after each update |
| `setShadows(cast, receive)`, `setOutline(color, width)`, `dispose()` | Shadows (on by default), an ink outline (off by default), and freeing it |

Characters of your own game's (villagers, fans, opponents): `createAvatar('moki', { skin: 'chef' })` for a Moki look
(`MOKI_SKINS`: `classic`, `guide`, `sailor`, `explorer`, `ninja`, `kimono`, `chef`, `starfluff`), `createAvatar('moki',
{ traits: { Fur: 'Gold', Clothing: 'Ninja' } })` for one dressed from Moki traits, `createAvatar('schiffy')`.

A character picker: `FREE_RIDERS` lists the free ones (`{ key, name, portrait }`, a square image), `saveRider(key)`
keeps this browser's pick, `riderName(key)` names any key, `riderKey(value)` turns anything unknown into `'moki'`.
`?as=moki#1234` on the page's address tries a wallet Moki. Your own `MeshStandardMaterial`s can wear the characters'
look: `toonifyTree(object)` (tune it with `TOON_UNIFORMS`).

Our characters' files come from the platform's asset catalog, at `/assets/...` on the game's own address: served
to every game, never copied into one, so don't download them into your folder. The kit fetches each one with your
invite key the first time a game asks for it and keeps it in `~/.pupkins`, so the next game, and the next run
offline, already have it. `npm run dev` says at start when there's no key (then the characters can't load). A wallet
Moki's traits come from `/api/mokis` the same way; without them it plays as the free Moki.

### More moves: the actions pack

`loadAvatar(key, { clips: ['actions'] })` adds 25 clips to the avatar, the same for the Moki and Schiffy. Then
`me.play('Sit')`, `me.play('KO')` and so on:

| | |
|---|---|
| Resting | `Sit` and `Sleep` hold their pose until the player moves. `Idle2` and `Idle3` are other idles, looping |
| Feelings | `No`, `Angry`, `Alert`, `Tired`, `Worship` (bowing down to the floor) |
| Hits and falls | `Hurt` (a flinch), `KO` (falls on its face), `KOBack` (knocked flying backwards), `Faint` (topples over backwards). The three falls stay down until you play something else or call `setIdle()` |
| Fighting | `Attack`, `Swipe`, `Punch`, `Slam` (a jumping slam), `Throw`: the hit lands about halfway through. `Block` loops while you hold it. `Dash` is a lunge (move the root yourself) |
| Work and play | `Dig`, `Chop`, `Craft`, `Tinker` and `Swim` loop (for `Swim`, put the character in water up to its chest) |

`play(name, options)` returns the clip's length in seconds. While one plays, `busy` is how long it still runs
(`Infinity` for a looping or held one), and `setIdle()` ends it and goes back to standing. The options:

- `hold: true` stops on the clip's last frame and stays there. `Sit`, `Sleep` and the falls hold by default;
  `hold: false` plays them once.
- `reverse: true` plays it backwards, from its last frame to its first: after `play('Sit')`,
  `play('Sit', { reverse: true })` stands back up, and `play('KO', { reverse: true })` gets up off the floor.
- `loop: true` repeats it; `loops: 3` plays it three times. The work clips, `Swim`, `Block` and the idles loop by
  default.
- `interruptible: true` lets moving (`setSpeed` above a stroll) end it. `Sit` and `Sleep` are interruptible;
  the falls aren't, so a knocked-out player stays down until your game says.
- `full: true` is for a clip that moves the whole body, like lying down or falling over. Our characters' heads
  keep within a limit in other clips. `Sleep`, `Worship` and the falls already have it.
- `fade` is the cross-fade in, in seconds (default 0.15). `timeScale` plays it faster or slower.

`addClips(clips)` adds clips of your own made for our characters' rigs (a `Map` or an array of
`THREE.AnimationClip`s) and returns the names it added. Then `play(name)` plays them like ours. A clip's
`userData.play` (its glTF animation `extras.play`) can set its own defaults, e.g. `{ "hold": true }`.

### Animations of your own

A move our clips don't have (a backflip, a dance, a sword swing, a victory pose) you can make yourself, once for the
Moki and Schiffy both. Write a clip as a short script of poses; the kit poses it on both characters (there's nothing
else to install), turns it into your game's clips files, says what it made and draws a preview of each to look at.
With Blender you can also pose a clip by hand, in its window.

```bash
pupkins-create anim new Backflip    # anims/Backflip.js, a clip to start from (--loop, --hold)
npm run anim                        # (pupkins-create anim build) every clip in anims/ into client/anims/moki.glb and
                                    # schiffy.glb, a report, and a preview of each in .pupkins/anim/
pupkins-create anim preview         # the previews again (name clips to draw only those)
pupkins-create anim open Wave2      # a .blend to pose by hand in Blender's window (--rig moki|schiffy, --loop, --hold)
```

The game loads them with the character and plays them like ours:

```js
const me = await loadAvatar(key, { clips: ['./anims/{rig}.glb'] });   // {rig}: moki (any Moki) or schiffy
me.play('Backflip');                                                   // returns its length in seconds
```

`./anims/{rig}.glb` is the page's address for `client/anims/<rig>.glb`: those files are your game's own, so keep
them with it. `anims/` holds what they're made from (the clip scripts and any .blend files). `npm run check` warns
when one of those is newer than the clips files. With other packs in `clips`, a name two of them have plays the one
listed first.

A clip, `anims/Backflip.js`:

```js
import { clip } from '@pupkins/create/anim';

clip('Backflip', { seconds: 1.1 })
  .pose(0)                                                                         // standing, as in the game
  .pose(0.15, { upper_leg: [-60, 0, 0], lower_leg: [90, 0, 0], upper_arm: [0, 0, -40], ground: true })   // crouch
  .pose(0.35, { body: [-90, 0, 0], move: [0, 0.7, 0], upper_arm: [0, 0, -160], ease: 'linear' })
  .pose(0.55, { body: [-180, 0, 0], move: [0, 0.9, 0], upper_leg: [-80, 0, 0], lower_leg: [110, 0, 0], ease: 'linear' })
  .pose(0.75, { body: [-270, 0, 0], move: [0, 0.6, 0], ease: 'linear' })
  .pose(0.9, { body: [-360, 0, 0], upper_leg: [-50, 0, 0], lower_leg: [80, 0, 0], ground: true })      // landing
  .pose(1.1, { body: [-360, 0, 0] });
```

`clip(name, { seconds, fps, loop, hold, interruptible, full })` begins one clip. A script can make several, with loops
and functions of its own, and import helpers from `anims/` (a file whose name starts with `_`, like `_moves.js`, isn't
a clip script). Its name is how the game plays it: letters, digits, `_` and `-`, and not one of the characters' own
(`Idle`, `Walk`, `Run` and the six emotes). `seconds` is its length, by default its last pose's time, and `fps` is 30.
`loop`, `hold` and `interruptible` are how `play(name)` plays it unless the game says otherwise (the options above).
`full`, on unless you say `full: false`, lets it move the whole body.

`.pose(seconds, { ...parts, body, move, ground, ease })` adds the whole pose at that moment and returns the clip, so
poses chain. A part left out stands as in the game's standing pose, so `.pose(1)` is back to standing. Each part is
`[bend, turn, tilt]` in degrees, turned at its joint about the character's own axes, on top of what it hangs from:

| | turns the part about | + is |
|---|---|---|
| `bend` | the character's left-right axis | the part's top going forward: the head nods, the spine bows. A part that hangs down swings the other way: + sends a hanging arm's hand back (-90: straight ahead) and a leg's foot back |
| `turn` | its up axis | the part's front turning to the character's left (the head looks left) |
| `tilt` | its front-back axis | the part's top going to the character's left. A hanging arm's hand goes to the right, so `upper_arm_l: [0, 0, -80]` raises the left arm out to the side |

The parts are named the same on both characters: `spine`, `head`, `tail`, `tail_2` and `tail_3` (the tail's
root, middle and tip), and in pairs `shoulder`, `upper_arm`, `lower_arm`, `hand`, `upper_leg`, `lower_leg`,
`foot` and `ear`, with `_l` (the character's own left) or `_r`. A pair's name without `_l` or `_r` poses both
sides as mirror images: `upper_arm: [0, 0, -80]` raises both arms out to the sides. The Moki also has `leaf`, and
Schiffy has `chest`, `neck` and `jaw`. On the other character those are skipped, and the report says so.

- `body: [bend, turn, tilt]` turns the whole character about its hips: `body: [-90, 0, 0]` lies it on its back,
  `body: [0, 180, 0]` turns it round.
- `move: [left, up, forward]` moves it, in its own heights: `move: [0, 0.5, 0]` lifts it half its height (a jump).
  When the clip ends the character is back where your game has it, so for a move that travels (a dash, a roll)
  move the character in your game as the clip plays.
- `ground: true` sets that pose down on the floor: its lowest point (the tail left out) touches it, whatever
  `move`'s up says. Use it for crouching, sitting, lying down and landing: our characters are different heights and
  builds, and the same turns leave them at different heights.
- `ease` is how the move into that pose goes: `'smooth'` (the default, a smooth curve through the poses that slows
  where a part turns back), `'linear'` (a steady speed: spins and flips) or `'step'` (it holds the pose before, then
  snaps to this one: a robot's moves).
- Between two poses a part turns the short way round, so a flip or a spin needs a pose at least every 90 degrees,
  as above. A loop writes them: `const spin = clip('Spin', { loop: true }).pose(0);` then `for (let k = 1; k <= 4;
  k++) spin.pose(k * 0.15, { body: [0, 90 * k, 0], ease: 'linear' });`. A pose every 0.1 to 0.3 seconds reads well.
- A mistake stops the script with its line: a part that isn't one, angles that aren't three numbers, a pose before 0.

Poses to start from: a nod `head: [20, 0, 0]`; looking up `head: [-25, 0, 0]`; looking left `head: [0, 40, 0]`; a bow
`spine: [35, 0, 0]`; arms up in a V `upper_arm: [0, 0, -100]`; arms out `upper_arm: [0, 0, -80]`; arms straight ahead
`upper_arm: [-90, 0, 0]`; the tail up `tail: [40, 0, 0]`; a crouch `upper_leg: [-60, 0, 0], lower_leg: [80, 0, 0],
ground: true`; sitting on the floor `upper_leg: [-85, 0, 0], lower_leg: [85, 0, 0], ground: true`; lying on its back
`body: [-90, 0, 0], tail: [-90, 0, 0], ground: true` (the tail laid along the floor). The characters stand
differently, so the same turns can look a little different on each: the previews show both.

`npm run anim` lists each clip with its length and notes anything to fix on either character: a pose that goes under
the floor, a tail through the floor, a held last pose off the floor, a looping clip whose last pose isn't its first
(it jumps each time it loops). A script that fails costs only its own clips, and the error names its line. Then it
saves `.pupkins/anim/<Name>.png` for each clip: the clip on the Moki and Schiffy at six moments, from the front and
from the side, played by the game's own avatar engine. Open them (your file-reading tool shows PNGs) and fix what
looks wrong: they're how you see a clip.

By hand, in Blender (4.2 or newer: free, from blender.org; only this needs it): `pupkins-create anim open Wave2`
makes `anims/Wave2.moki.blend` (`--rig schiffy` for Schiffy), with the character standing as in the game and an
action called `Wave2`, and opens it in Blender. Pose the bones, key them, save, and `npm run anim`. Each action in the
file is a clip, named as the game plays it (Blender keeps an action only while something uses it, so give each its
fake user, the shield). `--loop`, `--hold` and `--interruptible` set its play defaults (the action's custom
properties of those names). A clip made by hand on one character plays on the other too: the build carries it over
part by part, and sets it as far off the floor.

`anim` needs our characters' rigs from the asset catalog (signed in, as `npm run dev` does) and Chrome
for the previews. It finds
Blender on the PATH or where Blender installs (`PUPKINS_BLENDER` names another); `pupkins-create anim` on its own says
which Blender it found, or that it found none.

## Props: our games' things (`loadProp`)

Every 3D thing our own games are built from is a **prop** a game may use: barrels, crates, lanterns, fences, trees,
rocks, market stalls, cottages, bridges, a treehouse, the moon stadium, a basketball hoop, gold, a skate park, shapes
for effects, and whole places (a village, an island, a backyard) to start a level in. Over 300 of them, from more
than 20 of our games' sets. Each has an id (`village-barrel`, `garden-gnome`, `camp-kiln-hut`, `moon-stadium`), a
kind (`prop`: a thing to place; `set`: a building, a stage, a backdrop; `world`: a whole place; `fx`: a shape for
effects, to tint, fade and spin), a size in metres and a picture.

```bash
pupkins-create library                 # the props library in the browser: search, filter, turn any one in 3D, download it
pupkins-create props lantern           # the props matching every word (in the id, name, set or tags), with size and triangles
pupkins-create props --kind world      # by kind (prop, set, world, fx) or --collection <set>; --json for the full list
pupkins-create props tree --pictures   # and each one's picture, in .pupkins/props/<id>.webp, to look at
```

While `npm run dev` runs, the library is at `/library` on the game's address too, and the scene editor opens it to
pick a prop. Nothing downloads up front: the list is small, the pictures load as you scroll, and a prop's file loads
the first time a game or the library asks for it (signed in, as our characters do) and is kept in
`~/.pupkins`. Props are served to every game from the platform's asset catalog, never copied into one, so a game
doesn't carry them. Many props are cut from one file (the village's barrels, crates, carts and stalls are one file):
it loads once for all of them, and the library says what each file weighs and how many props share it.

```js
import { loadProp, listProps } from '@pupkins/create/avatars';

const barrel = await loadProp('village-barrel');            // a THREE.Group, standing on y = 0, centred on x and z
barrel.position.set(2, 0, -3);
scene.add(barrel);
const gnome = await loadProp('garden-gnome', { height: 0.5 });   // sized to 0.5 m tall ({ scale: 2 } scales it instead)
const yard = await loadProp('backyard');                    // a world keeps its own origin: it's where its game had it
const crystals = (await listProps()).filter((p) => p.tags.includes('crystals'));   // the list: id, name, collection, kind, tags, size, tris, bytes, thumb
```

`loadProp` gives a new copy each time (the file's meshes and textures are shared), so place as many as you like;
recolour a copy by cloning its materials first. Props come in our toon look when the scene's `toon` is on; a page of
your own can give them it with `toonifyTree(prop)`. In a scene file a prop is `{ "type": "prop", "prop":
"village-barrel" }` (the editor's Add menu has it, with a button that opens the library to pick one), and a
`scatter` scatters props too: `"item": { "type": "prop", "prop": "garden-mushroom" }`.

The library's **Download .glb** saves one prop as a file of its own, to look at or change in Blender. A game that
uses a prop as it is should load it with `loadProp` rather than carry the file: the catalog serves it, and it stays
the same as in our games.

## Scenes and the scene editor (`@pupkins/create/scene`)

A **scene** is a place in the game laid out as data: a 3d level (ground, walls, trees, lights, the sky, the sun, the
game's camera) or a 2d board (a court, a card table, a HUD). Each one is a file, `scenes/<name>.scene.json`, which the
page loads and the **scene editor** opens. Every starter is laid out in one (`scenes/plaza.scene.json`,
`scenes/court.scene.json`, ...).

```bash
npm run edit                     # the dev server with the scene editor open (pupkins-create edit): /edit on its address
pupkins-create scene list        # the game's scenes
pupkins-create scene new level   # a new 3d scene (--2d for a 2d one)
pupkins-create scene remove old  # a scene taken away (it says if the page still loads it)
pupkins-create scene sync        # the logic files the scenes feed the rules, made again (the editor does it on save)
```

The editor, in the browser at `/edit` while `npm run dev` runs: a list of the scene's objects on the left (drag to
reorder or put one inside another), the view in the middle, the selected object's fields on the right. In 3d, orbit
with the left mouse button, pan with the right, zoom with the wheel; W E R move, turn and size the selected object
with the gizmo; C looks through the game's camera; F frames the selection. In 2d, drag objects, their yellow corner
to size them and the blue dot to turn them. Ctrl+S saves (the game's page reloads with it), Ctrl+Z / Ctrl+Y undo
and redo, Ctrl+D duplicates, Ctrl+C / Ctrl+V copy and paste (into another scene too), ? lists the keys. Only this
machine can change files through it (`share` and published games have no editor), and a scene file changed on
disk while it's open (Claude edited it) opens as it is now, or, with changes unsaved, saving asks which to keep.

### Loading a scene in the page

```js
import * as THREE from 'three';
import { loadScene } from '@pupkins/create/scene';

const renderer = new THREE.WebGLRenderer({ antialias: true });
const world = await loadScene('/scenes/plaza.scene.json', { renderer });   // sets the renderer up as the scene says
world.scene;                    // a THREE.Scene: the sky, the fog, the sun, the fill light and every object
world.camera;                   // the scene's game camera (camera.userData.target: where it looks)
world.get('fountain');          // an object by its id (a THREE.Object3D: move it, hide it, recolour it)
world.all('coin');              // every object with the tag "coin"
world.place('spawn');           // where an object is in the whole scene, in metres: { x, y, z, yaw, ...its size }
const gem = world.spawn('gem'); // a new copy of the prefab "gem", for the game to add and move: scene.add(gem)
world.sunAt(x, z);              // the sun follows a spot (shadows stay sharp where the player is), at its own angle
world.update(dt);               // every frame: characters standing in the scene animate
await world.ready();            // models, characters and the fill light loaded
```

A 2d scene draws on a canvas: `const board = await loadScene('/scenes/court.scene.json')`, then each frame
`board.draw(ctx)` (it fills the canvas, keeping the scene's shape; `board.fit(w, h)` is where it lands). The game
moves its objects by changing them: `board.get('ball').x = 300` (2d objects are the scene's own data),
`board.drawPrefab(ctx, 'card', x, y)` draws a prefab anywhere, `board.draw(ctx, null, { hidden })` leaves out the ids
in a `Set`, and `board.place(id)` and `board.tagged(tag)` work as in 3d.

### What a scene holds

Positions are metres in 3d (x to the right, y up, z toward the camera; rotations in degrees, yaw 0 facing +z) and the
scene's own units in 2d (`size`, by default 1600 x 900, y down). An object has an `id` (the game finds it by it), a
`name`, a `type`, its place (`position` / `rotation` / `scale`, or `x` / `y` / `rotation` / `scale` / `alpha` in 2d),
`visible`, `tags` and `children`, and its type's fields:

| 3d | |
|---|---|
| `box` `sphere` `cylinder` `cone` `capsule` `torus` `poly` | Shapes (`poly`: a rock or crystal: `tetra`, `octa`, `dodeca`, `icosa`), each with a `material` |
| `plane` `circle` `ring` | Flat on the ground |
| `prop` | One of our props (`prop`: its id, as `pupkins-create props` and the library list them), standing where it's placed |
| `model` | A `.glb` / `.gltf` of the game's own (`file`, from the game's folder) |
| `character` | One of our characters standing there (`rider`: `moki`, `schiffy`; `clip`: a clip it plays) |
| `light` | `point`, `spot` or `directional`, with a `color`, `intensity`, `distance` |
| `label` | Words that always face the camera |
| `marker` | A named spot or area (`radius`) the game uses: not drawn in the game |
| `group` | Holds others |
| `prefab` | A placement of one of the scene's `prefabs` (edit the prefab and every placement changes) |
| `scatter` | Many copies of a prefab or a shape over an area (trees, rocks, clouds), the same every time (`seed`) |

| 2d | |
|---|---|
| `rect` `circle` `line` `text` | Shapes, with `fill`, `stroke`, `lineWidth`, `dash` |
| `image` | A picture of the game's own (`file`) |
| `marker` `group` `prefab` | As in 3d |

A 3d material is the name of one of the scene's `materials` (shared: change it once) or one of the object's own:
`color`, `roughness`, `metalness`, `emissive`, `opacity`, `unlit`, `double`, `flat`, and a `texture`: a picture of the
game's own, or one the page draws (`paving`, `grass`, `lawn`, `planks`, `bricks`, `stone`, `sand`, `checker`,
`tiles`, tinted by the colour) with its `repeat`. A cylinder's material can be three: its side, top and bottom. The
scene's `environment` is its sky (one to three colours), fog, sun (`azimuth` and `elevation` in degrees, shadows),
sky light and `toon` (our characters' look on everything, on by default); its `camera` is the game camera.

### Places the rules use: logic names

The rules can't load a scene (they run in the room too, with whole numbers only), but a scene can hand them places:
give an object a **logic name** (the inspector's *Logic name*), and the scene's logic file (`"logic": { "file":
"logic/scene.js" }`) lists every object with that name, where it is in the whole scene and its size, as whole
numbers: millimetres in 3d (`units`: 1000 to a metre), the scene's units times `units` in 2d. Angles are 16-bit turns
(65536 a full turn, as `fixed.TURN`).

```js
// logic/game.js
import { SCENE } from './scene.js';
export const PLAZA = SCENE.plaza[0].r;          // the radius of the object named "plaza", in millimetres
const spawns = SCENE.spawn.map(({ x, z }) => ({ x, z }));   // every marker named "spawn", in the scene's order
```

The editor writes the logic file on each save and the dev server when a scene file changes; `pupkins-create scene sync`
writes it after hand edits, and `check` fails when it's out of step with its scene. Don't edit it: edit the scene.
Each scene writes its own logic file: two scenes naming the same one are a problem of both (neither is written) until
one has its own or is removed. Replacing a starter's scene with your own? `pupkins-create scene remove` the old one.

## The manifest (`pupkins.game.json`)

```json
{ "id": "my-game", "name": "My Game", "version": "0.1.0", "sdk": "0.1",
  "entry": "client/index.html", "logic": "logic/game.js",
  "multiplayer": { "mode": "rollback", "delay": 2, "minPlayers": 1, "quickmatch": true } }
```

`id` is the game's address on the platform: 2-32 lowercase letters and digits, with single dashes between them
(`check` says when it isn't). `mode` is `"rollback"`, `"lockstep"`, `"turns"` or `"presence"`, the same as the logic's (`check` says when they
differ); `delay` (input delay, in ticks) is for rollback games (a lockstep game's rooms pick their own), and a world
needs nothing else.

`minPlayers` is how many players a room needs to start: set it to `seats` if your game has no CPU (a rollback game's
`input.cpu`, a lockstep game's way of playing a null seat, a turns game's `bot`).
