from app.main_window import MainWindow


def test_sidebar_canvas_properties_are_wrapped_in_rounded_cards(qtbot):
    """IMG_9186.png 참고 디자인처럼 사이드바/캔버스/속성 패널이 서로 붙은 사각 블록이
    아니라, 각각 독립된 카드(QFrame)로 감싸져 있어야 한다."""
    window = MainWindow()
    qtbot.addWidget(window)

    sidebar_card = window.sidebar.parentWidget()
    assert sidebar_card is not None
    assert sidebar_card.objectName() == "sidebarCard"

    properties_card = window.properties_panel.parentWidget()
    assert properties_card is not None
    assert properties_card.objectName() == "propertiesCard"

    canvas_card = window.center_stack.parentWidget()
    assert canvas_card is not None
    assert canvas_card.objectName() == "canvasCard"


def test_brand_widget_has_object_names_for_transparent_background(qtbot):
    """브랜드(로고+텍스트) 위젯이 툴바와 다른 색으로 떠 보이지 않도록, dark.qss가
    투명 처리할 수 있는 objectName이 지정되어 있어야 한다."""
    window = MainWindow()
    qtbot.addWidget(window)

    from PySide6.QtWidgets import QWidget

    brand = window.findChild(QWidget, "brandWidget")
    assert brand is not None

    name_label = window.findChild(QWidget, "brandName")
    assert name_label is not None
    icon_label = window.findChild(QWidget, "brandIcon")
    assert icon_label is not None


def test_sidebar_and_properties_cards_have_equal_gap_to_canvas_card(qtbot):
    """QSplitter가 고정폭 카드의 sizeHint를 기준으로 section을 잘못 잡아, 사이드바-캔버스
    간격이 캔버스-속성패널 간격보다 넓어 보이던 버그의 회귀 테스트. 두 간격이 같아야 한다."""
    from PySide6.QtWidgets import QSplitter

    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1360, 840)
    window.show()
    qtbot.wait(10)

    splitter = window.centralWidget().findChild(QSplitter, "mainSplitter")
    assert splitter is not None

    sidebar_card = window.sidebar.parentWidget()
    canvas_card = window.center_stack.parentWidget()
    properties_card = window.properties_panel.parentWidget()

    gap_left = canvas_card.geometry().left() - sidebar_card.geometry().right()
    gap_right = properties_card.geometry().left() - canvas_card.geometry().right()

    assert gap_left == gap_right
    assert sidebar_card.width() == 208
    assert properties_card.width() == 340
