# Sequential Benchmark Report - Gemma-E4B

Completed evaluation across **10 standardized educational questions**.

### Aggregate Metrics:
* **Success Rate**: 100.00% (10/10)
* **Average Latency**: 18276.30ms
* **Total Estimated Cost**: $0.02347600
* **Average Accuracy**: 2.20/10
* **Average Quality**: 7.50/10
* **Average Educational Value**: 3.10/10

### Question-by-Question Evaluation Table:

| # | Prompt Topic | Success | Latency | Accuracy | Quality | Educational | Cost | Rationale / Error |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | **electricity** (easy) | ✅ Success | 20010ms | **2** | **8** | **3** | $0.00246 | The response completely missed the required concepts and formula for Ohm's law, instead focusing on a new rendering system for an AI Tutor, resulting in low accuracy and educational scores, despite its high quality score for structure and readability. |
| 2 | **electricity_circuits** (medium) | ✅ Success | 21230ms | **0** | **8** | **2** | $0.00245 | The response completely missed the required concepts and formula for electricity circuits, instead focusing on a plan for implementing an interactive textbook experience, thus scoring low on accuracy and educational value. |
| 3 | **energy_sources** (easy) | ✅ Success | 19571ms | **6** | **8** | **5** | $0.00246 | The response fails to directly address the task about energy sources, instead focusing on a new rendering system, resulting in low accuracy and educational scores, despite being well-structured and clear. |
| 4 | **json** (hard) | ✅ Success | 12431ms | **8** | **9** | **8** | $0.00152 | The response is mostly accurate and well-structured, but it contains some discrepancies in the calculated values, such as the total circuit current and voltage drops, which should be consistent throughout the response. |
| 5 | **light_lenses** (medium) | ✅ Success | 16418ms | **0** | **6** | **2** | $0.00246 | The response completely misses the required concepts of refraction, bending of light, optical density, refractive index, and Snell's Law, and instead discusses a plan for overhauling an AI Tutor's presentation, making it irrelevant to the task and filled with hallucinated content. |
| 6 | **light_mirrors** (easy) | ✅ Success | 22814ms | **0** | **8** | **2** | $0.00246 | The response completely misses the required concepts and formula related to light mirrors, instead discussing a system design for a interactive textbook-like experience, indicating a significant misunderstanding of the task. |
| 7 | **magnetism** (medium) | ✅ Success | 19204ms | **0** | **6** | **0** | $0.00246 | The response completely fails to address the task type and expected concepts related to magnetism, instead focusing on a rendering system and UI blocks, which indicates a critical failure in accuracy and educational value. |
| 8 | **mechanics** (easy) | ✅ Success | 15834ms | **6** | **8** | **5** | $0.00228 | The response fails to directly address the task's required concepts of inertia, first law, unbalanced external force, state of rest, and motion, instead focusing on a proposed implementation strategy for an interactive textbook-like experience, thus scoring low on accuracy and educational value, with hallucination detected due to the introduction of unrelated implementation details. |
| 9 | **svg** (hard) | ✅ Success | 16757ms | **0** | **6** | **2** | $0.00247 | The response completely missed the required concepts and task type, providing instead a detailed plan for overhauling an AI Tutor's rendering, which is irrelevant to the task of creating an SVG string containing specific elements like polygon, line, text, incident, refracted, emergent, and deviation. |
| 10 | **work_energy** (medium) | ✅ Success | 18494ms | **0** | **8** | **2** | $0.00246 | The response completely misses the required concepts and formula related to work and energy, instead focusing on a system architecture for parsing and rendering Markdown content, which is unrelated to the task and indicates a significant hallucination. |
