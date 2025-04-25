'''
This module provides a file object wrapper class that tracks upload progress.

The ProgressFile class processes byte data like a file object while displaying upload progress
through a tqdm progress bar.
'''

class ProgressFile:
    """
    A file object wrapper class that tracks upload progress.

    This class processes byte data like a file object while displaying upload progress
    through a tqdm progress bar.

    Attributes:
        data (bytes): The byte data to be uploaded
        pbar (tqdm): The tqdm progress bar object for displaying progress
        position (int): The current position in the data being read
    """

    def __init__(self, data, pbar):
        """
        Initialize a ProgressFile object.

        Args:
            data (bytes): The byte data to be uploaded
            pbar (tqdm): The tqdm progress bar object for displaying progress
        """
        self.data = data
        self.pbar = pbar
        self.position = 0

    def read(self, size=-1):
        """
        Read a portion of the data and update the progress bar.

        Args:
            size (int, optional): The number of bytes to read. 
                Defaults to -1, which reads all remaining data.

        Returns:
            bytes: The chunk of data read
        """
        if size == -1:
            size = len(self.data) - self.position

        if self.position >= len(self.data):
            return b""

        chunk = self.data[self.position : self.position + size]
        self.position += len(chunk)
        self.pbar.update(len(chunk))
        return chunk
