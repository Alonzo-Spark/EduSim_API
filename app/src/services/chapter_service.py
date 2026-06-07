class ChapterService:
    @staticmethod
    def match_chapter(subject: str, chapter: str, topic: str) -> str:
        # In a more advanced implementation, this uses fuzzy matching against the DB.
        # For now, we rely on the RagService's internal filtering for chapter name inclusion.
        return chapter
