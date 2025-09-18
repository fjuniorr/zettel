from .fzf import Note as FzfNote


class Note(FzfNote):
    def __repr__(self) -> str:
        return f"[{self.id}] {self.title}"
