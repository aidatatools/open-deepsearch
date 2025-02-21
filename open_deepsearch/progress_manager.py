from .research_progress_results import ResearchProgress

class ProgressManager:
    def __init__(self):
        self.last_progress = None
        self.progress_lines = 4
        self.initialized = False
        print('\n' * self.progress_lines, end='')

    def draw_progress_bar(self, label: str, value: int, total: int, char: str = '=') -> str:
        width = min(30, 80 - 20)
        percent = (value / total) * 100
        filled = round((width * percent) / 100)
        empty = width - filled
        return f"{label} [{char * filled}{' ' * empty}] {round(percent)}%"

    def update_progress(self, progress: ResearchProgress) -> None:
        self.last_progress = progress
        terminal_height = 24
        progress_start = terminal_height - self.progress_lines
        print(f"\x1B[{progress_start};1H\x1B[0J", end='')

        lines = [
            self.draw_progress_bar('Depth:   ', progress.total_depth - progress.current_depth, progress.total_depth, '█'),
            self.draw_progress_bar('Breadth: ', progress.total_breadth - progress.current_breadth, progress.total_breadth, '█'),
            self.draw_progress_bar('Queries: ', progress.completed_queries, progress.total_queries, '█')
        ]

        if progress.current_query:
            lines.append(f"Current:  {progress.current_query}")

        print('\n'.join(lines), end='\n')
        print(f"\x1B[{self.progress_lines}A", end='')

    def stop(self) -> None:
        print(f"\x1B[{self.progress_lines}B\n", end='')