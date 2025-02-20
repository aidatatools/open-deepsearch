class TextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError('Cannot have chunkOverlap >= chunkSize')

    def split_text(self, text: str) -> list[str]:
        raise NotImplementedError

    def create_documents(self, texts: list[str]) -> list[str]:
        documents = []
        for text in texts:
            documents.extend(self.split_text(text))
        return documents

    def split_documents(self, documents: list[str]) -> list[str]:
        return self.create_documents(documents)

    def join_docs(self, docs: list[str], separator: str) -> str:
        text = separator.join(docs).strip()
        return text if text else None

    def merge_splits(self, splits: list[str], separator: str) -> list[str]:
        docs = []
        current_doc = []
        total = 0
        for d in splits:
            _len = len(d)
            if total + _len >= self.chunk_size:
                if total > self.chunk_size:
                    print(f'Created a chunk of size {total}, which is longer than the specified {self.chunk_size}')
                if current_doc:
                    doc = self.join_docs(current_doc, separator)
                    if doc:
                        docs.append(doc)
                    while total > self.chunk_overlap or (total + _len > self.chunk_size and total > 0):
                        total -= len(current_doc[0])
                        current_doc.pop(0)
            current_doc.append(d)
            total += _len
        doc = self.join_docs(current_doc, separator)
        if doc:
            docs.append(doc)
        return docs

class RecursiveCharacterTextSplitter(TextSplitter):
    def __init__(self, chunk_size=1000, chunk_overlap=200, separators=None):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or ['\n\n', '\n', '.', ',', '>', '<', ' ', '']

    def split_text(self, text: str) -> list[str]:
        final_chunks = []

        separator = self.separators[-1]
        for s in self.separators:
            if s == '' or s in text:
                separator = s
                break

        splits = text.split(separator) if separator else list(text)

        good_splits = []
        for s in splits:
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged_text = self.merge_splits(good_splits, separator)
                    final_chunks.extend(merged_text)
                    good_splits = []
                final_chunks.extend(self.split_text(s))
        if good_splits:
            merged_text = self.merge_splits(good_splits, separator)
            final_chunks.extend(merged_text)
        return final_chunks