
How To Build A New Icon Font
============================

Welcome. Contained in this repo is everything you need to build a new custom
RhodeCode icon font for RhodeCode Community and Enterprise Editions. While the
files are here, this document references what needs to be done in the actual
Community Edition repository.

Creating New Icons
------------------

Presumably, you're reading this because you'd like to update the icon font with
new icons. To create new icons, you'll want to use Illustrator. Start with an
empty 1000px x 1000px artboard, or use an existing .svg file if you'd like to
use an existing icon as a guide.

You'll need to make sure that your outlines are paths. This can be done using
the Shape Modes in the Pathfinder tool; see Window > Pathfinder in Illustrator
to build a compound image. It may happen that your image is rasterized, in which
case it will need to be converted to vector; check the results carefully.

    .. note::
        When adding to the existing icon collection, please maintain our
        existing icon style.


Creating The Font
-----------------

*Fontello*

We use fontello.com to generate the font files. On the main page, there is a
section for clicking and dragging icons to add to a font. If you would like to
use the existing font icons, here you will need to drag the .json file from the
current fontello folder. Once it has preloaded all of the existing fonts, drag
any new .svg icons into this same section to add them.

Any icons which appear blank or incorrect will need to be rebuilt in Illustrator.
This likely means that the paths have not been generated correctly; check the
settings in the Pathfinder tool.

After all of the icons are loaded into fontello, resist the temptation to click
the big red button; there's another task to do. Each icon has a pencil button;
click *every* icon - including the pre-existing ones - and check the settings.
Each current icon should have the same hex code as that which is listed in
rcicons.less. The "default css name" should be its simplified name; this is what
will be prepended with "icon-" for the CSS classes. Also remove any unnecessary
information from the keywords.

Once you have checked the icons, click the button in fontello which downloads a
zip file of the new font.


Preparing The LESS Files
------------------------

    .. note::
        It's a good idea to have `grunt watch` running in the background for this.

First, obviously the font files located in the unzipped folder under "font"
should replace the existing files in rhodecode/public/fonts/RCIcons/. While
doing this, check the permissions of the files that they have not changed; they
should be set to `chmod 644` but fontello's files may be different.

Next, you'll need to open the rcicons.css file which comes in the fontello .zip
and match the @font-face declaration to the one at the top of
rhodecode/public/css/rcicons.less, making sure to adjust the paths to
/fonts/RCIcons/.

In the same file, you will see the CSS for each icon. Take a quick look to make
sure that the existing icons haven't changed; if they have, you'll need to
adjust the content. Add any new icons to rcicons.less (note that similar ones
have been grouped together).

If you haven't yet, you'll need to run grunt to compile the LESS files; see the
developer documentation for instructions.

