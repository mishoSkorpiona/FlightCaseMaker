bl_info = {
    "name": "Flight Case Maker",
    "author": "GitHub Copilot",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Flight Case",
    "description": "Parametric generator for standard rectangular flight cases",
    "category": "Object",
}

import csv
from dataclasses import dataclass
from pathlib import Path

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Operator, Panel, PropertyGroup


ADDON_COLLECTION_NAME = "FlightCaseMaker"
DIMENSION_TEXT_NAME = "FCM_Dimension_Sheet"


CASE_PRESETS = {
    "SMALL": {
        "label": "Small Utility",
        "external_width": 400.0,
        "external_depth": 300.0,
        "external_height": 250.0,
        "lid_height": 80.0,
        "material_thickness": 9.0,
        "hardware_set": "LIGHT",
    },
    "MEDIUM": {
        "label": "Medium AV",
        "external_width": 600.0,
        "external_depth": 400.0,
        "external_height": 450.0,
        "lid_height": 120.0,
        "material_thickness": 9.0,
        "hardware_set": "STANDARD",
    },
    "LARGE": {
        "label": "Large Touring",
        "external_width": 900.0,
        "external_depth": 600.0,
        "external_height": 700.0,
        "lid_height": 180.0,
        "material_thickness": 12.0,
        "hardware_set": "STANDARD",
    },
}


HARDWARE_PRESETS = {
    "LIGHT": {
        "label": "Light Duty",
        "handle_count": 2,
        "latch_count": 2,
        "hinge_count": 2,
        "wheel_count": 0,
        "corner_count": 8,
        "min_width": 300.0,
        "min_depth": 250.0,
        "min_height": 200.0,
    },
    "STANDARD": {
        "label": "Standard Touring",
        "handle_count": 2,
        "latch_count": 4,
        "hinge_count": 3,
        "wheel_count": 4,
        "corner_count": 8,
        "min_width": 450.0,
        "min_depth": 300.0,
        "min_height": 280.0,
    },
}


@dataclass
class PanelPart:
    name: str
    width: float
    depth: float
    height: float
    location: tuple[float, float, float]
    parent_name: str
    material: str
    quantity: int = 1


@dataclass
class HardwarePart:
    name: str
    size: tuple[float, float, float]
    location: tuple[float, float, float]
    parent_name: str
    category: str
    quantity: int = 1


def mm_to_units(value: float) -> float:
    return value / 1000.0


def get_dimensions(props):
    thickness = props.material_thickness
    if props.dimension_mode == "EXTERNAL":
        width = props.external_width
        depth = props.external_depth
        height = props.external_height
    else:
        width = props.internal_width + (2.0 * thickness)
        depth = props.internal_depth + (2.0 * thickness)
        height = props.internal_height + (2.0 * thickness)
    return width, depth, height, thickness


def build_case_data(props):
    width, depth, height, thickness = get_dimensions(props)
    lid_height = props.lid_height
    body_height = height - lid_height
    divider_thickness = max(thickness * 0.5, 6.0)
    internal_width = width - (2.0 * thickness)
    internal_depth = depth - (2.0 * thickness)
    internal_height = height - (2.0 * thickness)
    body_internal_height = body_height - thickness
    lid_internal_height = lid_height - thickness
    hardware = HARDWARE_PRESETS[props.hardware_set]
    exploded_offset = props.explode_distance if props.exploded_view else 0.0

    panels = [
        PanelPart(
            "Body Bottom",
            width,
            depth,
            thickness,
            (0.0, 0.0, thickness / 2.0),
            "Body",
            props.panel_material,
        ),
        PanelPart(
            "Body Front",
            width,
            thickness,
            body_height - thickness,
            (0.0, (depth - thickness) / 2.0, (body_height + thickness) / 2.0),
            "Body",
            props.panel_material,
        ),
        PanelPart(
            "Body Back",
            width,
            thickness,
            body_height - thickness,
            (0.0, -(depth - thickness) / 2.0, (body_height + thickness) / 2.0),
            "Body",
            props.panel_material,
        ),
        PanelPart(
            "Body Left",
            thickness,
            depth - (2.0 * thickness),
            body_height - thickness,
            (-(width - thickness) / 2.0, 0.0, (body_height + thickness) / 2.0),
            "Body",
            props.panel_material,
        ),
        PanelPart(
            "Body Right",
            thickness,
            depth - (2.0 * thickness),
            body_height - thickness,
            ((width - thickness) / 2.0, 0.0, (body_height + thickness) / 2.0),
            "Body",
            props.panel_material,
        ),
        PanelPart(
            "Lid Top",
            width,
            depth,
            thickness,
            (0.0, 0.0, height - (thickness / 2.0) + exploded_offset),
            "Lid",
            props.panel_material,
        ),
        PanelPart(
            "Lid Front",
            width,
            thickness,
            lid_height - thickness,
            (
                0.0,
                (depth - thickness) / 2.0,
                body_height + (lid_height / 2.0) + exploded_offset,
            ),
            "Lid",
            props.panel_material,
        ),
        PanelPart(
            "Lid Back",
            width,
            thickness,
            lid_height - thickness,
            (
                0.0,
                -(depth - thickness) / 2.0,
                body_height + (lid_height / 2.0) + exploded_offset,
            ),
            "Lid",
            props.panel_material,
        ),
        PanelPart(
            "Lid Left",
            thickness,
            depth - (2.0 * thickness),
            lid_height - thickness,
            (
                -(width - thickness) / 2.0,
                0.0,
                body_height + (lid_height / 2.0) + exploded_offset,
            ),
            "Lid",
            props.panel_material,
        ),
        PanelPart(
            "Lid Right",
            thickness,
            depth - (2.0 * thickness),
            lid_height - thickness,
            (
                (width - thickness) / 2.0,
                0.0,
                body_height + (lid_height / 2.0) + exploded_offset,
            ),
            "Lid",
            props.panel_material,
        ),
    ]

    internal_parts = []
    if props.enable_foam:
        foam_height = min(props.foam_height, max(body_internal_height - 10.0, 10.0))
        internal_parts.append(
            PanelPart(
                "Foam Insert",
                max(internal_width - 4.0, 10.0),
                max(internal_depth - 4.0, 10.0),
                foam_height,
                (0.0, 0.0, thickness + (foam_height / 2.0)),
                "Body",
                "Foam",
            )
        )

    if props.width_dividers > 0:
        spacing = internal_width / (props.width_dividers + 1)
        for index in range(props.width_dividers):
            x_pos = -(internal_width / 2.0) + ((index + 1) * spacing)
            internal_parts.append(
                PanelPart(
                    f"Width Divider {index + 1}",
                    divider_thickness,
                    internal_depth,
                    max(body_internal_height, 10.0),
                    (x_pos, 0.0, thickness + (body_internal_height / 2.0)),
                    "Body",
                    props.panel_material,
                )
            )

    if props.depth_dividers > 0:
        spacing = internal_depth / (props.depth_dividers + 1)
        for index in range(props.depth_dividers):
            y_pos = -(internal_depth / 2.0) + ((index + 1) * spacing)
            internal_parts.append(
                PanelPart(
                    f"Depth Divider {index + 1}",
                    internal_width,
                    divider_thickness,
                    max(body_internal_height, 10.0),
                    (0.0, y_pos, thickness + (body_internal_height / 2.0)),
                    "Body",
                    props.panel_material,
                )
            )

    hardware_parts = []
    handle_size = (30.0, 120.0, 90.0)
    latch_size = (80.0, 25.0, 120.0)
    hinge_size = (70.0, 20.0, 40.0)
    corner_size = (30.0, 30.0, 30.0)
    wheel_size = (60.0, 60.0, 80.0)

    if hardware["handle_count"] == 2:
        handle_z = max(min(body_height * 0.45, body_height - 45.0), 50.0)
        for side, x_pos in (("Left", -(width / 2.0) - 15.0), ("Right", (width / 2.0) + 15.0)):
            hardware_parts.append(
                HardwarePart(
                    f"{side} Handle",
                    handle_size,
                    (x_pos, 0.0, handle_z),
                    "Body",
                    "Handle",
                )
            )

    latch_count = hardware["latch_count"]
    latch_positions = evenly_spaced_positions(latch_count, width * 0.7)
    for index, x_pos in enumerate(latch_positions, start=1):
        hardware_parts.append(
            HardwarePart(
                f"Latch {index}",
                latch_size,
                (x_pos, (depth / 2.0) + 12.0, body_height - 18.0),
                "Body",
                "Latch",
            )
        )

    hinge_count = hardware["hinge_count"]
    hinge_positions = evenly_spaced_positions(hinge_count, width * 0.6)
    for index, x_pos in enumerate(hinge_positions, start=1):
        hardware_parts.append(
            HardwarePart(
                f"Hinge {index}",
                hinge_size,
                (x_pos, -(depth / 2.0) - 10.0, body_height + exploded_offset + 5.0),
                "Lid",
                "Hinge",
            )
        )

    corner_locations = [
        (-(width / 2.0), -(depth / 2.0), 0.0, "Body"),
        (-(width / 2.0), (depth / 2.0), 0.0, "Body"),
        ((width / 2.0), -(depth / 2.0), 0.0, "Body"),
        ((width / 2.0), (depth / 2.0), 0.0, "Body"),
        (-(width / 2.0), -(depth / 2.0), height + exploded_offset, "Lid"),
        (-(width / 2.0), (depth / 2.0), height + exploded_offset, "Lid"),
        ((width / 2.0), -(depth / 2.0), height + exploded_offset, "Lid"),
        ((width / 2.0), (depth / 2.0), height + exploded_offset, "Lid"),
    ]
    for index, (x_pos, y_pos, z_pos, parent_name) in enumerate(corner_locations[: hardware["corner_count"]], start=1):
        hardware_parts.append(
            HardwarePart(
                f"Corner {index}",
                corner_size,
                (x_pos, y_pos, z_pos),
                parent_name,
                "Corner",
            )
        )

    if hardware["wheel_count"] == 4:
        wheel_z = wheel_size[2] / 2.0
        wheel_x = (width / 2.0) - 50.0
        wheel_y = (depth / 2.0) - 50.0
        for index, (x_sign, y_sign) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)), start=1):
            hardware_parts.append(
                HardwarePart(
                    f"Wheel {index}",
                    wheel_size,
                    (wheel_x * x_sign, wheel_y * y_sign, wheel_z),
                    "Body",
                    "Wheel",
                )
            )

    return {
        "external_width": width,
        "external_depth": depth,
        "external_height": height,
        "internal_width": internal_width,
        "internal_depth": internal_depth,
        "internal_height": internal_height,
        "body_height": body_height,
        "lid_height": lid_height,
        "body_internal_height": body_internal_height,
        "lid_internal_height": lid_internal_height,
        "panels": panels,
        "internal_parts": internal_parts,
        "hardware_parts": hardware_parts,
        "divider_thickness": divider_thickness,
        "hardware": hardware,
    }


def evenly_spaced_positions(count: int, span: float):
    if count <= 0:
        return []
    if count == 1:
        return [0.0]
    step = span / (count - 1)
    start = -(span / 2.0)
    return [start + (step * index) for index in range(count)]


def build_validation_messages(props):
    data = build_case_data(props)
    messages = []
    width = data["external_width"]
    depth = data["external_depth"]
    height = data["external_height"]
    thickness = props.material_thickness
    lid_height = props.lid_height
    body_height = data["body_height"]
    hardware = data["hardware"]

    if min(width, depth, height) <= 0.0:
        messages.append("All dimensions must be greater than zero.")
    if thickness < 4.0:
        messages.append("Material thickness below 4 mm is unlikely to be suitable for a flight case.")
    if width <= (2.0 * thickness) or depth <= (2.0 * thickness) or height <= (2.0 * thickness):
        messages.append("Wall thickness is too large for the selected dimensions.")
    if lid_height <= thickness:
        messages.append("Lid height must be greater than the panel thickness.")
    if body_height <= thickness:
        messages.append("Body height must be greater than the panel thickness.")
    if props.dimension_mode == "INTERNAL" and min(
        props.internal_width, props.internal_depth, props.internal_height
    ) <= 0.0:
        messages.append("Internal dimensions must be greater than zero.")
    if width < hardware["min_width"] or depth < hardware["min_depth"] or height < hardware["min_height"]:
        messages.append(f"{hardware['label']} hardware set is too large for the selected case dimensions.")
    if props.width_dividers > 0:
        clear_width = data["internal_width"] / (props.width_dividers + 1)
        if clear_width < 80.0:
            messages.append("Width divider count leaves less than 80 mm clear width per compartment.")
    if props.depth_dividers > 0:
        clear_depth = data["internal_depth"] / (props.depth_dividers + 1)
        if clear_depth < 80.0:
            messages.append("Depth divider count leaves less than 80 mm clear depth per compartment.")
    if props.enable_foam and props.foam_height >= data["body_internal_height"]:
        messages.append("Foam height must stay below the usable body interior height.")
    if props.panel_material == "6 mm Plywood" and props.hardware_set == "STANDARD":
        messages.append("Standard hardware with 6 mm plywood may need reinforcement plates.")
    if lid_height > (height * 0.5):
        messages.append("Lid height above 50% of total case height may reduce body usability.")
    return messages


def create_box_mesh_object(name, size, location, collection, parent=None):
    sx, sy, sz = [mm_to_units(max(value, 1.0)) for value in size]
    lx, ly, lz = [mm_to_units(value) for value in location]
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    vertices = [
        (-hx, -hy, -hz),
        (hx, -hy, -hz),
        (hx, hy, -hz),
        (-hx, hy, -hz),
        (-hx, -hy, hz),
        (hx, -hy, hz),
        (hx, hy, hz),
        (-hx, hy, hz),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new(name=f"{name} Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (lx, ly, lz)
    collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def get_or_create_collection(scene):
    collection = bpy.data.collections.get(ADDON_COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(ADDON_COLLECTION_NAME)
        scene.collection.children.link(collection)
    elif collection.name not in {child.name for child in scene.collection.children}:
        scene.collection.children.link(collection)
    return collection


def clear_collection_objects(collection):
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def rebuild_case(context):
    if context is None or context.scene is None:
        return
    props = context.scene.flight_case_maker
    collection = get_or_create_collection(context.scene)
    clear_collection_objects(collection)

    body_parent = bpy.data.objects.new("Body", None)
    lid_parent = bpy.data.objects.new("Lid", None)
    collection.objects.link(body_parent)
    collection.objects.link(lid_parent)

    data = build_case_data(props)
    parents = {"Body": body_parent, "Lid": lid_parent}

    for panel in data["panels"]:
        create_box_mesh_object(
            panel.name,
            (panel.width, panel.depth, panel.height),
            panel.location,
            collection,
            parent=parents[panel.parent_name],
        )

    for part in data["internal_parts"]:
        create_box_mesh_object(
            part.name,
            (part.width, part.depth, part.height),
            part.location,
            collection,
            parent=parents[part.parent_name],
        )

    for hardware in data["hardware_parts"]:
        create_box_mesh_object(
            hardware.name,
            hardware.size,
            hardware.location,
            collection,
            parent=parents[hardware.parent_name],
        )

    props.last_validation = "\n".join(build_validation_messages(props)) or "No validation warnings."


def update_case(self, context):
    if context is not None and getattr(self, "auto_update", False):
        rebuild_case(context)


class FlightCaseMakerProperties(PropertyGroup):
    dimension_mode: EnumProperty(
        name="Dimension Mode",
        items=[
            ("EXTERNAL", "External", "Drive the case from external dimensions"),
            ("INTERNAL", "Internal", "Drive the case from internal usable dimensions"),
        ],
        default="EXTERNAL",
        update=update_case,
    )
    preset: EnumProperty(
        name="Preset",
        items=[(key, value["label"], value["label"]) for key, value in CASE_PRESETS.items()],
        default="MEDIUM",
    )
    external_width: FloatProperty(name="External Width (mm)", default=600.0, min=50.0, update=update_case)
    external_depth: FloatProperty(name="External Depth (mm)", default=400.0, min=50.0, update=update_case)
    external_height: FloatProperty(name="External Height (mm)", default=450.0, min=50.0, update=update_case)
    internal_width: FloatProperty(name="Internal Width (mm)", default=582.0, min=10.0, update=update_case)
    internal_depth: FloatProperty(name="Internal Depth (mm)", default=382.0, min=10.0, update=update_case)
    internal_height: FloatProperty(name="Internal Height (mm)", default=432.0, min=10.0, update=update_case)
    lid_height: FloatProperty(name="Lid Height (mm)", default=120.0, min=20.0, update=update_case)
    material_thickness: FloatProperty(name="Material Thickness (mm)", default=9.0, min=4.0, update=update_case)
    panel_material: EnumProperty(
        name="Panel Material",
        items=[
            ("6 mm Plywood", "6 mm Plywood", ""),
            ("9 mm Plywood", "9 mm Plywood", ""),
            ("12 mm Plywood", "12 mm Plywood", ""),
            ("Composite Panel", "Composite Panel", ""),
        ],
        default="9 mm Plywood",
        update=update_case,
    )
    hardware_set: EnumProperty(
        name="Hardware Set",
        items=[(key, value["label"], value["label"]) for key, value in HARDWARE_PRESETS.items()],
        default="STANDARD",
        update=update_case,
    )
    width_dividers: IntProperty(name="Width Dividers", default=0, min=0, max=10, update=update_case)
    depth_dividers: IntProperty(name="Depth Dividers", default=0, min=0, max=10, update=update_case)
    enable_foam: BoolProperty(name="Foam Insert", default=False, update=update_case)
    foam_height: FloatProperty(name="Foam Height (mm)", default=60.0, min=10.0, update=update_case)
    exploded_view: BoolProperty(name="Exploded View", default=False, update=update_case)
    explode_distance: FloatProperty(name="Explode Distance (mm)", default=120.0, min=0.0, update=update_case)
    auto_update: BoolProperty(name="Auto Update", default=True)
    export_directory: StringProperty(
        name="Export Directory",
        default="//",
        subtype="DIR_PATH",
    )
    export_basename: StringProperty(
        name="Export Basename",
        default="flight_case",
    )
    last_validation: StringProperty(name="Validation", default="Generate a case to validate.")


class FCM_OT_apply_preset(Operator):
    bl_idname = "flight_case.apply_preset"
    bl_label = "Apply Preset"
    bl_description = "Apply the selected flight case preset"

    def execute(self, context):
        props = context.scene.flight_case_maker
        preset = CASE_PRESETS[props.preset]
        props.external_width = preset["external_width"]
        props.external_depth = preset["external_depth"]
        props.external_height = preset["external_height"]
        props.lid_height = preset["lid_height"]
        props.material_thickness = preset["material_thickness"]
        props.hardware_set = preset["hardware_set"]
        props.panel_material = f"{int(preset['material_thickness'])} mm Plywood"
        rebuild_case(context)
        return {"FINISHED"}


class FCM_OT_generate_case(Operator):
    bl_idname = "flight_case.generate_case"
    bl_label = "Generate / Update Case"
    bl_description = "Build the flight case model from the current parameters"

    def execute(self, context):
        rebuild_case(context)
        return {"FINISHED"}


class FCM_OT_export_reports(Operator):
    bl_idname = "flight_case.export_reports"
    bl_label = "Export CSV Reports"
    bl_description = "Export BOM, cut list, and dimension sheet as CSV and text files"

    def execute(self, context):
        props = context.scene.flight_case_maker
        data = build_case_data(props)
        export_dir = Path(bpy.path.abspath(props.export_directory))
        export_dir.mkdir(parents=True, exist_ok=True)
        base_name = props.export_basename.strip() or "flight_case"

        cut_list_path = export_dir / f"{base_name}_cut_list.csv"
        hardware_path = export_dir / f"{base_name}_hardware.csv"
        dimensions_path = export_dir / f"{base_name}_dimensions.txt"

        with cut_list_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Part", "Width (mm)", "Depth (mm)", "Height (mm)", "Material", "Parent"])
            for part in data["panels"] + data["internal_parts"]:
                writer.writerow([part.name, part.width, part.depth, part.height, part.material, part.parent_name])

        with hardware_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Item", "Category", "Size X (mm)", "Size Y (mm)", "Size Z (mm)", "Parent"])
            for item in data["hardware_parts"]:
                writer.writerow([item.name, item.category, *item.size, item.parent_name])

        dimensions_path.write_text(build_dimension_sheet(props, data), encoding="utf-8")
        self.report({"INFO"}, f"Reports exported to {export_dir}")
        return {"FINISHED"}


class FCM_OT_generate_dimension_sheet(Operator):
    bl_idname = "flight_case.generate_dimension_sheet"
    bl_label = "Generate Dimension Sheet"
    bl_description = "Create a Blender text block with panel sizes, BOM, and warnings"

    def execute(self, context):
        props = context.scene.flight_case_maker
        data = build_case_data(props)
        text_block = bpy.data.texts.get(DIMENSION_TEXT_NAME)
        if text_block is None:
            text_block = bpy.data.texts.new(DIMENSION_TEXT_NAME)
        else:
            text_block.clear()
        text_block.write(build_dimension_sheet(props, data))
        self.report({"INFO"}, f"Updated {DIMENSION_TEXT_NAME}")
        return {"FINISHED"}


def build_dimension_sheet(props, data):
    lines = [
        "Flight Case Maker - Dimension Sheet",
        "",
        f"Dimension Mode: {props.dimension_mode}",
        f"External Size (mm): {data['external_width']} x {data['external_depth']} x {data['external_height']}",
        f"Internal Size (mm): {data['internal_width']} x {data['internal_depth']} x {data['internal_height']}",
        f"Body Height / Lid Height (mm): {data['body_height']} / {data['lid_height']}",
        f"Panel Material: {props.panel_material}",
        f"Hardware Set: {HARDWARE_PRESETS[props.hardware_set]['label']}",
        "",
        "Cut List",
        "--------",
    ]
    for part in data["panels"] + data["internal_parts"]:
        lines.append(
            f"- {part.name}: {part.width:.1f} x {part.depth:.1f} x {part.height:.1f} mm ({part.material})"
        )

    lines.extend(["", "Hardware", "--------"])
    for item in data["hardware_parts"]:
        lines.append(
            f"- {item.name}: {item.category} at ({item.location[0]:.1f}, {item.location[1]:.1f}, {item.location[2]:.1f}) mm"
        )

    lines.extend(["", "Validation", "----------"])
    warnings = build_validation_messages(props)
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No validation warnings.")
    return "\n".join(lines) + "\n"


class FCM_PT_presets(Panel):
    bl_label = "Preset Management"
    bl_idname = "FCM_PT_presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Flight Case"

    def draw(self, context):
        props = context.scene.flight_case_maker
        layout = self.layout
        layout.prop(props, "preset")
        layout.operator("flight_case.apply_preset")


class FCM_PT_case_parameters(Panel):
    bl_label = "Case Parameters"
    bl_idname = "FCM_PT_case_parameters"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Flight Case"

    def draw(self, context):
        props = context.scene.flight_case_maker
        layout = self.layout
        layout.prop(props, "dimension_mode")
        if props.dimension_mode == "EXTERNAL":
            layout.prop(props, "external_width")
            layout.prop(props, "external_depth")
            layout.prop(props, "external_height")
        else:
            layout.prop(props, "internal_width")
            layout.prop(props, "internal_depth")
            layout.prop(props, "internal_height")
        layout.prop(props, "lid_height")
        layout.prop(props, "material_thickness")
        layout.prop(props, "panel_material")
        layout.prop(props, "auto_update")


class FCM_PT_hardware_layout(Panel):
    bl_label = "Hardware & Layout"
    bl_idname = "FCM_PT_hardware_layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Flight Case"

    def draw(self, context):
        props = context.scene.flight_case_maker
        layout = self.layout
        layout.prop(props, "hardware_set")
        layout.separator()
        layout.prop(props, "width_dividers")
        layout.prop(props, "depth_dividers")
        layout.prop(props, "enable_foam")
        if props.enable_foam:
            layout.prop(props, "foam_height")
        layout.separator()
        layout.prop(props, "exploded_view")
        if props.exploded_view:
            layout.prop(props, "explode_distance")


class FCM_PT_generate(Panel):
    bl_label = "Generate"
    bl_idname = "FCM_PT_generate"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Flight Case"

    def draw(self, context):
        layout = self.layout
        layout.operator("flight_case.generate_case", icon="MOD_BUILD")
        layout.operator("flight_case.generate_dimension_sheet", icon="TEXT")


class FCM_PT_output(Panel):
    bl_label = "Output & Export"
    bl_idname = "FCM_PT_output"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Flight Case"

    def draw(self, context):
        props = context.scene.flight_case_maker
        layout = self.layout
        layout.prop(props, "export_directory")
        layout.prop(props, "export_basename")
        layout.operator("flight_case.export_reports", icon="EXPORT")


class FCM_PT_validation(Panel):
    bl_label = "Validation"
    bl_idname = "FCM_PT_validation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Flight Case"

    def draw(self, context):
        props = context.scene.flight_case_maker
        layout = self.layout
        warnings = props.last_validation.splitlines() if props.last_validation else []
        for warning in warnings:
            icon = "ERROR" if warning != "No validation warnings." else "CHECKMARK"
            layout.label(text=warning, icon=icon)


classes = (
    FlightCaseMakerProperties,
    FCM_OT_apply_preset,
    FCM_OT_generate_case,
    FCM_OT_export_reports,
    FCM_OT_generate_dimension_sheet,
    FCM_PT_presets,
    FCM_PT_case_parameters,
    FCM_PT_hardware_layout,
    FCM_PT_generate,
    FCM_PT_output,
    FCM_PT_validation,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.flight_case_maker = PointerProperty(type=FlightCaseMakerProperties)


def unregister():
    del bpy.types.Scene.flight_case_maker
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
