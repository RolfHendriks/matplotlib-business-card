# svgtomaplotlib
# Implements a custom solution for loading svg file contents into a matplotlib Path

import svgpathtools as svg
from matplotlib.path import Path
import re

def svg_path_to_matplotlib_path(svg_path: svg.Path) -> Path:
    # Creates a list of path commands in SVG's path language.
    # This method seems to defeat the purpose of using a 3rd party utility - why not just parse the raw SVG path into a matplotlib path?
    # Because the 3rd party library normalizes the format of the svg path, reducing it to only a small fraction of the total complexity of parsing an svg path.
    commands = svg_path.d()
    commands = re.split('([A-Z])', commands)[1:]
    vertices = []
    codes = []
    for command, args in zip(commands[::2], commands[1::2]):
        #print(command, args)
        points = [x for x in args.split(' ') if x != '']
        points = [point_str.split(',') for point_str in points]
        points = [(float(p[0]), float(p[1])) for p in points]
        path_command = ''
        if command == 'M':
            path_command = Path.MOVETO
        elif command == 'L':
            path_command = Path.LINETO
        elif command == 'C':
            path_command = Path.CURVE4
        elif command == 'Q':
            path_command = Path.CURVE3
        else:
            raise ValueError(f'Unrecognized path command: {command}') 
        vertices.extend(points)
        codes.extend([path_command] * len(points))
    return Path(vertices, codes)

def read_svg(file: str, invert_y = True, height = None):
    """
    Opens an svg file and returns a Path matplotlib representation for output in a plot and underlying csv file metadata.

    Parameters:
        - invert_y: if true, flip y coordinates of the underlying svg for matplotlib, converting from screen space (y origin at top) to figure space (y origin at bottom). if false, graphics will appear upside-down when attaching them to a plot.
        - height: if set, scale the resulting path to fit a specified height
    Returns:
        Path: a matplotlib path that can be added to a plot using PathPatch to display the svg
    """

    # A note on path transformation:
    # It would have been more desirable to use PathPatch's built-in transformations to flip and scale svg graphics and return a PathPath instead of Path.
    # However, doing this correctly is unexpectedly nontrivial because it involves coordinating with Axes transformations.
    # So, we transform the underlying svg data manually instead of using PathPatch transforms.
    def transform_vertices(transform: lambda x,y: (x,y), path: Path) -> Path:
        vertices = [transform(vertex[0], vertex[1]) for vertex in path.vertices.copy()]
        return Path(vertices, path.codes)

    paths, _, svg_attributes = svg.svg2paths(file, return_svg_attributes = True)
    paths = [svg_path_to_matplotlib_path(path) for path in paths]
    viewBox = [int(x) for x in svg_attributes['viewBox'].split(' ')]
    svg_attributes['viewBox'] = viewBox
    width = viewBox[2] - viewBox[0]

    # turn image 'upside down' to convert from svg/screen coordinates (where y axis begins at the top) to matplotlib/math coordinates (where y is from the bottom).
    img_height = viewBox[3] - viewBox[1]
    if invert_y:
        paths = [transform_vertices(lambda x, y: (x, img_height - y), path) for path in paths]
    # rescale if needed
    if height != None:
        scale = height / img_height
        paths = [transform_vertices(lambda x, y: (x * scale, y * scale), path) for path in paths]
        width *= scale
    else:
        height = img_height
    svg_attributes["size"] = (width, height)
    if len(paths) == 1:
        return paths[0], svg_attributes
    else:
        print('Warning: this svg contains multiple paths. This case has not been tested.')
        return paths, svg_attributes  
