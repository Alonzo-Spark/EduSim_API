export interface TextbookMetadata {
    className: string | null;
    subject: string | null;
    chapter: string | null;
    topic: string | null;
}
export interface SemanticChunk extends TextbookMetadata {
    content: string;
    sourceFile: string;
    page: number;
    fingerprint: string;
}
export declare function deriveMetadataFromPath(relativePath: string): TextbookMetadata;
export declare function chunkTextbookDocument(input: {
    rawText: string;
    sourceFile: string;
    metadata: TextbookMetadata;
}): SemanticChunk[];
