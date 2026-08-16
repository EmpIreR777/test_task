from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from src.tsk.broker import mk_broker

mk_scheduler = TaskiqScheduler(mk_broker, sources=[LabelScheduleSource(mk_broker)])
