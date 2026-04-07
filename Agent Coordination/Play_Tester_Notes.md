# Play Tester Notes

## Unresolved Issues

### Issue Convention
- Type: bug, design issue, polish, or telemetry request
- Priority: blocker, major, medium, low
- Reproduction: how to trigger it
- Expected: what should happen 
- Seen by Planner: Has the planning agent reviewed/triaged this note?

### GUI
- Type: design issue
- Priority: major
- Reproduction: Start Game (also select a tower site)
- Expected: All buttons and status text should be stationary regardless of what text needs to be displayed. There should be enough room to keep all buttons on the screen. Similar buttons should be grouped and labels as short as possible (ie. Group 'Build' buttons under one label and only give name of tower on each button, similar with upgrades). Tower buttons can have symbol rather than text to distinguish them. Multiple columns of buttons is ideal.
- Seen by Planner: Yes - approved as an active UI/layout priority for the current phase; Designer should translate this into a more stable grouped control-panel spec without expanding scope

- Type: design issue
- Priority: minor
- Reproduction: Start Game
- Expected: Grid should not extend byond the row/column of the playable area and/or the tower sites. This is not the case on the right side of the map.
- Seen by Planner: No

- Type: design issue
- Priority: major
- Reproduction: Start Game
- Expected: All buttons should be visible by player on different screen sizes. Currently buttons are visible on large screens, but not small (laptop) screens
- Seen by Planner: No

### Gameplay

- Type: design issue
- Priority: medium
- Reproduction: Start game
- Expected: Player does not have enough opportunity to harvest coins. There is no way to replenish green lines if they are all harvested. Suggestion: Have a anti-enemy that acts just like the enemies that seed corrupted lines who seeds green lines
- Seen by Planner: Yes - reviewed and deferred as a scope-expanding future concept; not approved for the current tuning phase

- Type: design issue
- Priority: medium
- Reproduction: Start game, then build some towers
- Expected: Orbs should be visibly reducing the amount of corruption in a predictable (if not controlable) way by the player.
- Seen by Planner: Yes - approved as an active readability priority; preserve stochastic orb behavior, but make the corruption-reduction cause-and-effect read more clearly in live play

### Economy
- None

### Enemies
- None

### Towers

- Type: design issue
- Priority: medium
- Reproduction: Build seed tower
- Expected: Seeding orb should travel only along gridlines
- Seen by Planner: Yes - reviewed and deferred unless it becomes a clear active readability blocker; not part of the current power-tower tuning batch

- Type: design issue
- Priority: medium
- Reproduction: Build seed tower
- Expected: Seed orb and resulting orb should both be able to travel along medium gridlines
- Seen by Planner: Yes - reviewed and not approved for the current phase because it conflicts with the existing grid-access progression and needs a broader planner decision

### Visuals
- What is the status of the visuals? Are there still a lot of open works in the pipeline?
- Seen by Planner: Yes - visuals remain an open workstream; readability-focused temporary visuals are acceptable now, but final polish against `Style Example.jpg` is still pending
