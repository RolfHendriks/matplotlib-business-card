# Matplotlib Business Card

This project demonstrates how to lay out a business card using matplotlib:
![Business Card](/output/BusinessCard-300dpi.png)
![Business Card Layout](/output/BusinessCard-annotated.png)
## Why?!

Matplotlib is not at all the best tool for making a business card - I would not recommend using matplotlib as a replacement for design software if your intent is to achieve results at anything resembling a somewhat reasonable rate. So why does this project exist?

The purpose of this project was to achieve and demonstrate mastery of matplotlib layout fundamentals by using matplotlib for a task that needs pixel-perfect precision. Getting the business card layout to work as expected involved a surprising variety of advanced matplotlib details that are potentially useful for other custom visualizations. Details like:

- Pixel-perfect subplot layouts
  - Disabling automatic margins/padding in Jupyter Labs notebooks
- Texts inside bars
- Adding outline strokes to text
- A pixel-perfect horizontal bar layout
- Displaying raster graphic assets (jpg file for headshot)
- Displaying vector graphic assets (svg files for contact icons)
- Using custom coordinate spaces including flipped y axis to facilitate layout
- Using transforms to convert between different coordinate spaces
- Managing artist hierarchies

To discover the full details on any of these techniques for use in your matplotlib charts, please explore the [business card notebook](businesscard-matplotlib.ipynb).

## How?

Roughly in order of relevance for improving your everyday charts, this project features the following matplotlib tricks:

### Text Outlines
![Text Outlines](/screenshots/outlines.png)

To add an outline stroke to a matplotlib text, we can use maplotlib’s **patheffects** library:

```
def add_outline(artist: Artist, color = 'k', linewidth = 1):
    artist.set_path_effects([
        path_effects.Stroke(linewidth = linewidth, foreground = color),
        path_effects.Normal()
    ])
```

To obtain a handle on one or more Text objects to which to add an outline effect, use the results of any matplotlib method that creates text. Common examples include **annotation**, **text**, and **bar_label**.

This trick is especially useful for displaying text on the inside of a bar chart’s bars. Practical applications include highlighting an individual value or fitting a bar label that would be out of bounds if placed outside of its bar.

### Internal bar labels
![Bar Labels](/screenshots/text_in_box.png)

Adding labels inside of a bar chart’s bars is useful for a wide variety of plots.  We can achieve this effect by getting a handle on the individual bars (**[Rectangle](https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Rectangle.html)** instances) created when making a bar chart, then using the very versatile **[annotate](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.annotate.html)** method to insert texts relative to each bar:

```
bars = plt.barh(ys, widths)

for bar in bars: # bar is Rectangle instance
	text = plt.annotate(
		bar_text, 
		# text alignment relative to bar, in data coordinates
		xy = (bar.get_x(), bar.get_center()[1]), verticalalignment = 'center', horizontalalignment = 'left',
		# additional offset in points (or other coordinate system if desired)
		xytext = (label_margin_in_points, 0), textcoords = 'offset points',
	)
```

matplotlib also offers a convenient [bar_label](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.bar_label.html) utility, but it only supports layouts relative the right or top edge of a bar.

### Precise Subplot Layouts
Laying out subplots precisely in matplotlib is deceptively difficult and can be an exercise in frustration. Matplotlib features numerous layout engines (default, tight layout, constrained layout, compressed layout, auto layout), all of which are sophisticated and seem to have a mind of their own once we apply them to a subplot. To achieve pixel-perfect control over regions of the overall figure, this project uses a more custom approach:

```
# Prevents Jupyter Labs from adding unwanted margins to figures in notebooks:
%config InlineBackend.print_figure_kwargs = {'bbox_inches': None}

# Carves out an exact area of a figure for a subplot:
header_area_inches = Bbox.from_extents(
    0, fig_height - bleed - headshot_size - 2 * margin_y,
    fig_width, fig_height
)
# Normalize inches to 0-1 coordinates relative to the figure:
header_area_relative = inches_to_figure_space(header_area_inches, figure)
header = figure.add_axes(header_area_relative)
```

### Artist Tree Dumps
![Layout Tree](/screenshots/debugLog.png)

This project creates a reusable [matplotliblayout](matplotliblayout.py) module that can pretty-print the layout of all parts of a figure down to pixel-level precision. I used this tool frequently throughout the project to help troubleshoot layouts, and I expect to use it to help in future projects as well.

### Raster Graphics
![Raster Graphic](/screenshots/raster.png)

Integrating an image asset (the headshot) into a matplotlib plot is deceptively difficult. At first, it seems like the very versatile [imshow](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.imshow.html) method is the answer. This utility can display an image if given image data or a heat map if given a 2D matrix of values.

However, imshow does not allow us to control layout - it takes over a chart completely instead of inserting an image into it. It also does not solve how to load the image from a file. To add an image asset at a specific point in a plot, we need to use a combination of the PIL library, AxesImage, an image extents instead:

```
from PIL import Image # PIL/pillow is standard with Anaconda installations
im_data = Image.open('assets/headshot.jpg')
im = AxesImage(header)
im.set_data(im_data)
box = headshot_area # in data coordinates, which are configured as inches in this case
# Paste the image into a desired target area, in data coordinates.
im.set_extent((box.x0, box.x1, box.y0, box.y1)) 
```

### Vector / SVG Graphics
![Vector Graphics](/screenshots/svgs.png)

Integrating vector/svg assets into a plot was by far the most challenging aspect of this project because matplotlib does not offer direct support for svgs.

Matplotlib’s feature-equivalent to svg graphics is the very versatile [paths](https://matplotlib.org/stable/api/path_api.html) module, but converting an svg into a matplotlib path is a challenge with no built-in solution even with Anaconda installations. Matplotlib’s extensive documentation helpfully offers [an example](https://matplotlib.org/stable/gallery/showcase/firefox.html#sphx-glr-gallery-showcase-firefox-py), but the example offers only enough parsing logic to handle the single image in the demo. The full svg spec is much larger than this single case and is well beyond the scope of a simple matplotlib documentation page. Realistically, loading svg data requires a 3rd party library like [svgpathtools](https://pypi.org/project/svgpathtools/) instead.

But wait, there’s more. Once we obtain a matplotlib path, laying out the path within a figure is another challenge, and requires understanding of matplotlib [transforms](https://matplotlib.org/stable/api/transformations.html#module-matplotlib.transforms). For unknown reasons, matplotlib’s diverse [Artist hierarchyi](https://matplotlib.org/stable/api/artist_api.html) uses diverse layout systems and methods depending on objet type, so laying out a path is entirely different from laying out an image, which in turn is entirely different from laying out a text.

A distilled version of how this project places svg assets into a plot is:

```
path, metadata = read_svg(asset_file)
icon_width_px, icon_height_px = metadata['size']
# svgs load in pixel coordinates with zero origin:
bbox_source = Bbox.from_bounds(0,0, icon_width_px, icon_height_px)
# but we want to place the svg
icon_x_px, icon_y_px = ... # 
bbox_destination = pixels_to_figure_space(Bbox.from_bounds(
    icon_right_px - icon_width_px, , icon_width, icon_height
), fig) # Desired asset location in figure-relative space

# 2. place icon in bounding box.
patch = PathPatch(path, facecolor = f'C{index}', **contact_icon_style)
#from_bbox = Bbox.from_bounds(0, 0, box_px.width, icon_box_px.height)
patch.set_transform(transform(bbox_asset, bbox_icon) + fig.transFigure)
```
