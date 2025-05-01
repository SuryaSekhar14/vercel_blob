'''
This module provides a file object wrapper class that tracks upload progress.

The ProgressFile class processes byte data like a file object while displaying upload progress
through a tqdm progress bar with enhanced visual feedback.
'''

from vercel_blob.errors import InvalidColorError

def _hex_to_ansi(hex_color: str) -> str:
    """
    Convert a hex color code to ANSI escape code.
    
    Args:
        hex_color (str): Hex color code (e.g. '#FF0000' or 'FF0000')
        
    Returns:
        str: ANSI escape code for the color
        
    Raises:
        InvalidColorError: If the hex color code is invalid
    """
    hex_color = hex_color.lstrip('#')

    if not hex_color:
        raise InvalidColorError("Empty color code provided")

    if len(hex_color) != 6:
        raise InvalidColorError(f"Invalid hex color length: {hex_color}. Must be 6 characters.")

    try:
        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    except ValueError as e:
        raise InvalidColorError(f"Invalid hex color code: {hex_color}. {str(e)}") from e

    # Convert RGB to ANSI 256 color code
    # Using the formula from https://gist.github.com/MicahElliott/719710
    if r == g == b:
        if r < 8:
            ansi_code = 16
        elif r > 248:
            ansi_code = 231
        else:
            ansi_code = round(((r - 8) / 247) * 24) + 232
    else:
        ansi_code = 16 + (36 * round(r / 255 * 5)) + (6 * round(g / 255 * 5)) + round(b / 255 * 5)

    return f"\033[38;5;{ansi_code}m"

class ColorConfig:
    """
    Configuration class for progress bar colors.
    
    Attributes:
        desc (str): Color for the description text (e.g., "Uploading")
        bar (str): Color for the progress bar itself
        text (str): Color for the progress text (percentage, speed, etc.)
    """
    def __init__(self, desc="\033[1;32m", bar="\033[1;36m", text="\033[1;34m"):
        self.desc = desc
        self.bar = bar
        self.text = text

    def reset(self):
        """Reset all colors to default values."""
        self.desc = "\033[1;32m"  # Bright green
        self.bar = "\033[1;36m"   # Bright cyan
        self.text = "\033[1;34m"  # Bright blue

    def set_colors(self, desc=None, bar=None, text=None):
        """
        Set custom colors for the progress bar.
        
        Args:
            desc (str, optional): Color code for description (hex or ANSI)
            bar (str, optional): Color code for progress bar (hex or ANSI)
            text (str, optional): Color code for progress text (hex or ANSI)
            
        Raises:
            InvalidColorError: If any of the provided color codes are invalid
        """
        if desc is not None:
            self.desc = _hex_to_ansi(desc) if desc.startswith('#') else desc
        if bar is not None:
            self.bar = _hex_to_ansi(bar) if bar.startswith('#') else bar
        if text is not None:
            self.text = _hex_to_ansi(text) if text.startswith('#') else text

_default_colors = ColorConfig()

class ProgressFile:
    """
    A file object wrapper class that tracks upload progress with enhanced visual feedback.

    This class processes byte data like a file object while displaying upload progress
    through a tqdm progress bar. It provides smooth progress tracking and handles
    edge cases gracefully.

    Attributes:
        data (bytes): The byte data to be uploaded
        pbar (tqdm): The tqdm progress bar object for displaying progress
        position (int): The current position in the data being read
        total_size (int): The total size of the data to be processed
        colors (ColorConfig): Color configuration for the progress bar
    """

    def __init__(self, data, pbar, colors=None):
        """
        Initialize a ProgressFile object.

        Args:
            data (bytes): The byte data to be uploaded
            pbar (tqdm): The tqdm progress bar object for displaying progress
            colors (ColorConfig, optional): Custom color configuration. 
                If None, uses default colors.

        Raises:
            TypeError: If data is not bytes or pbar is not a tqdm instance
        """
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if not hasattr(pbar, 'update'):
            raise TypeError("pbar must be a tqdm instance")

        self.data = data
        self.pbar = pbar
        self.position = 0
        self.total_size = len(data)
        self.colors = colors if colors is not None else _default_colors

    def read(self, size=-1):
        """
        Read a portion of the data and update the progress bar.

        Args:
            size (int, optional): The number of bytes to read. 
                Defaults to -1, which reads all remaining data.

        Returns:
            bytes: The chunk of data read

        Note:
            The progress bar will be updated with the actual number of bytes read,
            ensuring accurate progress tracking even if the requested size is larger
            than the remaining data.
        """
        if size == -1:
            size = self.total_size - self.position

        if self.position >= self.total_size:
            return b""

        chunk = self.data[self.position : self.position + size]
        actual_size = len(chunk)
        self.position += actual_size
        self.pbar.update(actual_size)
        return chunk

__all__ = ["ProgressFile", "_default_colors"]
