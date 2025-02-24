from typing import Any
from .research_progress_results import ResearchProgress

class OutputManager:
    def __init__(self):
        self.progress_lines = 4
        self.progress_area = []
        self.initialized = False
        print('\n' * self.progress_lines, end='')
        self.initialized = True

    def log(self, *args: Any) -> None:
        if self.initialized:
            print(f"\x1B[{self.progress_lines}A", end='')
            print('\x1B[0J', end='')
        print(*args)
        if self.initialized:
            self.draw_progress()

    def update_progress(self, progress: ResearchProgress) -> None:
        self.progress_area = [
            f"Depth:    [{self.get_progress_bar(progress.total_depth - progress.current_depth, progress.total_depth)}] {round((progress.total_depth - progress.current_depth) / progress.total_depth * 100)}%",
            f"Breadth:  [{self.get_progress_bar(progress.total_breadth - progress.current_breadth, progress.total_breadth)}] {round((progress.total_breadth - progress.current_breadth) / progress.total_breadth * 100)}%",
            f"Queries:  [{self.get_progress_bar(progress.completed_queries, progress.total_queries)}] {round(progress.completed_queries / progress.total_queries * 100)}%",
            f"Current:  {progress.current_query}" if progress.current_query else ''
        ]
        self.draw_progress()

    def get_progress_bar(self, value: int, total: int) -> str:
        width = min(30, 80 - 20)
        filled = round((width * value) / total)
        return '█' * filled + ' ' * (width - filled)

    def draw_progress(self) -> None:
        if not self.initialized or not self.progress_area:
            return
        terminal_height = 24
        print(f"\x1B[{terminal_height - self.progress_lines};1H", end='')
        print('\n'.join(self.progress_area), end='')
        print(f"\x1B[{terminal_height - self.progress_lines - 1};1H", end='')