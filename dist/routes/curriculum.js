import { Router } from "express";
import { HttpError } from "../middleware/error.js";
import { getChapters, getClasses, getSubjects, getTopics } from "../services/curriculum.js";
const curriculumRouter = Router();
function parseId(raw, field) {
    const parsed = Number(raw);
    if (!Number.isInteger(parsed) || parsed <= 0) {
        throw new HttpError(`${field} must be a positive integer`, 400);
    }
    return parsed;
}
curriculumRouter.get("/classes", async (_request, response, next) => {
    try {
        const classes = await getClasses();
        response.json({ classes });
    }
    catch (error) {
        next(error);
    }
});
curriculumRouter.get("/subjects/:classId", async (request, response, next) => {
    try {
        const classId = parseId(request.params.classId, "classId");
        const subjects = await getSubjects(classId);
        response.json({ subjects });
    }
    catch (error) {
        next(error);
    }
});
curriculumRouter.get("/chapters/:subjectId", async (request, response, next) => {
    try {
        const subjectId = parseId(request.params.subjectId, "subjectId");
        const chapters = await getChapters(subjectId);
        response.json({ chapters });
    }
    catch (error) {
        next(error);
    }
});
curriculumRouter.get("/topics/:chapterId", async (request, response, next) => {
    try {
        const chapterId = parseId(request.params.chapterId, "chapterId");
        const topics = await getTopics(chapterId);
        response.json({ topics });
    }
    catch (error) {
        next(error);
    }
});
export { curriculumRouter };
//# sourceMappingURL=curriculum.js.map