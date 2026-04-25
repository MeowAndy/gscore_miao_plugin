from __future__ import annotations

import asyncio
from datetime import datetime

from gsuid_core.aps import scheduler
from gsuid_core.logger import logger
from gsuid_core.subscribe import gs_subscribe

from .config import MiaoConfig
from .handlers.login import get_sign_uids_for_cfg, run_daily_sign_for_cfg
from .mys_service import fetch_starrail_roles
from .settings import merge_user_cfg
from .store import get_all_user_cfg, get_group_bot_self_id

_JOB_ID = "MiHoYoUID_auto_daily_sign"
SIGN_RESULT_SUBSCRIBE = "喵喵签到结果"
_SIGN_LOCK = asyncio.Lock()
_LAST_RUN_DATE = ""


def _empty_stat() -> dict[str, int]:
    return {"total": 0, "success": 0, "failed": 0, "skipped": 0}


def _sign_time() -> tuple[int, int]:
    raw = MiaoConfig.get_config("AutoDailySignTime").data or ["0", "30"]
    try:
        hour = int(raw[0]) if len(raw) > 0 else 0
        minute = int(raw[1]) if len(raw) > 1 else 30
    except Exception:
        hour, minute = 0, 30
    return max(0, min(23, hour)), max(0, min(59, minute))


async def auto_daily_sign_task(sign_all: bool = False) -> str:
    if not sign_all and not MiaoConfig.get_config("EnableAutoDailySign").data:
        return "自动签到全局开关已关闭"
    if _SIGN_LOCK.locked():
        return "签到任务正在执行中，已跳过本次任务"

    async with _SIGN_LOCK:
        all_cfg = await get_all_user_cfg()
        stats = {"原神": _empty_stat(), "崩铁": _empty_stat()}
        error_messages: list[str] = []

        for key, raw_cfg in all_cfg.items():
            if str(key).startswith("_"):
                continue
            if not isinstance(raw_cfg, dict):
                continue
            cfg = merge_user_cfg(raw_cfg)
            if not sign_all and not cfg.get("auto_daily_sign"):
                continue
            user_key = str(key).split(":", 1)[-1]
            cookie = str(cfg.get("mys_cookie") or "")
            if cookie and not cfg.get("mys_sr_roles"):
                try:
                    cfg = {**cfg, "mys_sr_roles": await fetch_starrail_roles(cookie)}
                except Exception:
                    pass
            gs_uids, sr_uids = get_sign_uids_for_cfg(cfg)
            stats["原神"]["total"] += len(gs_uids)
            stats["崩铁"]["total"] += len(sr_uids)
            if not cookie:
                for game_name, uids in (("原神", gs_uids), ("崩铁", sr_uids)):
                    stats[game_name]["skipped"] += len(uids)
                continue
            if not gs_uids and not sr_uids:
                continue
            try:
                sections, errors = await run_daily_sign_for_cfg(cfg)
                gs_done = sum(1 for section in sections if section.startswith("【原神签到】"))
                sr_done = sum(1 for section in sections if section.startswith("【崩铁签到】"))
                gs_failed = sum(1 for error in errors if error.startswith("原神 "))
                sr_failed = sum(1 for error in errors if error.startswith("崩铁 "))
                stats["原神"]["success"] += gs_done
                stats["崩铁"]["success"] += sr_done
                stats["原神"]["failed"] += gs_failed
                stats["崩铁"]["failed"] += sr_failed
                stats["原神"]["skipped"] += max(0, len(gs_uids) - gs_done - gs_failed)
                stats["崩铁"]["skipped"] += max(0, len(sr_uids) - sr_done - sr_failed)
                if errors:
                    error_messages.append(f"{user_key}: " + "；".join(errors[:3]))
                await asyncio.sleep(1)
            except Exception as e:
                stats["原神"]["failed"] += len(gs_uids)
                stats["崩铁"]["failed"] += len(sr_uids)
                error_messages.append(f"{user_key}: {e}")

        title = "喵喵全部签到" if sign_all else "喵喵自动签到"
        summary_lines = [
            f"✅ [{title}] 执行完成：",
            f"🎮 原神账号 {stats['原神']['total']} 个",
            f"✅ 成功 {stats['原神']['success']} 个",
            f"❌ 失败 {stats['原神']['failed']} 个",
            f"⏭️ 跳过 {stats['原神']['skipped']} 个",
            f"🚆 崩铁账号 {stats['崩铁']['total']} 个",
            f"✅ 成功 {stats['崩铁']['success']} 个",
            f"❌ 失败 {stats['崩铁']['failed']} 个",
            f"⏭️ 跳过 {stats['崩铁']['skipped']} 个",
        ]
        if error_messages:
            summary_lines.append("⚠️ 失败详情：" + "；".join(error_messages[:5]))
        summary = "\n".join(summary_lines)
        logger.info(summary)
        return summary


async def push_sign_result(summary: str) -> None:
    try:
        subscribes = await gs_subscribe.get_subscribe(SIGN_RESULT_SUBSCRIBE)
    except Exception as e:
        logger.exception(f"[喵喵签到结果] 获取订阅失败：{e}")
        return
    if not subscribes:
        return
    logger.info(f"[喵喵签到结果] 推送订阅统计：{summary}")
    private_report = MiaoConfig.get_config("PrivateSignReport").data
    group_report = MiaoConfig.get_config("GroupSignReport").data
    for sub in subscribes:
        try:
            user_type = str(getattr(sub, "user_type", ""))
            if user_type == "direct" and not private_report:
                continue
            if user_type == "group":
                if not group_report:
                    continue
                group_id = str(getattr(sub, "group_id", "") or "")
                latest_bot = await get_group_bot_self_id(group_id)
                if latest_bot and latest_bot != getattr(sub, "bot_self_id", ""):
                    logger.info(
                        f"[喵喵签到结果] 更新群订阅 bot_self_id: "
                        f"{getattr(sub, 'bot_self_id', '')} -> {latest_bot}"
                    )
                    sub.bot_self_id = latest_bot
            await sub.send(summary)
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.exception(f"[喵喵签到结果] 推送失败：{e}")


async def _auto_daily_sign_tick() -> None:
    global _LAST_RUN_DATE
    if not MiaoConfig.get_config("EnableAutoDailySign").data:
        return
    hour, minute = _sign_time()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    if now.hour != hour or now.minute != minute or _LAST_RUN_DATE == today:
        return
    _LAST_RUN_DATE = today
    try:
        summary = await auto_daily_sign_task()
        await push_sign_result(summary)
    except Exception as e:
        logger.exception(f"[喵喵自动签到] 定时任务异常：{e}")


def register_auto_daily_sign_job() -> None:
    try:
        if scheduler.get_job(_JOB_ID):
            scheduler.remove_job(_JOB_ID)
    except Exception:
        pass
    scheduler.add_job(
        _auto_daily_sign_tick,
        "cron",
        id=_JOB_ID,
        second=0,
        replace_existing=True,
    )
    hour, minute = _sign_time()
    logger.info(f"[喵喵自动签到] 已注册每日 {hour:02d}:{minute:02d} 执行")
