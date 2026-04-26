"""GsCore 版 miao-plugin（简化移植版）"""

from gsuid_core.sv import Plugins

from .config import MiaoConfig
from .const import PLUGIN_NAME
from .startup import ensure_image_panel_defaults

ensure_image_panel_defaults()

_prefix = str(MiaoConfig.get_config("CommandPrefix").data or "喵喵").strip() or "喵喵"
_force_prefix = [_prefix, "miao", "MM"]

Plugins(
    name=PLUGIN_NAME,
    force_prefix=_force_prefix,
    allow_empty_prefix=False,
)

Plugins(
    name="gscore_miao-plugin",
    force_prefix=_force_prefix,
    allow_empty_prefix=False,
    force=True,
)

try:
    from . import database as _database  # noqa: F401
    from . import status as _status  # noqa: F401
except Exception:
    pass

from .auto_sign import register_auto_daily_sign_job  # noqa: E402
# handlers
from .handlers import admin as _admin  # noqa: F401,E402
from .handlers import calendar as _calendar  # noqa: F401,E402
from .handlers import changelog as _changelog  # noqa: F401,E402
from .handlers import features as _features  # noqa: F401,E402
from .handlers import gacha as _gacha  # noqa: F401,E402
from .handlers import help as _help  # noqa: F401,E402
from .handlers import login as _login  # noqa: F401,E402
from .handlers import miao_admin as _miao_admin  # noqa: F401,E402
from .handlers import stat as _stat  # noqa: F401,E402
from .handlers import wiki_extra as _wiki_extra  # noqa: F401,E402

register_auto_daily_sign_job()
