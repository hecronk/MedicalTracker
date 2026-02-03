# -*- coding: utf-8 -*-
"""Обработчики для статистики и быстрых действий без изменения БД."""
from datetime import datetime, date, timedelta
import pytz
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import get_cancel_keyboard
from bot.keyboards.reply import get_main_menu_keyboard
from database.base import async_session_maker
from services.medication_service import MedicationService
from database.repository import UserRepository, NotificationRepository
from database.models import NotificationLog, MedicationSchedule

router = Router()


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message, db_user):
    """Показать статистику на основе уведомлений."""
    try:
        async with async_session_maker() as session:
            notification_repo = NotificationRepository(session)
            
            # Получаем статистику за последние 30 дней
            thirty_days_ago = datetime.now(pytz.UTC).replace(tzinfo=None) - timedelta(days=30)
            
            # Получаем все логи уведомлений пользователя
            all_logs = await notification_repo.get_user_notification_logs(
                db_user.id, 
                thirty_days_ago
            )
            
            if not all_logs:
                await message.answer(
                    "📊 У вас пока нет статистики.\n\n"
                    "Используйте лекарства несколько дней, чтобы увидеть статистику!"
                )
                return
            
            # Считаем статистику
            sent_count = len([log for log in all_logs if log.status == 'sent'])
            failed_count = len([log for log in all_logs if log.status == 'failed'])
            total_count = len(all_logs)
            
            success_rate = (sent_count / total_count * 100) if total_count > 0 else 0
            
            text = (
                f"📊 Ваша статистика за последние 30 дней:\n\n"
                f"📈 Успешных уведомлений: {success_rate:.1f}%\n"
                f"✅ Отправлено: {sent_count}\n"
                f"❌ Ошибок: {failed_count}\n"
                f"📋 Всего: {total_count}\n\n"
                f"💡 Совет: Регулярно принимайте лекарства в одно время для лучшего эффекта!"
            )
            
            await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении статистики: {str(e)}")


@router.message(Command("history"))
@router.message(F.text == "📅 История")
async def cmd_history(message: Message, db_user):
    """Показать историю уведомлений."""
    try:
        async with async_session_maker() as session:
            notification_repo = NotificationRepository(session)
            
            # Получаем историю за последние 7 дней
            seven_days_ago = datetime.now(pytz.UTC).replace(tzinfo=None) - timedelta(days=7)
            
            logs = await notification_repo.get_user_notification_logs(
                db_user.id, 
                seven_days_ago
            )
            
            if not logs:
                await message.answer(
                    "📅 У вас пока нет истории уведомлений.\n\n"
                    "Начните принимать лекарства, и здесь появится история!"
                )
                return
        
        # Конвертируем время в часовой пояс пользователя
        user_tz = pytz.timezone(db_user.timezone)
        
        text = "📅 История уведомлений (последние 7 дней):\n\n"
        
        for log in sorted(logs, key=lambda x: x.scheduled_time, reverse=True)[:15]:
            log_time_user = log.scheduled_time.astimezone(user_tz)
            
            status_emoji = {
                'sent': '✅',
                'failed': '❌',
                'pending': '⏳'
            }.get(log.status, '❓')
            
            text += (
                f"{status_emoji} {log_time_user.strftime('%d.%m.%Y %H:%M')}\n"
                f"   📋 Уведомление #{log.id}\n"
                f"   🔄 Попыток: {log.attempts}\n"
            )
            
            if log.error_message:
                text += f"   ❌ Ошибка: {log.error_message}\n"
            
            text += "\n"
        
        await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении истории: {str(e)}")


@router.message(Command("quick_schedule"))
@router.message(F.text == "📅 Быстрый план")
async def cmd_quick_schedule(message: Message, db_user):
    """Быстрый план на сегодня без сложной логики."""
    try:
        async with async_session_maker() as session:
            service = MedicationService(session)
            medications = await service.get_user_medications(db_user.id, active_only=True)
        
        if not medications:
            await message.answer(
                "📋 У вас нет добавленных лекарств.\n\n"
                "Используйте /add_medication, чтобы добавить первое лекарство."
            )
            return
        
        # Получаем текущую дату в часовом поясе пользователя
        user_tz = pytz.timezone(db_user.timezone)
        now_utc = datetime.now(pytz.UTC)
        now_user_tz = now_utc.astimezone(user_tz)
        today = now_user_tz.date()
        
        text = f"📅 План на сегодня ({today.strftime('%d.%m.%Y')}):\n\n"
        
        today_meds = []
        for medication in medications:
            for schedule in medication.schedules:
                if _should_take_today(schedule, today):
                    time_str = schedule.time.strftime("%H:%M")
                    frequency_text = "каждый день" if schedule.frequency_type == 'daily' else f"через {schedule.interval_days} дня"
                    
                    today_meds.append(
                        f"⏰ {time_str} - 💊 {medication.name}\n"
                        f"   💊 Доза: {schedule.dose} препарата\n"
                        f"   📅 {frequency_text}\n"
                    )
        
        if not today_meds:
            text += "✅ Сегодня нет запланированных приемов!\n"
            text += "Отдыхайте! 😊"
        else:
            text += "\n".join(today_meds)
            text += "\n\n💡 Не забудьте принять лекарства вовремя!"
        
        await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


def _should_take_today(schedule, check_date):
    """Проверить нужно ли принимать лекарство в указанную дату."""
    # Проверяем дату окончания
    if schedule.end_date and check_date > schedule.end_date:
        return False
    
    # Проверяем дату начала
    if check_date < schedule.start_date:
        return False
    
    # Проверяем периодичность
    if schedule.frequency_type == 'daily':
        return True
    
    if schedule.frequency_type == 'interval' and schedule.interval_days:
        days_since_start = (check_date - schedule.start_date).days
        return days_since_start >= 0 and days_since_start % schedule.interval_days == 0
    
    return False
