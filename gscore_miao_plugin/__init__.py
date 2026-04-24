"""GsCore 版 miao-plugin（简化移植版）"""

from gsuid_core.sv import Plugins

from .const import PLUGIN_NAME

Plugins(
    name=PLUGIN_NAME,
    force_prefix=["喵喵", "miao"],
    allow_empty_prefix=False,
)

try:
    from . import database as _database  # noqa: F401
    from . import status as _status  # noqa: F401
except Exception:
    pass

# handlers
from .handlers import admin as _admin  # noqa: F401,E402
from .handlers import changelog as _changelog  # noqa: F401,E402
from .handlers import features as _features  # noqa: F401,E402
from .handlers import help as _help  # noqa: F401,E402
from .handlers import login as _login  # noqa: F401,E402
