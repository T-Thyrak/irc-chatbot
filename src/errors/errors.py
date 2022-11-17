class ValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.msg = message
        
    def message(self):
        return self.msg