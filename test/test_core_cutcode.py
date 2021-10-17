import unittest

from PIL import Image, ImageDraw

from meerk40t.core.cutcode import LaserSettings, LineCut, CutCode, QuadCut, RasterCut
from meerk40t.core.elements import LaserOperation
from meerk40t.svgelements import Point, Path, SVGImage


class TestCutcode(unittest.TestCase):
    def test_cutcode(self):
        """
        Test intro to Cutcode.

        :return:
        """
        cutcode = CutCode()
        settings = LaserSettings()
        cutcode.append(LineCut(Point(0, 0), Point(100, 100), settings=settings))
        cutcode.append(LineCut(Point(100, 100), Point(0, 0), settings=settings))
        cutcode.append(LineCut(Point(50, -50), Point(100, -100), settings=settings))
        cutcode.append(
            QuadCut(Point(0, 0), Point(100, 100), Point(200, 0), settings=settings)
        )
        path = Path(*list(cutcode.as_elements()))
        self.assertEqual(
            path, "M 0,0 L 100,100 L 0,0 M 50,-50 L 100,-100 M 0,0 Q 100,100 200,0"
        )

    def test_cutcode_cut(self):
        """
        Convert a Cut Operation into Cutcode and Back.

        :return:
        """
        initial = "M 0,0 L 100,100 L 0,0 M 50,-50 L 100,-100 M 0,0 Q 100,100 200,0"
        path = Path(initial)
        laserop = LaserOperation()
        laserop.operation = "Cut"
        laserop.add(path, type="opnode")
        cutcode = CutCode(laserop.as_cutobjects())
        path = list(cutcode.as_elements())[0]
        self.assertEqual(path, initial)

    def test_cutcode_engrave(self):
        """
        Convert an Engrave Operation into Cutcode and Back.

        :return:
        """
        initial = "M 0,0 L 100,100 L 0,0 M 50,-50 L 100,-100 M 0,0 Q 100,100 200,0"
        path = Path(initial)
        laserop = LaserOperation()
        laserop.operation = "Engrave"
        laserop.add(path, type="opnode")
        cutcode = CutCode(laserop.as_cutobjects())
        path = list(cutcode.as_elements())[0]
        self.assertEqual(path, initial)

    def test_cutcode_no_type(self):
        """
        Convert an Unknown Operation into Cutcode and Back.

        :return:
        """
        initial = "M 0,0 L 100,100 L 0,0 M 50,-50 L 100,-100 M 0,0 Q 100,100 200,0"
        path = Path(initial)
        laserop = LaserOperation()
        # Operation type is unset.
        laserop.add(path, type="opnode")
        cutcode = CutCode(laserop.as_cutobjects())

        self.assertEqual(len(list(cutcode.flat())), 0)  # Unknown is blank.

    def test_cutcode_raster(self):
        """
        Convert CutCode from Raster Operation

        :return:
        """
        laserop = LaserOperation()
        laserop.operation = "Raster"

        # Add Path
        initial = "M 0,0 L 100,100 L 0,0 M 50,-50 L 100,-100 M 0,0 Q 100,100 200,0"
        path = Path(initial)
        laserop.add(path, type="opnode")

        # Add SVG Image
        svg_image = SVGImage()
        svg_image.image = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
        svg_image.values["raster_step"] = 3  # Raster should ignore this value.
        draw = ImageDraw.Draw(svg_image.image)
        draw.ellipse((50, 50, 150, 150), "white")
        draw.ellipse((100, 100, 105, 105), "black")
        laserop.add(svg_image, type="opnode")

        # raster_step is default to 0 and not set.
        self.assertRaises(AssertionError, CutCode, laserop.as_cutobjects())

        laserop.settings.raster_step = 2
        cutcode = CutCode(laserop.as_cutobjects())
        self.assertEqual(len(cutcode), 1)
        rastercut = cutcode[0]
        self.assertTrue(isinstance(rastercut, RasterCut))
        self.assertEqual(rastercut.tx, 100)
        self.assertEqual(rastercut.ty, 100)
        image = rastercut.image
        self.assertTrue(isinstance(image, Image.Image))
        self.assertIn(image.mode, ("L", "1"))
        self.assertEqual(image.size, (3, 3))

    def test_cutcode_raster_crosshatch(self):
        """
        Convert CutCode from Raster Operation, crosshatched

        :return:
        """
        # Initialize with Raster Defaults, +crosshatch
        laserop = LaserOperation(operation="Raster", raster_direction=4)
        # Default step 2.

        # Add Path
        initial = "M 0,0 L 100,100 L 0,0 M 50,-50 L 100,-100 M 0,0 Q 100,100 200,0"
        path = Path(initial)
        laserop.add(path, type="opnode")

        # Add SVG Image
        svg_image = SVGImage()
        svg_image.image = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
        svg_image.values["raster_step"] = 3
        draw = ImageDraw.Draw(svg_image.image)
        draw.ellipse((50, 50, 150, 150), "white")
        draw.ellipse((100, 100, 105, 105), "black")
        laserop.add(svg_image, type="opnode")

        cutcode = CutCode(laserop.as_cutobjects())
        self.assertEqual(len(cutcode), 2)

        rastercut0 = cutcode[0]
        self.assertTrue(isinstance(rastercut0, RasterCut))
        self.assertEqual(rastercut0.tx, 100)
        self.assertEqual(rastercut0.ty, 100)
        image0 = rastercut0.image
        self.assertTrue(isinstance(image0, Image.Image))
        self.assertIn(image0.mode, ("L", "1"))
        self.assertEqual(image0.size, (3, 3))  # default step value 2, 6/2

        rastercut1 = cutcode[1]
        self.assertTrue(isinstance(rastercut1, RasterCut))
        self.assertEqual(rastercut1.tx, 100)
        self.assertEqual(rastercut1.ty, 100)
        image1 = rastercut1.image
        self.assertTrue(isinstance(image1, Image.Image))
        self.assertIn(image1.mode, ("L", "1"))
        self.assertEqual(image1.size, (3, 3))  # default step value 2, 6/2

        self.assertIs(image0, image1)

    def test_cutcode_image(self):
        """
        Convert CutCode from Image Operation, also test image-based crosshatched

        :return:
        """
        laserop = LaserOperation()
        laserop.operation = "Image"

        # Add Path
        initial = "M 0,0 L 100,100 L 0,0 M 50,-50 L 100,-100 M 0,0 Q 100,100 200,0"
        path = Path(initial)
        laserop.add(path, type="opnode")

        # Add SVG Image1
        svg_image1 = SVGImage()
        svg_image1.image = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
        svg_image1.values["raster_step"] = 3
        draw = ImageDraw.Draw(svg_image1.image)
        draw.ellipse((50, 50, 150, 150), "white")
        draw.ellipse((100, 100, 105, 105), "black")
        laserop.add(svg_image1, type="opnode")

        # Add SVG Image2
        svg_image2 = SVGImage()
        svg_image2.image = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
        svg_image2.values["raster_step"] = 2
        svg_image2.values["raster_direction"] = 4  # Crosshatch.
        draw = ImageDraw.Draw(svg_image2.image)
        draw.ellipse((50, 50, 150, 150), "white")
        draw.ellipse((80, 80, 120, 120), "black")
        laserop.add(svg_image2, type="opnode")

        cutcode = CutCode(laserop.as_cutobjects())
        self.assertEqual(len(cutcode), 3)
        rastercut = cutcode[0]
        self.assertTrue(isinstance(rastercut, RasterCut))
        self.assertEqual(rastercut.tx, 100)
        self.assertEqual(rastercut.ty, 100)
        image = rastercut.image
        self.assertTrue(isinstance(image, Image.Image))
        self.assertIn(image.mode, ("L", "1"))
        self.assertEqual(image.size, (2, 2))  # step value 2, 6/2

        rastercut1 = cutcode[1]
        self.assertTrue(isinstance(rastercut1, RasterCut))
        self.assertEqual(rastercut1.tx, 80)
        self.assertEqual(rastercut1.ty, 80)
        image1 = rastercut1.image
        self.assertTrue(isinstance(image1, Image.Image))
        self.assertIn(image1.mode, ("L", "1"))
        self.assertEqual(image1.size, (21, 21))  # default step value 2, 40/2 + 1

        rastercut2 = cutcode[2]
        self.assertTrue(isinstance(rastercut2, RasterCut))
        self.assertEqual(rastercut2.tx, 80)
        self.assertEqual(rastercut2.ty, 80)
        image2 = rastercut2.image
        self.assertTrue(isinstance(image2, Image.Image))
        self.assertIn(image2.mode, ("L", "1"))
        self.assertEqual(image2.size, (21, 21))  # default step value 2, 40/2 + 1

    def test_cutcode_image_crosshatch(self):
        """
        Convert CutCode from Image Operation. ImageOp Crosshatch

        :return:
        """
        laserop = LaserOperation(operation="Image", raster_direction=4)

        # Add Path
        initial = "M 0,0 L 100,100 L 0,0 M 50,-50 L 100,-100 M 0,0 Q 100,100 200,0"
        path = Path(initial)
        laserop.add(path, type="opnode")

        # Add SVG Image1
        svg_image1 = SVGImage()
        svg_image1.image = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
        svg_image1.values["raster_step"] = 3
        draw = ImageDraw.Draw(svg_image1.image)
        draw.ellipse((50, 50, 150, 150), "white")
        draw.ellipse((100, 100, 105, 105), "black")
        laserop.add(svg_image1, type="opnode")

        # Add SVG Image2
        svg_image2 = SVGImage()
        svg_image2.image = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
        svg_image2.values["raster_step"] = 2
        draw = ImageDraw.Draw(svg_image2.image)
        draw.ellipse((50, 50, 150, 150), "white")
        draw.ellipse((80, 80, 120, 120), "black")
        laserop.add(svg_image2, type="opnode")

        cutcode = CutCode(laserop.as_cutobjects())
        self.assertEqual(len(cutcode), 4)

        rastercut1_0 = cutcode[0]
        self.assertTrue(isinstance(rastercut1_0, RasterCut))
        self.assertEqual(rastercut1_0.tx, 100)
        self.assertEqual(rastercut1_0.ty, 100)
        image = rastercut1_0.image
        self.assertTrue(isinstance(image, Image.Image))
        self.assertIn(image.mode, ("L", "1"))
        self.assertEqual(image.size, (2, 2))  # step value 2, 6/2

        rastercut1_1 = cutcode[1]
        self.assertTrue(isinstance(rastercut1_1, RasterCut))
        self.assertEqual(rastercut1_1.tx, 100)
        self.assertEqual(rastercut1_1.ty, 100)
        image = rastercut1_1.image
        self.assertTrue(isinstance(image, Image.Image))
        self.assertIn(image.mode, ("L", "1"))
        self.assertEqual(image.size, (2, 2))  # step value 2, 6/2

        rastercut2_0 = cutcode[2]
        self.assertTrue(isinstance(rastercut2_0, RasterCut))
        self.assertEqual(rastercut2_0.tx, 80)
        self.assertEqual(rastercut2_0.ty, 80)
        image1 = rastercut2_0.image
        self.assertTrue(isinstance(image1, Image.Image))
        self.assertIn(image1.mode, ("L", "1"))
        self.assertEqual(image1.size, (21, 21))  # default step value 2, 40/2 + 1

        rastercut2_1 = cutcode[3]
        self.assertTrue(isinstance(rastercut2_1, RasterCut))
        self.assertEqual(rastercut2_1.tx, 80)
        self.assertEqual(rastercut2_1.ty, 80)
        image2 = rastercut2_1.image
        self.assertTrue(isinstance(image2, Image.Image))
        self.assertIn(image2.mode, ("L", "1"))
        self.assertEqual(image2.size, (21, 21))  # default step value 2, 40/2 + 1

    def test_cutcode_image_nostep(self):
        """
        Convert CutCode from Image Operation
        Test default value without step.

        Reuse Checks for Knockon-Effect

        :return:
        """
        laserop = LaserOperation(operation="Image")

        # Add Path
        initial = "M 0,0 L 100,100 L 0,0 M 50,-50 L 100,-100 M 0,0 Q 100,100 200,0"
        path = Path(initial)
        laserop.add(path, type="opnode")

        # Add SVG Image1
        svg_image1 = SVGImage()
        svg_image1.image = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
        draw = ImageDraw.Draw(svg_image1.image)
        draw.ellipse((50, 50, 150, 150), "white")
        draw.ellipse((100, 100, 105, 105), "black")
        laserop.add(svg_image1, type="opnode")

        cutcode = CutCode(laserop.as_cutobjects())
        self.assertEqual(len(cutcode), 1)

        rastercut = cutcode[0]
        self.assertTrue(isinstance(rastercut, RasterCut))
        self.assertEqual(rastercut.tx, 100)
        self.assertEqual(rastercut.ty, 100)
        image = rastercut.image
        self.assertTrue(isinstance(image, Image.Image))
        self.assertIn(image.mode, ("L", "1"))
        self.assertEqual(image.size, (6, 6))  # step value 1, 6/2

        laserop.settings.raster_step = 2  # Raster_Step should be ignored.
        cutcode = CutCode(laserop.as_cutobjects())
        self.assertEqual(len(cutcode), 1)

        rastercut = cutcode[0]
        self.assertTrue(isinstance(rastercut, RasterCut))
        self.assertEqual(rastercut.tx, 100)
        self.assertEqual(rastercut.ty, 100)
        image = rastercut.image
        self.assertTrue(isinstance(image, Image.Image))
        self.assertIn(image.mode, ("L", "1"))
        self.assertEqual(image.size, (6, 6))  # step value 1, 6/1
