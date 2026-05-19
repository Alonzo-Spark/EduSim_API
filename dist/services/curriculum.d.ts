import type { PoolClient } from "pg";
export interface CurriculumNameInput {
    className?: string | null;
    subject?: string | null;
    chapter?: string | null;
    topic?: string | null;
}
export interface CurriculumIds {
    classId: number | null;
    subjectId: number | null;
    chapterId: number | null;
    topicId: number | null;
}
export declare function resolveOrCreateCurriculumIds(client: PoolClient, input: CurriculumNameInput): Promise<CurriculumIds>;
export declare function getClasses(): Promise<Array<{
    id: number;
    name: string;
    sortOrder: number;
}>>;
export declare function getSubjects(classId: number): Promise<Array<{
    id: number;
    name: string;
    sortOrder: number;
}>>;
export declare function getChapters(subjectId: number): Promise<Array<{
    id: number;
    name: string;
    sortOrder: number;
}>>;
export declare function getTopics(chapterId: number): Promise<Array<{
    id: number;
    name: string;
    sortOrder: number;
}>>;
