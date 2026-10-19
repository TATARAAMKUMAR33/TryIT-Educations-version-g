import re
import xml.etree.ElementTree as ET

ALLOWED_TAGS = {"svg", "polygon", "polyline", "circle", "ellipse", "rect", "line", "text", "tspan"}
ALLOWED_ATTRS = {
    "svg": {"viewbox", "width", "height"},
    "polygon": {"points", "fill", "stroke", "stroke-width", "stroke-dasharray"},
    "polyline": {"points", "fill", "stroke", "stroke-width", "stroke-dasharray"},
    "circle": {"cx", "cy", "r", "fill", "stroke", "stroke-width", "stroke-dasharray"},
    "ellipse": {"cx", "cy", "rx", "ry", "fill", "stroke", "stroke-width"},
    "rect": {"x", "y", "width", "height", "rx", "ry", "fill", "stroke", "stroke-width"},
    "line": {"x1", "y1", "x2", "y2", "stroke", "stroke-width", "stroke-dasharray"},
    "text": {"x", "y", "fill", "font-size", "text-anchor"},
    "tspan": {"x", "y", "fill", "font-size"},
}
_NUM = r"-?\d+(\.\d+)?"
_NUMERIC_RE = re.compile(rf"^\s*{_NUM}\s*$")
_POINTS_RE = re.compile(rf"^(\s*{_NUM}\s*,\s*{_NUM}\s*)+$")
_VIEWBOX_RE = re.compile(rf"^\s*{_NUM}(\s+{_NUM}){{3}}\s*$")
_DASHARRAY_RE = re.compile(rf"^\s*{_NUM}(\s*,\s*{_NUM})*\s*$")
_COLOR_RE = re.compile(r"^(none|[a-zA-Z]{2,20}|#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6})$")
_ANCHOR_RE = re.compile(r"^(start|middle|end)$")
_VALUE_VALIDATORS = {
    "viewbox": _VIEWBOX_RE, "width": _NUMERIC_RE, "height": _NUMERIC_RE, "points": _POINTS_RE,
    "cx": _NUMERIC_RE, "cy": _NUMERIC_RE, "r": _NUMERIC_RE, "rx": _NUMERIC_RE, "ry": _NUMERIC_RE,
    "x": _NUMERIC_RE, "y": _NUMERIC_RE, "x1": _NUMERIC_RE, "y1": _NUMERIC_RE, "x2": _NUMERIC_RE, "y2": _NUMERIC_RE,
    "stroke-width": _NUMERIC_RE, "stroke-dasharray": _DASHARRAY_RE, "font-size": _NUMERIC_RE,
    "fill": _COLOR_RE, "stroke": _COLOR_RE, "text-anchor": _ANCHOR_RE,
}
def _local_tag(elem_tag: str) -> str:
    return elem_tag.split("}")[-1].lower()
def _clean_element(elem):
    tag = _local_tag(elem.tag)
    if tag not in ALLOWED_TAGS: return None
    cleaned = ET.Element(tag)
    for attr_name, attr_value in elem.attrib.items():
        local_name = _local_tag(attr_name)
        if local_name not in ALLOWED_ATTRS.get(tag, set()): continue
        validator = _VALUE_VALIDATORS.get(local_name)
        if validator and not validator.match(attr_value.strip()): continue
        cleaned.set(local_name, attr_value.strip())
    if tag in ("text", "tspan") and elem.text:
        cleaned.text = re.sub(r"[<>]", "", elem.text)[:200]
    for child in elem:
        cleaned_child = _clean_element(child)
        if cleaned_child is not None: cleaned.append(cleaned_child)
    return cleaned
def sanitize_svg(svg_string: str) -> str:
    if not svg_string or "<svg" not in svg_string: return ""
    try: root = ET.fromstring(svg_string)
    except ET.ParseError: return ""
    if _local_tag(root.tag) != "svg": return ""
    cleaned_root = _clean_element(root)
    if cleaned_root is None or len(cleaned_root) == 0: return ""
    return ET.tostring(cleaned_root, encoding="unicode")
def sanitize_question_svgs(question: dict, diagram_kind: str) -> dict:
    if diagram_kind == "geometry_svg" and question.get("diagram_svg"):
        question["diagram_svg"] = sanitize_svg(question["diagram_svg"])
    elif diagram_kind == "nonverbal_mirror_svg":
        if question.get("original_svg"): question["original_svg"] = sanitize_svg(question["original_svg"])
        if isinstance(question.get("option_svgs"), list): question["option_svgs"] = [sanitize_svg(s) for s in question["option_svgs"]]
    return question
