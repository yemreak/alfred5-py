class WorkflowError(Exception):
    """Alfred workflow exception that shows in Alfred results"""

    title: str
    subtitle: str

    def __init__(self, title: str, subtitle: str):
        self.title = title
        self.subtitle = subtitle
