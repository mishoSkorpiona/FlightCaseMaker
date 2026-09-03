# Flight Case Maker Blender Addon

This repository now includes a Blender addon for generating standard rectangular flight case designs with reusable presets, automatic hardware placement, divider/foam options, and production export reports.

## Addon location

- `/home/runner/work/FlightCaseMaker/FlightCaseMaker/flight_case_maker_addon/__init__.py`

## Current v1 scope

- Parametric rectangular flight case generator
- Separate body and removable lid generation
- External or internal dimension-driven workflow
- Material thickness-aware panel sizing
- Two starter hardware kits
- Divider and foam insert layout support
- Exploded preview mode
- CSV export for cut list and hardware list
- Text-based dimension sheet output inside Blender and to disk
- Validation warnings for common manufacturability issues

## Install in Blender

1. Open Blender.
2. Go to **Edit > Preferences > Add-ons**.
3. Choose **Install...**
4. Select the addon file from `/home/runner/work/FlightCaseMaker/FlightCaseMaker/flight_case_maker_addon/__init__.py`
5. Enable **Flight Case Maker**

## Use

1. Open the **3D Viewport**.
2. Open the **Sidebar** and go to the **Flight Case** tab.
3. Apply a preset or enter dimensions manually.
4. Select material, hardware set, dividers, foam, and exploded view options.
5. Click **Generate / Update Case**.
6. Use **Generate Dimension Sheet** for an in-Blender production summary.
7. Use **Export CSV Reports** to write cut list, hardware list, and dimension text files.

## Notes

- Geometry is intentionally box-oriented for repeatable workshop-friendly case design.
- Hardware is represented with simplified parametric placeholder geometry suitable for layout and planning.
- The addon is structured for future expansion toward richer hardware libraries, rack modules, and more advanced drawing/export formats.
