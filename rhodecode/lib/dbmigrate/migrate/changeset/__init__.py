"""
   This module extends SQLAlchemy and provides additional DDL [#]_
   support.

   .. [#] SQL Data Definition Language
"""
import re
import warnings

import sqlalchemy
from sqlalchemy import __version__ as _sa_version

warnings.simplefilter('always', DeprecationWarning)

_sa_version = tuple(int(re.match("\d+", x).group(0)) for x in _sa_version.split("."))
SQLA_07 = _sa_version >= (0, 7)
SQLA_08 = _sa_version >= (0, 8)
SQLA_09 = _sa_version >= (0, 9)
SQLA_10 = _sa_version >= (1, 0)

del re
del _sa_version

from rhodecode.lib.dbmigrate.migrate.changeset.schema import *
from rhodecode.lib.dbmigrate.migrate.changeset.constraint import *

sqlalchemy.schema.Table.__bases__ += (ChangesetTable, )
sqlalchemy.schema.Column.__bases__ += (ChangesetColumn, )
sqlalchemy.schema.Index.__bases__ += (ChangesetIndex, )

sqlalchemy.schema.DefaultClause.__bases__ += (ChangesetDefaultClause, )
