using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace DEMO.Endoscope.DirectoryBased
{
    /// <summary>
    /// ディレクトリベース入力のフレーム最適化クラス
    /// 既存のディレクトリ内の画像ファイルを処理する
    /// </summary>
    public class DirectoryBasedFrameOptimizer
    {
        private readonly string _exePath;
        private readonly string _workingDirectory;

        /// <summary>
        /// コンストラクタ
        /// </summary>
        /// <param name="exePath">FrameOptimizer.exeのパス</param>
        /// <param name="workingDirectory">作業ディレクトリ</param>
        public DirectoryBasedFrameOptimizer(string exePath, string workingDirectory = null)
        {
            _exePath = exePath ?? throw new ArgumentNullException(nameof(exePath));
            _workingDirectory = workingDirectory ?? Path.GetDirectoryName(exePath);
            
            if (!File.Exists(_exePath))
            {
                throw new FileNotFoundException($"FrameOptimizer.exeが見つかりません: {_exePath}");
            }
        }

        /// <summary>
        /// ディレクトリ内の画像を最適化（非同期）
        /// </summary>
        /// <param name="inputDir">入力画像ディレクトリ</param>
        /// <param name="outputDir">出力画像ディレクトリ</param>
        /// <param name="sharpnessThreshold">鮮明度閾値</param>
        /// <param name="similarityThreshold">類似度閾値</param>
        /// <param name="progressCallback">進捗コールバック</param>
        /// <returns>実行結果</returns>
        public async Task<DirectoryOptimizationResult> OptimizeFramesAsync(
            string inputDir, 
            string outputDir, 
            double sharpnessThreshold = 100.0, 
            double similarityThreshold = 0.85,
            IProgress<string> progressCallback = null)
        {
            try
            {
                progressCallback?.Report("ディレクトリベースのフレーム最適化を開始しています...");

                // 引数の検証
                ValidateDirectories(inputDir, outputDir);

                // 入力ディレクトリ内の画像ファイルを確認
                var inputFiles = GetInputImageFiles(inputDir);
                if (inputFiles.Length == 0)
                {
                    throw new InvalidOperationException($"入力ディレクトリに画像ファイルが見つかりません: {inputDir}");
                }

                progressCallback?.Report($"入力画像ファイル数: {inputFiles.Length}");

                // コマンドライン引数を構築
                var arguments = BuildArguments(inputDir, outputDir, sharpnessThreshold, similarityThreshold);

                // プロセス開始情報を設定
                var startInfo = new ProcessStartInfo
                {
                    FileName = _exePath,
                    Arguments = arguments,
                    WorkingDirectory = _workingDirectory,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = false,
                    WindowStyle = ProcessWindowStyle.Normal,
                    StandardOutputEncoding = System.Text.Encoding.UTF8,
                    StandardErrorEncoding = System.Text.Encoding.UTF8
                };

                progressCallback?.Report("FrameOptimizer.exeを実行中...");

                // プロセスを開始
                using var process = new Process { StartInfo = startInfo };
                
                var outputLines = new List<string>();
                var errorLines = new List<string>();

                // 出力をキャプチャ
                process.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        outputLines.Add(e.Data);
                        progressCallback?.Report(e.Data);
                    }
                };

                process.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        errorLines.Add(e.Data);
                        progressCallback?.Report($"エラー: {e.Data}");
                    }
                };

                // プロセスを開始
                if (!process.Start())
                {
                    throw new InvalidOperationException("プロセスの開始に失敗しました");
                }

                // 非同期で出力を読み取り開始
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                // 完了を待機
                await process.WaitForExitAsync();

                // 結果を解析
                var result = new DirectoryOptimizationResult
                {
                    Success = process.ExitCode == 0,
                    ExitCode = process.ExitCode,
                    Output = outputLines.ToArray(),
                    Errors = errorLines.ToArray(),
                    InputDirectory = inputDir,
                    OutputDirectory = outputDir,
                    SharpnessThreshold = sharpnessThreshold,
                    SimilarityThreshold = similarityThreshold,
                    InputFiles = inputFiles
                };

                if (result.Success)
                {
                    progressCallback?.Report("ディレクトリベースの最適化が完了しました");
                    
                    // 出力ファイルを確認
                    if (Directory.Exists(outputDir))
                    {
                        var outputFiles = GetOutputImageFiles(outputDir);
                        result.OutputFiles = outputFiles;
                        result.OutputFileCount = outputFiles.Length;
                        progressCallback?.Report($"出力ファイル数: {result.OutputFileCount}");
                    }
                    
                    // 標準出力から詳細情報を抽出
                    ParseOutputDetails(result, outputLines);
                }
                else
                {
                    progressCallback?.Report($"ディレクトリベースの最適化が失敗しました（終了コード: {process.ExitCode}）");
                }

                return result;
            }
            catch (Exception ex)
            {
                progressCallback?.Report($"ディレクトリベースの最適化でエラーが発生しました: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// ディレクトリ内の画像を最適化（同期）
        /// </summary>
        public DirectoryOptimizationResult OptimizeFrames(
            string inputDir, 
            string outputDir, 
            double sharpnessThreshold = 100.0, 
            double similarityThreshold = 0.85)
        {
            return OptimizeFramesAsync(inputDir, outputDir, sharpnessThreshold, similarityThreshold).Result;
        }

        /// <summary>
        /// バッチファイルを使用して最適化を実行
        /// </summary>
        public async Task<DirectoryOptimizationResult> OptimizeFramesWithBatchAsync(
            string inputDir, 
            string outputDir,
            IProgress<string> progressCallback = null)
        {
            var batchPath = Path.Combine(_workingDirectory, "run_frame_optimizer.bat");
            
            if (!File.Exists(batchPath))
            {
                throw new FileNotFoundException($"バッチファイルが見つかりません: {batchPath}");
            }

            try
            {
                progressCallback?.Report("バッチファイルでディレクトリベースの最適化を開始しています...");

                var startInfo = new ProcessStartInfo
                {
                    FileName = batchPath,
                    Arguments = $"\"{inputDir}\" \"{outputDir}\"",
                    WorkingDirectory = _workingDirectory,
                    UseShellExecute = true,
                    WindowStyle = ProcessWindowStyle.Normal
                };

                using var process = new Process { StartInfo = startInfo };
                process.Start();
                await process.WaitForExitAsync();

                var result = new DirectoryOptimizationResult
                {
                    Success = process.ExitCode == 0,
                    ExitCode = process.ExitCode,
                    InputDirectory = inputDir,
                    OutputDirectory = outputDir,
                    Output = new[] { "バッチファイルでディレクトリベースの実行が完了しました" }
                };

                if (result.Success)
                {
                    progressCallback?.Report("バッチファイルでのディレクトリベース実行が完了しました");
                }

                return result;
            }
            catch (Exception ex)
            {
                progressCallback?.Report($"バッチファイルでのディレクトリベース実行でエラーが発生しました: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// 入力ディレクトリ内の画像ファイルを取得
        /// </summary>
        private string[] GetInputImageFiles(string inputDir)
        {
            var supportedExtensions = new[] { "*.jpeg", "*.jpg", "*.png", "*.bmp", "*.tiff" };
            var allFiles = new List<string>();

            foreach (var extension in supportedExtensions)
            {
                var files = Directory.GetFiles(inputDir, extension);
                allFiles.AddRange(files);
            }

            return allFiles.ToArray();
        }

        /// <summary>
        /// 出力ディレクトリ内の画像ファイルを取得
        /// </summary>
        private string[] GetOutputImageFiles(string outputDir)
        {
            var supportedExtensions = new[] { "*.jpeg", "*.jpg", "*.png", "*.bmp", "*.tiff" };
            var allFiles = new List<string>();

            foreach (var extension in supportedExtensions)
            {
                var files = Directory.GetFiles(outputDir, extension);
                allFiles.AddRange(files);
            }

            return allFiles.ToArray();
        }

        /// <summary>
        /// 設定を検証
        /// </summary>
        private void ValidateDirectories(string inputDir, string outputDir)
        {
            if (string.IsNullOrEmpty(inputDir))
                throw new ArgumentException("入力ディレクトリが指定されていません", nameof(inputDir));

            if (string.IsNullOrEmpty(outputDir))
                throw new ArgumentException("出力ディレクトリが指定されていません", nameof(outputDir));

            if (!Directory.Exists(inputDir))
                throw new DirectoryNotFoundException($"入力ディレクトリが存在しません: {inputDir}");

            // 出力ディレクトリが存在しない場合は作成
            if (!Directory.Exists(outputDir))
            {
                Directory.CreateDirectory(outputDir);
            }
        }

        /// <summary>
        /// コマンドライン引数を構築
        /// </summary>
        private string BuildArguments(string inputDir, string outputDir, double sharpnessThreshold, double similarityThreshold)
        {
            // パス区切り文字をWindows形式に統一
            var normalizedInputDir = Path.GetFullPath(inputDir);
            var normalizedOutputDir = Path.GetFullPath(outputDir);
            
            return $"\"{normalizedInputDir}\" \"{normalizedOutputDir}\" --sharpness {sharpnessThreshold:F1} --similarity {similarityThreshold:F2}";
        }

        /// <summary>
        /// 標準出力から詳細情報を抽出
        /// </summary>
        private void ParseOutputDetails(DirectoryOptimizationResult result, List<string> outputLines)
        {
            foreach (var line in outputLines)
            {
                // 入力画像数を抽出
                if (line.Contains("入力画像数:"))
                {
                    var match = System.Text.RegularExpressions.Regex.Match(line, @"入力画像数:\s*(\d+)");
                    if (match.Success && int.TryParse(match.Groups[1].Value, out int inputCount))
                    {
                        result.InputFileCount = inputCount;
                    }
                }
                
                // 鮮明度フィルタリング結果を抽出
                if (line.Contains("鮮明度フィルタリング完了:"))
                {
                    var match = System.Text.RegularExpressions.Regex.Match(line, @"鮮明度フィルタリング完了:\s*(\d+)/(\d+)");
                    if (match.Success && int.TryParse(match.Groups[1].Value, out int sharpCount))
                    {
                        result.SharpImageCount = sharpCount;
                    }
                }
                
                // 類似度フィルタリング結果を抽出
                if (line.Contains("類似度フィルタリング完了:"))
                {
                    var match = System.Text.RegularExpressions.Regex.Match(line, @"類似度フィルタリング完了:\s*(\d+)/(\d+)");
                    if (match.Success && int.TryParse(match.Groups[1].Value, out int uniqueCount))
                    {
                        result.UniqueImageCount = uniqueCount;
                    }
                }
                
                // 最終結果を抽出
                if (line.Contains("処理完了:") && line.Contains("画像が最適化されました"))
                {
                    var match = System.Text.RegularExpressions.Regex.Match(line, @"処理完了:\s*(\d+)\s*画像");
                    if (match.Success && int.TryParse(match.Groups[1].Value, out int finalCount))
                    {
                        result.FinalImageCount = finalCount;
                    }
                }
            }
        }
    }

    /// <summary>
    /// ディレクトリベース最適化の実行結果
    /// </summary>
    public class DirectoryOptimizationResult
    {
        /// <summary>
        /// 実行が成功したかどうか
        /// </summary>
        public bool Success { get; set; }

        /// <summary>
        /// 終了コード
        /// </summary>
        public int ExitCode { get; set; }

        /// <summary>
        /// 標準出力
        /// </summary>
        public string[] Output { get; set; } = Array.Empty<string>();

        /// <summary>
        /// エラー出力
        /// </summary>
        public string[] Errors { get; set; } = Array.Empty<string>();

        /// <summary>
        /// 入力ディレクトリ
        /// </summary>
        public string InputDirectory { get; set; }

        /// <summary>
        /// 出力ディレクトリ
        /// </summary>
        public string OutputDirectory { get; set; }

        /// <summary>
        /// 鮮明度閾値
        /// </summary>
        public double SharpnessThreshold { get; set; }

        /// <summary>
        /// 類似度閾値
        /// </summary>
        public double SimilarityThreshold { get; set; }

        /// <summary>
        /// 入力ファイルのパス一覧
        /// </summary>
        public string[] InputFiles { get; set; } = Array.Empty<string>();

        /// <summary>
        /// 入力ファイル数
        /// </summary>
        public int InputFileCount { get; set; }

        /// <summary>
        /// 出力ファイルのパス一覧
        /// </summary>
        public string[] OutputFiles { get; set; } = Array.Empty<string>();

        /// <summary>
        /// 出力ファイル数
        /// </summary>
        public int OutputFileCount { get; set; }

        /// <summary>
        /// 鮮明度フィルタリング後の画像数
        /// </summary>
        public int SharpImageCount { get; set; }

        /// <summary>
        /// 類似度フィルタリング後の画像数
        /// </summary>
        public int UniqueImageCount { get; set; }

        /// <summary>
        /// 最終的な画像数
        /// </summary>
        public int FinalImageCount { get; set; }

        /// <summary>
        /// 実行時間（ミリ秒）
        /// </summary>
        public long ExecutionTimeMs { get; set; }
    }
}
