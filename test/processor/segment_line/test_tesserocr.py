import os
import shutil

from ocrd.resolver import Resolver
from ocrd.processor.segment_region.tesserocr import Tesseract3RegionSegmenter
from ocrd.processor.segment_line.tesserocr import Tesseract3LineSegmenter

from test.base import TestCase, main, assets
METS_HEROLD_SMALL = assets.url_of('SBB0000F29300010000/mets_one_file.xml')

WORKSPACE_DIR = '/tmp/pyocrd-test-segment-line-tesserocr'

class TestProcessorSegmentLineTesseract3(TestCase):

    def setUp(self):
        if os.path.exists(WORKSPACE_DIR):
            shutil.rmtree(WORKSPACE_DIR)
        os.makedirs(WORKSPACE_DIR)

    def runTest(self):
        resolver = Resolver(cache_enabled=True)
        workspace = resolver.create_workspace(METS_HEROLD_SMALL, directory=WORKSPACE_DIR)
        Tesseract3RegionSegmenter(workspace, inputGrp="INPUT", outputGrp="OCR-D-SEG-BLOCK").process()
        #  workspace.save_mets()
        Tesseract3LineSegmenter(workspace, inputGrp="OCR-D-SEG-BLOCK", outputGrp="OCR-D-SEG-LINE").process()
        workspace.save_mets()

if __name__ == '__main__':
    main()
