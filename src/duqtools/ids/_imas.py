# https://github.com/duqtools/duqtools/issues/27

import logging

logger = logging.getLogger(__name__)
imas_mocked = False

try:
    import xml.sax
    import xml.sax.handler

    import imas
    from imas import imasdef
    PATH_IDSDEF = '/gw/swimas/core/installer/src/3.34.0/ual/4.9.3/xml/IDSDef.xml'

    class Parser(xml.sax.handler.ContentHandler):
        import xml.sax
        import xml.sax.handler

        def __init__(self):
            xml.sax.handler.ContentHandler.__init__(self)
            self.idss = []

        def startElement(self, name: str, attrs):
            if name == 'IDS':
                ids = {}
                for i in attrs.getNames():
                    ids[i] = attrs.getValue(i)
                self.idss.append(ids)

        @classmethod
        def load_idsdef(cls):
            parser = cls()
            xml.sax.parse(PATH_IDSDEF, parser)
            return parser

except (ModuleNotFoundError, ImportError):
    from unittest.mock import MagicMock as Mock
    imas_mocked = True
    ids = Mock()
    ids.open_env = lambda *_, **__: [1]

    entry = Mock()
    entry.open = lambda *_, **__: (0, Mock())

    imas = Mock()
    imas.names = ['imas_3_34_0_ual_4_9_3']
    imas.ids = lambda *_, **__: ids
    imas.DBEntry = lambda *_, **__: entry

    imasdef = Mock()

    Parser = Mock()  # type: ignore

    logger.warning('Could not import IMAS:', exc_info=True)
