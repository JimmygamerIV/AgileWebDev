import sys
import os

# 获取当前脚本的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 找到上一级目录
parent_dir = os.path.dirname(current_dir)
# 将上一级目录加入到 sys.path 中
sys.path.append(parent_dir)

# 现在就可以正常导入了
from app import is_event_currently_running, events_overlap, get_primary_poi_id
from database import init_db
from datetime import datetime
from models import Event,User

class DummyEvent:
    def __init__(self, date, start_time, end_time, location=""):
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.location = location


def test_is_event_currently_running_true():
    event = DummyEvent("2026-04-26", "10:00", "12:00")
    now = datetime.strptime("2026-04-26 11:00", "%Y-%m-%d %H:%M")

    assert is_event_currently_running(event, now) is True


def test_is_event_currently_running_false():
    event = DummyEvent("2026-04-26", "10:00", "12:00")
    now = datetime.strptime("2026-04-26 13:00", "%Y-%m-%d %H:%M")

    assert is_event_currently_running(event, now) is False


def test_events_overlap_true():
    e1 = DummyEvent("2026-04-26", "10:00", "12:00")
    e2 = DummyEvent("2026-04-26", "11:00", "13:00")

    assert events_overlap(e1, e2) is True


def test_events_overlap_false():
    e1 = DummyEvent("2026-04-26", "10:00", "11:00")
    e2 = DummyEvent("2026-04-26", "11:00", "12:00")

    assert events_overlap(e1, e2) is False


def test_get_primary_poi_id():
    assert get_primary_poi_id("A101|B202") is None