class ProgressFile:
    def __init__(self, data, pbar):
        self.data = data
        self.pbar = pbar
        self.position = 0
        
    def read(self, size=-1):
        if size == -1:
            size = len(self.data) - self.position
        
        if self.position >= len(self.data):
            return b''
            
        chunk = self.data[self.position:self.position + size]
        self.position += len(chunk)
        self.pbar.update(len(chunk))
        return chunk