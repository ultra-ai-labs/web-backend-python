import time
import threading


class Snowflake:
    def __init__(self, worker_id, datacenter_id, sequence=0):
        # 定义 Snowflake 结构的各个位数
        self.worker_id_bits = 5
        self.datacenter_id_bits = 5
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)
        self.sequence_bits = 12

        # 定义 Snowflake 结构中的偏移量
        self.worker_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_left_shift = self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits
        self.sequence_mask = -1 ^ (-1 << self.sequence_bits)

        # 初始化 Snowflake 参数
        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = sequence
        self.last_timestamp = -1
        self.lock = threading.Lock()

        # 检查 worker_id 和 datacenter_id 是否在合法范围内
        if self.worker_id > self.max_worker_id or self.datacenter_id > self.max_datacenter_id:
            raise ValueError("worker_id 或 datacenter_id 超出范围")

    def _current_timestamp(self):
        return int(time.time() * 1000)

    def _til_next_millis(self, last_timestamp):
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    def generate_id(self):
        with self.lock:
            timestamp = self._current_timestamp()

            if timestamp < self.last_timestamp:
                raise ValueError("时钟回退，拒绝生成 ID")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.sequence_mask
                if self.sequence == 0:
                    timestamp = self._til_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # 生成 Snowflake ID
            snowflake_id = ((timestamp - 1609459200000) << self.timestamp_left_shift) | \
                           (self.datacenter_id << self.datacenter_id_shift) | \
                           (self.worker_id << self.worker_id_shift) | \
                           self.sequence

            return snowflake_id


# 封装全局变量
context = {'generator': Snowflake(0, 1)}


# 封装函数
def next_id():
    return str(context['generator'].generate_id())
