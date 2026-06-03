const fs = require('fs');
const path = require('path');

const datasetDir = path.resolve(__dirname, '../benchmark_dataset');
const responsesDir = path.resolve(datasetDir, 'responses');
const judgeResponsesDir = path.resolve(datasetDir, 'judge_responses');
const resultsCsvPath = path.resolve(datasetDir, 'benchmark_results.csv');
const failuresCsvPath = path.resolve(datasetDir, 'failures.csv');
const leaderboardCsvPath = path.resolve(datasetDir, 'leaderboard.csv');
const summaryMdPath = path.resolve(datasetDir, 'parallel_summary.md');
const checkpointPath = path.resolve(datasetDir, 'checkpoint.json');

console.log('🧹 Starting cleanup of all benchmark results...');

// Function to delete a file if it exists
function deleteFile(filePath) {
  if (fs.existsSync(filePath)) {
    try {
      fs.unlinkSync(filePath);
      console.log(`✅ Deleted file: ${path.basename(filePath)}`);
    } catch (err) {
      console.error(`❌ Failed to delete file ${path.basename(filePath)}:`, err.message);
    }
  }
}

// Function to recursively delete a directory
function deleteDirRecursive(dirPath) {
  if (fs.existsSync(dirPath)) {
    try {
      fs.rmSync(dirPath, { recursive: true, force: true });
      console.log(`✅ Deleted directory: ${path.basename(dirPath)}`);
    } catch (err) {
      console.error(`❌ Failed to delete directory ${path.basename(dirPath)}:`, err.message);
    }
  }
}

// Delete result CSVs & markdown summaries
deleteFile(resultsCsvPath);
deleteFile(failuresCsvPath);
deleteFile(leaderboardCsvPath);
deleteFile(summaryMdPath);

// Delete checkpoints
deleteFile(checkpointPath);

// Delete response subdirectories
deleteDirRecursive(responsesDir);
deleteDirRecursive(judgeResponsesDir);

console.log('🧹 Cleanup completed!');
