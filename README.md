# Crownfall: Cannon Rush

A self-contained 3D arcade campaign with **12 fortresses, 36 combat waves, and three boss battles**. Aim the cannon, grow your crew through upgrade gates, and break the Iron Crown.

Open [index.html](index.html) directly in a modern browser, or run `python3 start.py` to start a local server and open the game in your browser. On Windows, double-click `START-WINDOWS.bat`; on macOS or Linux, run `./start.sh`. Python 3 is required for the server. All game assets are bundled for offline play.

Drag or use the left and right arrow keys to steer. The dotted aim guide predicts moving gates, and the selected gate glows. Click **Pause**, or press **P** or **Escape**, to pause and resume. Switching away from the game automatically pauses combat.

Every fortress has three waves. Each wave rebuilds the defenders, resets your crew, and increases the fortress health. The second wave swaps selected gate choices; the third adds or speeds up moving gates and introduces extra ranged defenders. The stage timer runs during combat, with a short break between waves.

| Stage | Fortress |
| --- | --- |
| 1 | Harbor Approach |
| 2 | Crosswinds |
| 3 | The Citadel |
| 4 | Splitwater Crossing |
| 5 | Ember Bastion — boss |
| 6 | Moonlit Canal |
| 7 | Frostwatch |
| 8 | Stormkeep — boss |
| 9 | Sunken Ramparts |
| 10 | Cinder Reach |
| 11 | Royal Causeway |
| 12 | The Iron Crown — final boss |

Your browser automatically saves a checkpoint at each new wave. **Continue Campaign** resumes from that wave with a fresh timer; **New Campaign** starts over. Saved progress belongs to the browser and URL used to play. If browser storage is unavailable, the game still works for the current session.

On split paths, troops lock onto the route they enter. Guard troops deal **2 damage** to the fortress; raid troops deal **3 damage** and face more danger. Route bonuses stay with troops created at later gates. Bosses alternate their exposed side, block damage with the other shield, and enrage at half health. Red strips warn before attacks arrive.

Soldiers have animated limbs, shields, and capes. The cannon recoils and flashes; impacts send out sparks and expanding rings. Damaged fortresses crack, shed battlements, and collapse. Each environment has its own palette and scenery, with three procedural music themes.

Castle towers, doorways, pennants, and ballistae come from [Kenney's Castle Kit](https://kenney.nl/assets/castle-kit), licensed CC0. Selected source models and the license are in [`assets/models`](assets/models). The HTML bundles the models and their texture.

The game includes Three.js and its GLTFLoader under the MIT license. The Three.js copyright and license notice are preserved in `index.html`.
