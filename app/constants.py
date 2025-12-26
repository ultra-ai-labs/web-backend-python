class TaskStepStatus:
    INITIAL = 1
    RUNNING = 2
    FINISH = 3
    DELETE = 4
    STOPPED = 5

    STATUS_DICT = {
        INITIAL: "initial",
        RUNNING: "running",
        FINISH: "finish",
        DELETE: "delete",
        STOPPED: "stopped"
    }

    @classmethod
    def get_status_string(cls, status_number):
        return cls.STATUS_DICT.get(status_number, "unknown")

    @classmethod
    def get_status_number(cls, status_string):
        for number, string in cls.STATUS_DICT.items():
            if string == status_string:
                return number
        return None


class TaskStepType:
    CRAWLER = 1
    ANALYSIS = 2
    MARKETING = 3


# status_number = TaskStepStatus.RUNNING
# status_string = TaskStepStatus.get_status_string(status_number)
# print(status_number)
# print(status_string)
