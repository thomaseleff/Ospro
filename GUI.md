# OSPRO GUI Layout Spec (ASCII Wireframes)

This document is the canonical layout contract for developers and coding agents implementing the GUI.

See @./THEME.md for the visual design language.

## 1. Layout Contract

- Target viewport: `1024px x 600px` (width x height, landscape).
- Layout intent: touch-first kiosk UI.
- Screen composition: `Header`, `Content`, `Action Row`, `Status Footer`.
- All interactive controls have stable IDs (for implementation + review comments).
- Disabled controls are shown with `(dis)` in wireframes.

## 2. Global Conventions

- Buttons: `[ Label ]`
- Select/dropdown: `[ value v ]`
- Input field: `[ value________ ]`
- Slider: `[----o-------]`
- Metric emphasis: uppercase label + larger rendering in implementation
- Modal overlays block interaction with base screen until dismissed

## 3. Navigation Map

- `HOME` -> `DASHBOARD`
- `HOME` -> `SETTINGS`
- `DASHBOARD` -> `PLOT`
- `SETTINGS` -> `PROFILE_EDITOR`
- `PLOT` -> `ADD_PROFILE_MODAL`
- `SETTINGS` -> `ERROR/WARN/CONFIRM` modals
- `PROFILE_EDITOR` -> `WARN` modal (overwrite)

## 4. Screen Index

- `S1` Home
- `S2` Dashboard (Idle)
- `S3` Dashboard (Extracting)
- `S4` Dashboard (Stopped/Ready)
- `S5` Plot
- `S6` Settings
- `S7` Profile Editor
- `M1` Input Profile Name
- `M2` Error
- `M3` Overwrite Warning
- `M4` Delete Confirmation

---

## S1 - Home (`root` / mainFrame)

```text
+----------------------------------------------------------+
|                                             [H01 Close]  |
|                                                          |
|                +----------------------------+            |
|                |            LOGO            |            |
|                +----------------------------+            |
|                         OSPRO                            |
|            Better than decent, open-source espresso.     |
|                                                          |
|                                                          |
|      [H02 Power(dis)] [H03 Dashboard] [H04 Settings]     |
|                                                          |
| Temp[F/C]: 201   Pressure[Bars]: 8.7   Profile: Manual   |
+----------------------------------------------------------+
```

Notes:
- `H02 Power` remains disabled unless machine power control is implemented.

## S2 - Dashboard (Idle)

```text
+----------------------------------------------------------+
| [D01 Back]                                  [D02 Close]  |
| [D03 Flush(dis)]                                         |
|                                                          |
| TIMER                                                    |
| +----------------------------+   Temperature[F/C]: 201   |
| |            0.0             |                           |
| |                            |   Pressure[Bars]:   8.8   |
| +----------------------------+                           |
|                                                          |
| [D04 Start] [D05 Stop(dis)] [D06 Plot(dis)] [D07 Settings]|
| [D08 Save(dis)] [D09 Reset(dis)]                         |
|                                                          |
| Set-Point: 201   Flush[Sec]: 3   Profile: Manual         |
+----------------------------------------------------------+
```

## S3 - Dashboard (Extracting)

```text
+----------------------------------------------------------+
| [D01 Back(dis)]                             [D02 Close]  |
| [D03 Flush(dis)]                                         |
|                                                          |
| TIMER RUNNING                                            |
| +----------------------------+   Temperature[F/C]: 202   |
| |           12.4             |                           |
| |                            |   Pressure[Bars]:   9.1   |
| +----------------------------+                           |
|                                                          |
| [D04 Start(dis)] [D05 Stop] [D06 Plot(dis)]              |
| [D07 Settings(dis)] [D08 Save(dis)] [D09 Reset]          |
|                                                          |
| Set-Point: 201   Flush[Sec]: 3   Profile: Manual         |
+----------------------------------------------------------+
```

Behavior:
- If active profile is not `Manual`, `D05 Stop` is disabled and stop is automatic at profile end.

## S4 - Dashboard (Stopped / Ready to Save)

```text
+----------------------------------------------------------+
| [D01 Back(dis)]                             [D02 Close]  |
| [D03 Flush(dis)]                                         |
|                                                          |
| TIMER STOPPED (counter flashes)                          |
| +----------------------------+   Temperature[F/C]: 201   |
| |           27.9             |                           |
| |                            |   Pressure[Bars]:   0.0   |
| +----------------------------+                           |
|                                                          |
| [D04 Start] [D05 Stop(dis)] [D06 Plot]                   |
| [D07 Settings(dis)] [D08 Save] [D09 Reset]               |
|                                                          |
| Set-Point: 201   Flush[Sec]: 3   Profile: Manual         |
+----------------------------------------------------------+
```

## S5 - Plot (`create_plot`)

```text
+----------------------------------------------------------+
| [P01 Back]   Espresso Extraction Performance [P02 Close] |
|                    Correl[%]: 94.12                      |
|                                                          |
| +------------------------------------------------------+ |
| |                  TEMP/PRESSURE PLOT                  | |
| | Temp: solid + set-point dashed                       | |
| | Pres: solid + profile dashed (if non-manual)         | |
| +------------------------------------------------------+ |
|                      Time [Sec.]                         |
|                                                          |
| Duration: 27.9 Sec   Profile: Classic9bar                |
|                                        [P03 Add Profile] |
+----------------------------------------------------------+
```

## S6 - Settings (`create_settings`)

```text
+----------------------------------------------------------+
| [S01 Back/Save]                            [S02 Close]   |
|                                                          |
| Temperature [F/C]                                        |
|   Scale:      [S03 Fahrenheit [F] v]                     |
|   Set-Point:  [S04 201 v]                                |
|                                                          |
| Pressure Profile                                         |
|   Profile: [S05 Manual v] [S06 Delete] [S07 Edit]        |
|            [S08 New]                                     |
|                                                          |
| Flush [Sec.]                                             |
|   Duration:   [S09 3 v]                                  |
|                                                          |
| [S10 Refresh]                                            |
+----------------------------------------------------------+
```

Notes:
- `S01 Back/Save` persists config before closing.
- `Manual` profile cannot be deleted or edited.

## S7 - Pressure Profile Editor (`create_profile`)

```text
+----------------------------------------------------------+
| [E01 Back]                                 [E02 Close]   |
|                                                          |
| +------------------------------------------------------+ |
| |               PRESSURE PROFILE PREVIEW               | |
| | pressure/time line + control points                  | |
| +------------------------------------------------------+ |
|                                                          |
| Profile Name:              [E03 Custom_1___________]     |
| Extraction Duration [Sec]: [E04 -----o-----------]       |
| Pre-Infusion Duration:     [E05 0 v]                     |
| Pre-Infusion Pressure:     [E06 3 v]                     |
| P0: [E07 ----o-----]  P1: [E08 ----o-----]               |
| P2: [E09 ----o-----]  P3: [E10 ----o-----]               |
| P4: [E11 ----o-----]                                     |
| Params: 25.0s, Pre-Inf 3s@3bar                           |
|         {P0:9,P1:9,P2:9,P3:9,P4:9}                       |
|                                           [E12 Save]     |
+----------------------------------------------------------+
```

---

## M1 - Modal: Input Profile Name

```text
+--------------------------------------------+
| Input Profile Name                         |
|                                            |
| Profile Name:                              |
| [M101 User_1___________________________]   |
|                                            |
| [M102 Back]                   [M103 Save]  |
+--------------------------------------------+
```

## M2 - Modal: Error

```text
+--------------------------------------------+
| Error                                      |
|                                            |
| Error: <message>                           |
|                                            |
|                            [M201 Okay]     |
+--------------------------------------------+
```

## M3 - Modal: Overwrite Warning

```text
+--------------------------------------------+
| Warning                                    |
|                                            |
| [ProfileName] already exists.              |
| Do you want to overwrite it?               |
|                                            |
| [M301 No]                     [M302 Yes]   |
+--------------------------------------------+
```

## M4 - Modal: Delete Confirmation

```text
+--------------------------------------------+
| Confirmation                               |
|                                            |
| Delete profile [ProfileName]?              |
|                                            |
| [M401 No]                     [M402 Yes]   |
+--------------------------------------------+
```

---

## 5. Stateful Behavior Contract

- Dashboard states are mutually exclusive: `idle`, `extracting`, `stopped`.
- `extracting` disables navigation/settings actions that could corrupt sampling.
- `stopped` enables `Plot`, `Save`, `Reset`.
- Non-manual profile extraction ends automatically at profile duration.
- Modals are blocking and must restore focus to invoking control on close.

## 6. Review / Feedback Format

When proposing changes, reference:

- Screen ID and control ID (example: `S6.S05`)
- Viewport: `1024x600`
- Scenario/state (example: `S3 extracting with non-manual profile`)
- Expected vs actual layout behavior
