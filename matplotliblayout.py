# matplotlib-layout.py
# Utilities for inspecting the layout of matplotlib plots
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.artist import Artist
from matplotlib.text import Text
from matplotlib.transforms import Bbox
import matplotlib.patheffects as path_effects
from matplotlib.patches import Rectangle
#from matplotlib.figure import Figure

def add_outline(artist: mpl.artist.Artist, color = 'k', linewidth = 1):
    """
    Adds an outline stroke to an Artist. The intended use case is for creating high-contrast white text with black outlines.
    """
    artist.set_path_effects([
        path_effects.Stroke(linewidth=linewidth, foreground=color),
        path_effects.Normal()
    ])

################
# Debug Inspection
################
def describe_artist(artist: mpl.artist.Artist, coords = 'pixels') -> str:
    """
    Describes an Artist and its position and size within a figure.
    """
    bounds = artist.get_window_extent()
    artist_type = str(type(artist)).split('.')[-1][:-2]
    # Special case: for Text objects, also emit the underlying text
    if isinstance(artist, Text):
        artist_type += f":'{artist.get_text()}'"
    if coords != 'pixels':
        f = artist.figure
        if coords == 'inches':
            bounds = Bbox.from_bounds(*[x / f.dpi for x in bounds.bounds]) 
        elif coords == 'points':
            bounds = Bbox.from_bounds(*[72 * x / f.dpi for x in bounds.bounds])
        elif coords == 'fraction':
            w, h = f.get_figwidth() * f.dpi, f.get_figheight() * f.dpi
            figbounds = list(bounds.bounds)
            figbounds[0] /= w
            figbounds[1] /= h
            figbounds[2] /= w
            figbounds[3] /= h            
            bounds = Bbox.from_bounds(*figbounds) 
        else:
            raise ValueError('coords must be one of: pixels | inches | points | fraction')

    if coords in (['pixels', 'points']):
        bounds_str = f'xy = ({round(bounds.x0)}, {round(bounds.y0)}), width = {round(bounds.width)}, height = {round(bounds.height)}'
    else:
        bounds_str = f'xy = ({bounds.x0:.3g}, {bounds.y0:.3g}), width = {bounds.width:.3g}, height = {bounds.height:.3g}'
    return f'{artist_type}({bounds_str})'

# Artist hierarchy inspection - debug logging
def traverse_layout(artist: mpl.artist.Artist, handler = lambda artist, depth, index: None, depth = 0, index = 0):
    """
    Base layout inspection method that iterates through the Artist hierarchy and emits a callback on each Artist.
    """
    handler(artist, depth, index)
    for index, child in enumerate(artist.get_children()):
        traverse_layout(child, handler, depth = depth + 1, index = index)

def print_layout(artist: mpl.artist.Artist, coords = 'pixels'):
    """
    Layout inspection utility that debug-prints an artist hierarchy to the console
    """
    def handle_artist(artist, depth, index):
        artist_description = describe_artist(artist, coords = coords)
        print('| ' * depth + f'{index+1}. ' + artist_description)
    traverse_layout(artist, handle_artist)

# Artist Hierarchy Inspection - Visual
def add_debug_box(
    box: Bbox, 
    fig: mpl.figure.Figure,
    **style,
    #facecolor = 'none', edgecolor = ('k', 0.5), linestyle = '--', linewidth = 1
    #style = { 'edgecolor': ('k', 0.5), 'linestyle': '--', 'linewidth': 1, 'facecolor': 'none' }
):
    if style == {}:
        style = { 'edgecolor': ('k', 0.5), 'linestyle': '--', 'linewidth': 1, 'facecolor': 'none' }
    rect = Rectangle((box.x0, box.y0), box.width, box.height, **style)
    #rect.set_facecolor(facecolor)
    #rect.set_edgecolor(edgecolor)
    #rect.set_linewidth(linewidth)
    #rect.set_linestyle(linestyle)
    fig.add_artist(rect)

def show_layout(
    artist: mpl.artist.Artist, 
    depth = 0,
    renderer = None, # Used to compute bounding boxes
    handler = lambda artist: { 'edgecolor': ('k', 0.5), 'linestyle': '--', 'linewidth': 1, 'facecolor': 'none' }
):
    """
    Layout inspection utility that adds outlines to chart elements to reveal underlying layout details.
    """
    def handle_artist(artist, depth, index):
        #facecolor = style.get('facecolor')
        #edgecolor = style.get('edgecolor')
        #linewidth = style.get('linewidth')
        #linestyle = style.get('linestyle')
        bbox = artist.get_window_extent(renderer)
        style = handler(artist)
        add_debug_box(
            bbox,
            artist.get_figure(),
            **style
        )
        # if hasattr(artist, 'set_bbox'):
        #     artist.set_bbox(style)
        # if hasattr(artist, 'set_facecolor') and facecolor:
        #     if not artist.get_facecolor():
        #         artist.set_facecolor(facecolor)
        # if hasattr(artist, 'set_edgecolor') and edgecolor:
        #     if not artist.get_edgecolor():
        #         artist.set_edgecolor(edgecolor)
        #         if linestyle:
        #             artist.set_linestyle(linestyle)
        #         if linewidth:
        #             artist.set_linewidth(linewidth)
    traverse_layout(artist, handle_artist)