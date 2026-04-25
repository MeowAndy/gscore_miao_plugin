"""GsCore 版 miao-plugin（简化移植版）"""

from gsuid_core.sv import Plugins

from .config import MiaoConfig
from .const import PLUGIN_NAME
from .startup import ensure_image_panel_defaults

ensure_image_panel_defaults()

_prefix = str(MiaoConfig.get_config("CommandPrefix").data or "喵喵").strip() or "喵喵"

Plugins(
    name=PLUGIN_NAME,
    force_prefix=[_prefix, "miao"],
    allow_empty_prefix=False,
)

try:
    from . import database as _database  # noqa: F401
    from . import status as _status  # noqa: F401
except Exception:
    pass

from .auto_sign import register_auto_daily_sign_job  # noqa: E402
# handlers
from .handlers import admin as _admin  # noqa: F401,E402
from .handlers import changelog as _changelog  # noqa: F401,E402
from .handlers import features as _features  # noqa: F401,E402
from .handlers import help as _help  # noqa: F401,E402
from .handlers import login as _login  # noqa: F401,E402

register_auto_daily_sign_job()
