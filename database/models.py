"""Модели базы данных."""
from datetime import datetime, date, time
from sqlalchemy import BigInteger, String, Integer, Boolean, Text, Time, Date, ForeignKey, TIMESTAMP, text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class User(Base):
    """Модель пользователя."""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user_id
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default='UTC', server_default='UTC')
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    medications: Mapped[list['Medication']] = relationship(back_populates='user', cascade='all, delete-orphan')


class Medication(Base):
    """Модель лекарства."""
    __tablename__ = 'medications'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true')
    
    # Relationships
    user: Mapped['User'] = relationship(back_populates='medications')
    schedules: Mapped[list['MedicationSchedule']] = relationship(back_populates='medication', cascade='all, delete-orphan')


class MedicationSchedule(Base):
    """Модель расписания приема лекарства."""
    __tablename__ = 'medication_schedules'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medication_id: Mapped[int] = mapped_column(Integer, ForeignKey('medications.id', ondelete='CASCADE'), nullable=False)
    frequency_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'daily' или 'interval'
    interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Для 'interval' типа
    dose: Mapped[float] = mapped_column(Float, nullable=False)  # Количество таблеток
    time: Mapped[time] = mapped_column(Time, nullable=False)  # Время приема
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # NULL = бессрочно
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    medication: Mapped['Medication'] = relationship(back_populates='schedules')
    notification_logs: Mapped[list['NotificationLog']] = relationship(back_populates='schedule', cascade='all, delete-orphan')


class NotificationLog(Base):
    """Модель лога уведомления."""
    __tablename__ = 'notification_logs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_id: Mapped[int] = mapped_column(Integer, ForeignKey('medication_schedules.id', ondelete='CASCADE'), nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='pending')  # 'pending', 'sent', 'failed', 'delivered'
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # ID сообщения в Telegram
    
    # Relationships
    schedule: Mapped['MedicationSchedule'] = relationship(back_populates='notification_logs')
    retries: Mapped[list['NotificationRetry']] = relationship(back_populates='notification_log', cascade='all, delete-orphan')


class NotificationRetry(Base):
    """Модель повторной попытки отправки уведомления."""
    __tablename__ = 'notification_retries'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_log_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_logs.id', ondelete='CASCADE'), nullable=False)
    retry_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='pending')  # 'pending', 'completed', 'failed'
    
    # Relationships
    notification_log: Mapped['NotificationLog'] = relationship(back_populates='retries')

