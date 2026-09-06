"""Validate and normalize simple SVG input. No renderer code is included."""
import math
import re
import xml.etree.ElementTree as ET

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
TOKEN = re.compile(rf"{NUMBER}|[a-zA-Z]")
ARITY = {"M":2,"L":2,"H":1,"V":1,"C":6,"S":4,"Q":4,"T":2,"A":7}
SVG_NS = "http://www.w3.org/2000/svg"

def fail(message):
    raise ValueError(message)


def validate_path(data):
    """Check SVG path grammar without splitting compound holes into filled paths."""
    if TOKEN.sub("", data).strip(" ,\t\r\n"):
        fail("Path contains unsupported characters.")
    tokens = TOKEN.findall(data)
    if not tokens:
        fail("Empty path.")
    index, command, opened = 0, None, False
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
            if command.upper() == "Z":
                if not opened:
                    fail("Close-path without an open contour.")
                opened, command = False, None
                continue
            if command.upper() not in ARITY:
                fail(f"Unsupported path command: {command}")
            if index >= len(tokens) or tokens[index].isalpha():
                fail(f"Missing coordinates for {command}.")
        if command is None:
            fail("Coordinates require a path command.")
        size = ARITY[command.upper()]
        group = tokens[index:index + size]
        if len(group) != size or any(t.isalpha() for t in group):
            fail(f"Incomplete coordinates for {command}.")
        values = [float(t) for t in group]
        if any(not math.isfinite(n) or abs(n) > 1e7 for n in values):
            fail("Coordinates must be finite and within +/- 10,000,000.")
        if command.upper() == "M":
            if opened:
                fail("Close each filled contour with Z before the next M.")
            opened = True
            command = "l" if command == "m" else "L"
        elif not opened:
            fail("Each contour must begin with M.")
        if command.upper() == "A":
            if values[0] < 0 or values[1] < 0 or values[3] not in (0, 1) or values[4] not in (0, 1):
                fail("Arc radii must be nonnegative; arc flags must be 0 or 1.")
        index += size
    if opened:
        fail("Filled paths must explicitly close with Z.")
    return " ".join(tokens)


def parse_svg(raw):
    if len(raw) > 256_000:
        fail("This simple-SVG workflow accepts files up to 256 KB.")
    if re.search(br"<!\s*(?:DOCTYPE|ENTITY)", raw, re.I):
        fail("DOCTYPE and entities are not supported.")
    root = ET.fromstring(raw)

    def tag_name(element):
        tag = element.tag
        if tag.startswith("{"):
            namespace, tag = tag[1:].split("}", 1)
            if namespace != SVG_NS:
                fail("Foreign XML namespaces are not supported.")
        return tag

    if tag_name(root) != "svg":
        fail("Input root must be SVG.")
    box = root.get("viewBox", "")
    if re.fullmatch(rf"\s*{NUMBER}(?:[\s,]+{NUMBER}){{3}}\s*", box) is None:
        fail("Provide an explicit four-number viewBox.")
    bounds = [float(n) for n in re.findall(NUMBER, box)]
    if any(not math.isfinite(n) or abs(n) > 1e7 for n in bounds) or min(bounds[2:]) <= 0:
        fail("viewBox needs finite values and positive width/height.")
    paths, rules = [], []
    paints = set()

    def visit(element, inherited_fill="black", inherited_rule="nonzero"):
        tag = tag_name(element)
        if tag in ("title", "desc"):
            if list(element) or set(element.attrib) - {"id"}:
                fail("Metadata must contain plain text only, without active attributes or children.")
            return
        if tag not in ("svg", "g", "path") or (tag == "svg" and element is not root):
            fail(f"Unsupported <{tag}>. Convert basic shapes/text/strokes to closed paths first.")
        allowed = {"id", "fill", "fill-rule", "aria-label", "role"}
        allowed |= {"viewBox", "width", "height", "version"} if tag == "svg" else set()
        allowed |= {"d"} if tag == "path" else set()
        unexpected = set(element.attrib) - allowed
        if unexpected:
            fail(f"Unsupported {tag} attributes: {', '.join(sorted(unexpected))}. Flatten transforms/styles/strokes first.")
        paint = element.get("fill", inherited_fill).strip().lower()
        rule = element.get("fill-rule", inherited_rule)
        if rule not in ("nonzero", "evenodd"):
            fail("fill-rule must be nonzero or evenodd.")
        if not re.fullmatch(r"#[0-9a-f]{3}(?:[0-9a-f]{3})?|[a-z]+|rgba?\([\d\s.,%]+\)", paint):
            fail("Use an explicit solid fill; gradients and referenced paint are unsupported.")
        if paint in {"none", "transparent", "inherit", "currentcolor", "context-fill", "context-stroke"}:
            fail("Every path must have an explicit or inherited solid fill.")
        if tag == "path":
            if list(element):
                fail("Nested path children are unsupported.")
            paths.append(validate_path(element.get("d", "")))
            rules.append(rule)
            paints.add(paint)
        else:
            for child in element:
                visit(child, paint, rule)

    visit(root)
    if not paths or len(paths) > 32:
        fail("Provide 1 to 32 substantial closed paths.")
    if len(paints) != 1:
        fail("Use a monochrome SVG. White overlays do not create holes; use compound contours.")
    view_box = " ".join(format(n, ".12g") for n in bounds)
    normalized = ET.Element("svg", {"xmlns": SVG_NS, "viewBox": view_box,
                                     "width": format(bounds[2], ".12g"),
                                     "height": format(bounds[3], ".12g"), "fill": "#ffffff"})
    for path, rule in zip(paths, rules):
        ET.SubElement(normalized, "path", {"d": path, "fill-rule": rule})
    ET.indent(normalized, space="  ")
    return {"width": bounds[2], "height": bounds[3], "viewBox": view_box,
            "paths": paths, "fillRules": rules}, ET.tostring(normalized, encoding="utf-8") + b"\n"
