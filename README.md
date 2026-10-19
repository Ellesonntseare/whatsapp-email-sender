# Crownfall: Cannon Rush

A self-contained 3D arcade game. Aim the cannon, grow your crew through upgrade gates, and bring down five fortresses before time runs out.

Open [index.html](index.html) in a modern browser to play. Drag or use the left and right arrow keys to steer. The dotted aim guide predicts moving gates, and the selected gate glows.

Soldiers run with moving arms, legs, shields, and capes. The cannon recoils, rolls its wheels when steered, and flashes when firing. Impacts send out sparks and expanding rings; damaged fortresses crack, shed battlements, and collapse on victory.

| Stage | Challenge |
| --- | --- |
| Harbor Approach | Learn gate choices and build your crew. |
| Crosswinds | Time moving gates, choose a route, and avoid defenders' warning lanes. |
| The Citadel | Combine moving gates, stronger defenses, and route bonuses. |
| Splitwater Crossing | Follow split paths through moving gates and a sweeping hazard. |
| The Iron Crown | Attack the teal, exposed side of the boss castle and dodge its barrages. |

On split paths, troops lock onto the route they enter. Guard troops deal **2 damage** to the fortress; raid troops deal **3 damage** and face more danger. The aim badge shows the route your next shot will enter. These bonuses stay with troops created at later gates.

The Iron Crown alternates its exposed side. Its red shield blocks damage on the other side. At half health it becomes enraged, switches sides faster, and attacks two lanes at once. Red strips warn before shots arrive. Finish a level to unlock the next one; losing lets you retry that level.

Each stage has its own scenery, with three procedural music themes. The castle towers, doorway, pennants, and ballistae come from [Kenney's Castle Kit](https://kenney.nl/assets/castle-kit), licensed CC0. Selected source models and the license are in [`assets/models`](assets/models). The playable HTML bundles the models and their texture so it can be opened directly.

The game includes Three.js and its GLTFLoader under the MIT license. The Three.js copyright and license notice are preserved in `index.html`.
