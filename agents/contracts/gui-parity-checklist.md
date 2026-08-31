# GUI Parity Checklist

## Screen Coverage

- [ ] S1 Home
- [ ] S2 Dashboard Idle
- [ ] S3 Dashboard Extracting (Manual)
- [ ] S3 Dashboard Extracting (Non-manual)
- [ ] S4 Dashboard Stopped
- [ ] S5 Plot (Manual)
- [ ] S5 Plot (Non-manual)
- [ ] S6 Settings
- [ ] S7 Profile Editor

## Modal Coverage

- [ ] M1 Input Profile Name
- [ ] M2 Error
- [ ] M3 Overwrite Warning
- [ ] M4 Delete Confirmation

## Behavior Coverage

- [ ] Dashboard availability matrix matches `agents/contracts/ui-state-machine.md`
- [ ] Manual profile restrictions enforced
- [ ] Modal blocking and focus restore verified
- [ ] Settings/Profile persistence rules match `agents/contracts/persistence-contract.md`

## Visual/Theming Coverage

- [ ] Screenshots captured at `1024x600`
- [ ] Layout/control order matches `GUI.md`
- [ ] Semantic colors and states match `THEME.md`

## PR Evidence

- [ ] Artifact paths listed
- [ ] Expected vs actual deviations documented
- [ ] Estimated vs actual line count documented
