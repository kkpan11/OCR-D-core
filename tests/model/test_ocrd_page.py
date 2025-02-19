# -*- coding: utf-8 -*-

import pytest

from tests.base import main, assets, create_ocrd_file_with_defaults

from ocrd_modelfactory import page_from_image, page_from_file
from ocrd_models.ocrd_page_generateds import TextTypeSimpleType
from ocrd_models.ocrd_page import (
    AlternativeImageType,
    PcGtsType,
    PageType,
    TextRegionType,
    TextLineType,
    OrderedGroupIndexedType,
    UnorderedGroupIndexedType,
    ReadingOrderType,
    RegionRefIndexedType,
    WordType,
    GlyphType,

    parseString,
    parse,
    to_xml
)

simple_page = """\
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15 http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd">
    <Metadata>
        <Creator>OCR-D</Creator>
        <Created>2016-09-20T11:09:27.041+02:00</Created>
        <LastChange>2018-04-25T17:44:49.605+01:00</LastChange>
    </Metadata>
    <Page
        imageFilename="https://github.com/OCR-D/assets/raw/master/data/kant_aufklaerung_1784/data/OCR-D-IMG/INPUT_0017.tif"
        imageWidth="1457"
        imageHeight="2083"
        type="content">
        <TextRegion type="heading" id="r_1_1" custom="readingOrder {index:0;} structure {type:heading;}">
            <Coords points="113,365 919,365 919,439 113,439"/>
            <TextLine id="tl_1" primaryLanguage="German" custom="readingOrder {index:0;} textStyle {offset:0; length:26;fontFamily:Arial; fontSize:17.0; bold:true;}">
                <Coords points="114,366 918,366 918,438 114,438"/>
                <Baseline points="114,429 918,429"/>
                <Word id="w_w1aab1b1b2b1b1ab1" language="German" custom="readingOrder {index:0;} textStyle {offset:0; length:11;fontFamily:Arial; fontSize:17.0; bold:true;}">
                    <Coords points="114,368 442,368 442,437 114,437"/>
                    <TextEquiv conf="1">
                        <Unicode>Berliniſche</Unicode>
                    </TextEquiv>
                </Word>
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>
"""


@pytest.fixture(name='faulty_glyphs')
def _fixture_faulty_glyphs():
    with open(assets.path_to('glyph-consistency/data/OCR-D-GT-PAGE/FAULTY_GLYPHS.xml'), 'rb') as f:
        xml_as_str = f.read()
    pcgts = parseString(xml_as_str, silence=True)
    yield pcgts


def test_pcgts_id_matches(faulty_glyphs):
    assert faulty_glyphs.pcGtsId == 'FAULTY_GLYPHS_FILE'


def test_faulty_glyphs_to_xml(faulty_glyphs):
    as_xml = to_xml(faulty_glyphs)
    assert ' xmlns:pc="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"' in as_xml[:1000]
    assert ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15 http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd"', as_xml[:1000]
    assert '<pc:PcGts' in as_xml[0:100]
    assert '<pc:TextRegion' in as_xml[1000:3000]


def test_to_xml_unicode_nsprefix():
    """see https://github.com/OCR-D/core/pull/474#issuecomment-621477590"""

    # arrange
    with open(assets.path_to('kant_aufklaerung_1784-binarized/data/OCR-D-GT-WORD/INPUT_0020.xml'), 'rb') as f:
        from_xml = f.read()

    # assert
    assert '<Unicode>' in from_xml.decode('utf-8'), 'without NS prefix'
    assert '<Created' in from_xml.decode('utf-8'), 'without NS prefix'
    pcgts = parseString(from_xml, silence=True)
    as_xml = to_xml(pcgts)
    assert '<pc:Unicode>' in as_xml, 'with NS prefix'
    assert '<pc:Created>' in as_xml, 'with NS prefix'


def test_issue_269(faulty_glyphs):
    """
    @conf is parsed as str but should be float
    https://github.com/OCR-D/core/issues/269
    """
    # GIGO
    faulty_glyphs.get_Page().get_TextRegion()[0].get_TextEquiv()[0].set_conf(1.0)
    assert type(faulty_glyphs.get_Page().get_TextRegion()[0].get_TextEquiv()[0].get_conf()) == float
    faulty_glyphs.get_Page().get_TextRegion()[0].get_TextEquiv()[0].set_conf('1.0')
    assert type(faulty_glyphs.get_Page().get_TextRegion()[0].get_TextEquiv()[0].get_conf()) == str


def test_parse_string_succeeds():
    """parseString with @conf in TextEquiv won't throw an error"""
    assert parseString(simple_page, silence=True) is not None


def test_delete_region():
    pcgts = parseString(simple_page, silence=True)
    assert len(pcgts.get_Page().get_TextRegion()) == 1

    # act
    del pcgts.get_Page().get_TextRegion()[0]

    # assert
    assert len(pcgts.get_Page().get_TextRegion()) == 0


def test_set_image_filename(faulty_glyphs):
    assert faulty_glyphs.get_Page().imageFilename == '00000259.sw.tif'

    # act
    faulty_glyphs.get_Page().imageFilename = 'foo'

    # assert
    assert faulty_glyphs.get_Page().imageFilename == 'foo'


def test_alternative_image_additions():
    pcgts = PcGtsType(pcGtsId="foo")
    assert pcgts.pcGtsId == 'foo'

    # act
    # Page/AlternativeImage
    page = PageType()
    pcgts.set_Page(page)
    page.add_AlternativeImage(AlternativeImageType())
    # TextRegion/AlternativeImage
    region = TextRegionType()
    page.add_TextRegion(region)
    region.add_AlternativeImage(AlternativeImageType())
    # TextLine/AlternativeImage
    line = TextLineType()
    region.add_TextLine(line)
    line.add_AlternativeImage(AlternativeImageType())
    # Word/AlternativeImage
    word = WordType()
    line.add_Word(word)
    word.add_AlternativeImage(AlternativeImageType())
    # Glyph/AlternativeImage
    glyph = GlyphType()
    word.add_Glyph(glyph)
    glyph.add_AlternativeImage(AlternativeImageType())

    # TODO assertions


def test_simple_types(faulty_glyphs):
    regions = faulty_glyphs.get_Page().get_TextRegion()
    reg = regions[0]

    # assert
    assert isinstance(reg.get_type(), str)
    assert reg.get_type() == TextTypeSimpleType.CREDIT
    assert isinstance(TextTypeSimpleType.CREDIT, str)
    assert reg.get_type() == 'credit'
    assert isinstance(TextTypeSimpleType.CREDIT, str)
    reg.set_type(TextTypeSimpleType.PAGENUMBER)
    assert reg.get_type() == 'page-number'
    assert isinstance(reg.get_type(), str)


def test_orderedgroup_export_order():
    """
    See https://github.com/OCR-D/core/issues/475
    """
    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        pcgts = parseString(f.read().encode('utf8'), silence=True)

    # act
    og = pcgts.get_Page().get_ReadingOrder().get_OrderedGroup()
    xml_before = to_xml(og)
    children = og.get_AllIndexed()

    # assert
    assert len(children) == 22
    assert [c.index for c in children] == list(range(0, 22))
    # mix up the indexes
    children[0].index = 11
    children[11].index = 3
    children[3].index = 0
    assert [c.index for c in children] == [11, 1, 2, 0, 4, 5, 6, 7, 8, 9, 10, 3, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
    assert [c.index for c in og.get_AllIndexed()] == list(range(0, 22))
    assert og.get_AllIndexed()[1].__class__ == OrderedGroupIndexedType
    # serialize and make sure the correct order was serialized
    new_pcgts = parseString(to_xml(pcgts).encode('utf8'), silence=True)
    new_og = new_pcgts.get_Page().get_ReadingOrder().get_OrderedGroup()
    assert [c.index for c in new_og.get_AllIndexed()] == list(range(0, 22))

    xml_after = to_xml(new_og)
    # TODO why not working?
    #assert xml_after == xml_before


def test_empty_groups_to_regionrefindexed():
    """
    Corrolary See https://github.com/OCR-D/core/issues/475
    """
    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        pcgts = parseString(f.read().encode('utf8'), silence=True)

    og = pcgts.get_Page().get_ReadingOrder().get_OrderedGroup()
    children = og.get_AllIndexed()

    # assert
    assert isinstance(children[1], OrderedGroupIndexedType)
    assert isinstance(children[21], UnorderedGroupIndexedType)
    # empty all the elements in the first orederdGroupIndexed
    children[1].set_RegionRefIndexed([])
    # serialize apnd parse to see empty group converted
    pcgts = parseString(to_xml(pcgts).encode('utf8'), silence=True)
    og = pcgts.get_Page().get_ReadingOrder().get_OrderedGroup()
    children = og.get_AllIndexed()
    assert isinstance(children[1], RegionRefIndexedType)
    assert isinstance(children[21], RegionRefIndexedType)


def test_all_regions_without_reading_order():
    """
    https://github.com/OCR-D/core/pull/479
    https://github.com/OCR-D/core/issues/240#issuecomment-493135797
    """
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        pcgts = parseString(f.read().encode('utf8'), silence=True)

    # act
    pg = pcgts.get_Page()

    # assert
    assert len(pg.get_AllRegions()) == 65
    assert len(pg.get_AllRegions(depth=0)) == 65
    assert len(pg.get_AllRegions(depth=1)) == 45
    assert len(pg.get_AllRegions(depth=2)) == 65
    assert len(pg.get_AllRegions(depth=3)) == 65
    assert len(pg.get_AllRegions(classes=['Separator'])) == 25
    assert len(pg.get_AllRegions(classes=['Table'])) == 3
    assert len(pg.get_AllRegions(classes=['Text'])) == 37
    assert len(pg.get_AllRegions(classes=['Text'], depth=1)) == 17
    assert len(pg.get_AllRegions(classes=['Text'], depth=2)) == 37


def test_get_all_regions_invalid_order_raises_exception():
    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        pg = parseString(f.read().encode('utf8'), silence=True).get_Page()

    # act
    with pytest.raises(Exception) as exc:
        pg.get_AllRegions(order='random')

    # assert
    assert "Argument 'order' must be either 'document', 'reading-order' or 'reading-order-only', not 'random'" in str(exc.value)


def test_get_all_regions_invalid_depth_raises_exception():
    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        pg = parseString(f.read().encode('utf8'), silence=True).get_Page()

    # act
    with pytest.raises(Exception) as exc:
        pg.get_AllRegions(depth=-1)

    # assert
    assert "Argument 'depth' must be an integer greater-or-equal 0, not '-1'" in str(exc.value)


def test_all_regions_with_reading_order():
    """
    https://github.com/OCR-D/core/pull/479
    https://github.com/OCR-D/core/issues/240#issuecomment-493135797
    """

    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        pg = parseString(f.read().encode('utf8'), silence=True).get_Page()

    # assert
    assert len(pg.get_AllRegions(order='reading-order-only')) == 40
    assert len(pg.get_AllRegions(order='reading-order-only', depth=1)) == 20
    assert len(pg.get_AllRegions(order='reading-order-only', depth=2)) == 40
    assert len(pg.get_AllRegions(order='reading-order', depth=0)) == 65
    assert len(pg.get_AllRegions(order='reading-order', depth=1)) == 45
    assert len(pg.get_AllRegions(order='reading-order', depth=2)) == 65
    assert len(pg.get_AllRegions(classes=['Table'], order='reading-order')) == 3
    assert len(pg.get_AllRegions(classes=['Text'], order='reading-order')) == 37
    assert len(pg.get_AllRegions(classes=['Text'], order='reading-order', depth=1)) == 17


def test_get_unordered_group_children():
    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        pcgts = parseString(f.read().encode('utf8'), silence=True)

    # act
    ug = pcgts.get_Page().get_ReadingOrder().get_OrderedGroup().get_UnorderedGroupIndexed()[0]

    # assert
    assert len(ug.get_UnorderedGroupChildren()) == 1


def test_get_all_indexed_classes():
    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        pcgts = parseString(f.read().encode('utf8'), silence=True)

    # act
    og = pcgts.get_Page().get_ReadingOrder().get_OrderedGroup()

    # assert
    assert len(og.get_AllIndexed(classes=['RegionRef'])) == 17
    assert len(og.get_AllIndexed(classes=['OrderedGroup'])) == 3
    assert len(og.get_AllIndexed(classes=['UnorderedGroup'])) == 2


def test_get_all_indexed_index_sort():
    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        og = parseString(f.read().encode('utf8'), silence=True).get_Page().get_ReadingOrder().get_OrderedGroup()

    # act
    unogs = og.get_UnorderedGroupIndexed()

    # assert
    assert [x.index for x in unogs] == [20, 21]
    unogs[0].index = 21
    unogs[1].index = 20
    assert [x.index for x in og.get_AllIndexed(classes=['UnorderedGroup'], index_sort=True)] == [20, 21]
    assert [x.index for x in og.get_AllIndexed(classes=['UnorderedGroup'], index_sort=False)] == [21, 20]
    og.sort_AllIndexed()
    assert [x.index for x in og.get_AllIndexed(classes=['UnorderedGroup'], index_sort=False)] == [20, 21]


def test_extend_all_indexed_no_validation():
    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        og = parseString(f.read().encode('utf8'), silence=True).get_Page().get_ReadingOrder().get_OrderedGroup()

    # act
    og.extend_AllIndexed([
        RegionRefIndexedType(index=3, id='r3'),
        RegionRefIndexedType(index=2, id='r2'),
        RegionRefIndexedType(index=1, id='r1'),
    ])
    rrs = og.get_RegionRefIndexed()

    # assert
    assert [x.index for x in rrs][-3:] == [22, 23, 24]


def test_get_all_text_lines():
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        page = parseString(f.read().encode('utf8'), silence=True).get_Page()

    # assert
    assert len(page.get_AllTextLines()) == 55


def test_extend_all_indexed_validate_continuity():
    # arrange
    with open(assets.path_to('gutachten/data/TEMP1/PAGE_TEMP1.xml'), 'r') as f:
        og = parseString(f.read().encode('utf8'), silence=True).get_Page().get_ReadingOrder().get_OrderedGroup()

    # act
    with pytest.raises(Exception) as index_exc:
        og.extend_AllIndexed([
            RegionRefIndexedType(index=3, id='r3'),
            RegionRefIndexedType(index=2, id='r2'),
            RegionRefIndexedType(index=1, id='r1'),
        ], validate_continuity=True)

    assert "@index already used: 1" in str(index_exc.value)


def test_get_all_alternative_image_paths():
    # arrange
    with open(assets.path_to('kant_aufklaerung_1784-complex/data/OCR-D-OCR-OCRO-fraktur-SEG-LINE-tesseract-ocropy-DEWARP/OCR-D-OCR-OCRO-fraktur-SEG-LINE-tesseract-ocropy-DEWARP_0001.xml'), 'r') as f:
        pcgts = parseString(f.read().encode('utf8'), silence=True)

    # assert
    assert pcgts.get_AllAlternativeImagePaths(page=False, region=False, line=False) == []
    assert pcgts.get_AllAlternativeImagePaths(page=True, region=False, line=False) == [
        'OCR-D-IMG-BIN/OCR-D-IMG-BINPAGE-sauvola_0001-BIN_sauvola-ms-split.png',
        'OCR-D-IMG-CROP/OCR-D-IMG-CROP_0001.png',
        'OCR-D-IMG-BIN/INPUT_0017-BIN_sauvola-ms-split.png',
        'OCR-D-IMG-DESPECK/OCR-D-IMG-DESPECK_0001.png',
        'OCR-D-IMG-DESKEW/OCR-D-IMG-DESKEW_0001.png',
        'OCR-D-IMG-DESKEW/OCR-D-IMG-DESKEW_0001.png']
    assert len(pcgts.get_AllAlternativeImagePaths(page=True, region=True, line=False)) == 12
    assert len(pcgts.get_AllAlternativeImagePaths(page=True, region=True, line=False)) == 12
    assert len(pcgts.get_AllAlternativeImagePaths(page=True, region=True, line=True)) == 36

    # TODO: Test with word/glyph-level AlternativeImages
    # would work with len == 36
    # assert len(pcgts.get_AllAlternativeImagePaths(word=False)) == 37


def test_get_AllAlternativeImages():
    with open(assets.path_to('kant_aufklaerung_1784-complex/data/OCR-D-OCR-OCRO-fraktur-SEG-LINE-tesseract-ocropy-DEWARP/OCR-D-OCR-OCRO-fraktur-SEG-LINE-tesseract-ocropy-DEWARP_0001.xml'), 'r') as f:
        pcgts = parseString(f.read().encode('utf8'), silence=True)
        page = pcgts.get_Page()
        assert page.get_AllAlternativeImages(page=False, region=False, line=False) == []
        assert [x.filename for x in page.get_AllAlternativeImages(page=True, region=False, line=False)] == [
            'OCR-D-IMG-BIN/OCR-D-IMG-BINPAGE-sauvola_0001-BIN_sauvola-ms-split.png',
            'OCR-D-IMG-CROP/OCR-D-IMG-CROP_0001.png',
            'OCR-D-IMG-BIN/INPUT_0017-BIN_sauvola-ms-split.png',
            'OCR-D-IMG-DESPECK/OCR-D-IMG-DESPECK_0001.png',
            'OCR-D-IMG-DESKEW/OCR-D-IMG-DESKEW_0001.png',
            'OCR-D-IMG-DESKEW/OCR-D-IMG-DESKEW_0001.png']
        assert isinstance(page.get_AllAlternativeImages()[0], AlternativeImageType)


def test_serialize_no_empty_readingorder():
    """
    https://github.com/OCR-D/core/issues/602
    """
    pcgts = page_from_image(create_ocrd_file_with_defaults(local_filename=assets.path_to('kant_aufklaerung_1784/data/OCR-D-IMG/INPUT_0017.tif')))
    pcgts.get_Page().set_ReadingOrder(ReadingOrderType())
    assert pcgts.get_Page().get_ReadingOrder()
    pcgts = parseString(to_xml(pcgts, skip_declaration=True))
    assert not pcgts.get_Page().get_ReadingOrder()

def test_page_roundtrip(capsys):
    page_file = assets.path_to('kant_aufklaerung_1784/data/OCR-D-GT-PAGE/PAGE_0017_PAGE.xml')
    pcgts = page_from_file(page_file)
    text = to_xml(pcgts)
    assert "NoneRegionRefIndexed" not in text
    pcgts2 = parseString(text.encode('utf8'))
    stderr = capsys.readouterr().err
    assert pcgts2 is not None, stderr
    assert (pcgts.Page.ReadingOrder is not None) == (pcgts2.Page.ReadingOrder is not None)
    text2 = to_xml(pcgts2)
    assert text == text2
    assert len(pcgts.Page.ReadingOrder.OrderedGroup.RegionRefIndexed) == len(pcgts2.Page.ReadingOrder.OrderedGroup.RegionRefIndexed)

def test_hashable():
    """
    https://github.com/OCR-D/ocrd_segment/issues/45
    """
    pcgts = page_from_image(create_ocrd_file_with_defaults(local_filename=assets.path_to('kant_aufklaerung_1784/data/OCR-D-IMG/INPUT_0017.tif')))
    page = pcgts.get_Page()
    testset = set()
    testset.add(pcgts)
    testset.add(page)

    # TODO: was is actually to be asserted?


def test_id():
    """
    https://github.com/OCR-D/core/issues/682
    """
    fpath_page = assets.path_to('kant_aufklaerung_1784/data/OCR-D-GT-PAGE/PAGE_0017_PAGE.xml')
    pcgts = parse(fpath_page)

    # assert
    assert pcgts.id == 'PAGE_0017_PAGE'

    # TODO: is this *really* desired?
    # I would expect for a single Page-Element the ID is like from the top-level-Pgts-Container, not like a fileName
    assert pcgts.get_Page().id == 'OCR-D-IMG_INPUT_0017.tif'


if __name__ == '__main__':
    main(__file__)
