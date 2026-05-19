export interface RetrievalFilters {
    classId?: number;
    subjectId?: number;
    chapterId?: number;
    topicId?: number;
    className?: string;
    subject?: string;
    chapter?: string;
}
export interface RetrievedChunk {
    id: number;
    classId: number | null;
    subjectId: number | null;
    chapterId: number | null;
    topicId: number | null;
    className: string | null;
    subject: string | null;
    chapter: string | null;
    topic: string | null;
    content: string;
    sourceFile: string;
    page: number;
    semanticScore: number;
    keywordScore: number;
    score: number;
}
export interface RetrievalOptions extends RetrievalFilters {
    topK?: number;
    minimumSimilarity?: number;
    minimumScore?: number;
    semanticWeight?: number;
    keywordWeight?: number;
    disableCache?: boolean;
}
export declare function retrieveRelevantChunks(question: string, options?: RetrievalOptions): Promise<RetrievedChunk[]>;
