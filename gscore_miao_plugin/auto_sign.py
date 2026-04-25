from __future__ import annotations

import asyncio
from datetime import datetime

from gsuid_core.aps import scheduler
from gsuid_core.logger import logger
from gsuid_core.subscribe import gs_subscribe

from .config import MiaoConfig
from .handlers.login import run_daily_sign_for_cfg
from .settings import merge_user_cfg
from .store import get_all_user_cfg

_JOB_ID = "gscore_miao_auto_daily_sign"
SIGN_RESULT_SUBSCRIBE = "喵喵签到结果"
_SIGN_LOCK = asyncio.Lock()
_LAST_RUN_DATE = ""


def _sign_time() -> tuple[int, int]:
    raw = MiaoConfig.get_config("AutoDailySignTime").data or ["8", "0"]
    try:
        hour = int(raw[0]) if len(raw) > 0 else 8
        minute = int(raw[1]) if len(raw) > 1 else 0
    except Exception:
        hour, minute = 8, 0
    return max(0, min(23, hour)), max(0, min(59, minute))


async def auto_daily_sign_task(sign_all: bool = False) -> str:
    if not sign_all and not MiaoConfig.get_config("EnableAutoDailySign").data:
        return "自动签到全局开关已关闭"
    if _SIGN_LOCK.locked():
        return "签到任务正在执行中，已跳过本次任务"

    async with _SIGN_LOCK:
        all_cfg = await get_all_user_cfg()
        total = 0
        success = 0
        failed = 0
        skipped = 0
        messages: list[str] = []

        for key, raw_cfg in all_cfg.items():
            if not isinstance(raw_cfg, dict):
                continue
            cfg = merge_user_cfg(raw_cfg)
            if not sign_all and not cfg.get("auto_daily_sign"):
                continue
            total += 1
            cookie = str(cfg.get("mys_cookie") or "")
            if not cookie:
                skipped += 1
                continue
            try:
                sections, errors = await run_daily_sign_for_cfg(cfg)
                if sections:
                    success += 1
                if errors:
                    failed += 1
                user_key = str(key).split(":", 1)[-1]
                if errors:
                    messages.append(f"{user_key}: " + "；".join(errors[:3]))
                await asyncio.sleep(1)
            except Exception as e:
                failed += 1
                user_key = str(key).split(":", 1)[-1]
                messages.append(f"{user_key}: {e}")

        title = "喵喵全部签到" if sign_all else "喵喵自动签到"
        total_label = "账号" if sign_all else "开启"
        summary = f"[{title}] 执行完成：{total_label} {total} 个，成功 {success} 个，失败 {failed} 个，跳过 {skipped} 个"
        if messages:
            summary += "\n" + "\n".join(messages[:10])
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
    for sub in subscribes:
        try:
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
