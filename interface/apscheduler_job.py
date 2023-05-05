from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_REMOVED
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

init_scheduler_options = {
    'jobstores': {
        'default': SQLAlchemyJobStore(url='sqlite:///db.sqlite3')
        # 'default': {
        #     'type': 'sqlalchemy',
        #     'url': 'mysql+pymysql://root:syl123456@127.0.0.1:3306/interface?charset=utf8'
        # }
    },
    'executors': {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(5)
    },
    'job_defaults': {
        'coalesce': True,
        'misfire_grace_time': None,
        'max_instances': 10,
    },
    'timezone': 'Asia/Shanghai'
}


class ApschedulerJob:
    def __init__(self):
        self.scheduler = BackgroundScheduler(**init_scheduler_options)
        self.scheduler.add_listener(self.my_listener,
                                    EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_REMOVED)
        self.scheduler.start()

    def add_job(self, *args, **kwargs):
        self.scheduler.add_job(*args, **kwargs)
        if not self.scheduler.running:
            self.scheduler.start()

    def get_scheduler(self):
        return self.scheduler

    def remove_job(self, job_id):
        # 移除定时任务
        return self.scheduler.remove_job(job_id)

    def modify_job(self, job_id, **changes):
        # 修改任务当中除了id的任何属性
        return self.scheduler.modify_job(job_id, **changes)

    def reschedule_job(self, job_id, trigger=None, **trigger_args):
        # 重新调度任务（就是改变触发器）
        return self.scheduler.reschedule_job(job_id, trigger=trigger, **trigger_args)

    def my_listener(self, event):
        # if event.exception:
        print(f"定时任务初始状态：{self.scheduler.running}")
        print(event)
        print("监听到特定信号")
        # print(self.scheduler.print_jobs())
        if not self.scheduler.get_jobs():
            print(f"定时任务列表空：{self.scheduler.get_jobs()}，关闭服务")
            if self.scheduler.running:
                try:
                    self.scheduler.shutdown()
                except Exception as e:
                    print(e.__str__())
        print(f"定时任务服务：{self.scheduler.running}")
        # else:
        #     print(event)
        #     print("任务正常")
