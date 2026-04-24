from __future__ import annotations

from typing import Optional

from gsuid_core.utils.database.base_models import BaseIDModel
from gsuid_core.webconsole.mount_app import GsAdminModel, PageSchema, site
from sqlmodel import Field


class MiaoUserConfig(BaseIDModel, table=True):
    """用户级配置（简化版）"""

    __tablename__ = "GsCoreMiaoUserConfig"
    __table_args__ = {"extend_existing": True}

    user_id: str = Field(default="", title="用户ID")
    bot_id: str = Field(default="", title="机器人ID")
    uid: str = Field(default="", title="绑定UID")
    panel_server: str = Field(default="auto", title="面板服务")
    custom_splash: bool = Field(default=True, title="自定义面板图")
    team_calc: bool = Field(default=False, title="组队伤害计算")
    show_star: bool = Field(default=False, title="显示星级")
    comma_group: int = Field(default=3, title="数字分组")


@site.register_admin
class MiaoUserConfigAdmin(GsAdminModel):
    pk_name = "id"
    page_schema = PageSchema(
        label="GsCore Miao 用户配置",
        icon="fa fa-sliders",
    )
    model = MiaoUserConfig


class MiaoUserHistory(BaseIDModel, table=True):
    """用户历史操作"""

    __tablename__ = "GsCoreMiaoUserHistory"
    __table_args__ = {"extend_existing": True}

    user_id: str = Field(default="", title="用户ID")
    bot_id: str = Field(default="", title="机器人ID")
    action: str = Field(default="", title="操作")
    detail: str = Field(default="", title="详情")
    ts: int = Field(default=0, title="时间戳")


@site.register_admin
class MiaoUserHistoryAdmin(GsAdminModel):
    pk_name = "id"
    page_schema = PageSchema(
        label="GsCore Miao 历史记录",
        icon="fa fa-history",
    )
    model = MiaoUserHistory
