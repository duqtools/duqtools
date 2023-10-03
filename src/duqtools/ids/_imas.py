# https://github.com/duqtools/duqtools/issues/27
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
imas_mocked = False

try:
    import os
    import xml.sax
    import xml.sax.handler

    import imas
    from imas import imasdef  # type: ignore

    IMAS_PREFIX = os.getenv('IMAS_PREFIX', '')
    PATH_IDSDEF = f'{IMAS_PREFIX}/include/IDSDef.xml'

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

if imas_mocked:
    logger.info('Could not import IMAS, using mocks instead.')
