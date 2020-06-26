import io


class RunnerOutputBuffer:
    def __init__(self):
        self.buffer = io.StringIO()

    def __getattr__(self, item):
        return getattr(self.buffer, item)
