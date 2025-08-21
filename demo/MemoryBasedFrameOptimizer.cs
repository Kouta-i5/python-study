using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Linq;

namespace FFINDO.Endoscope.MemoryBased
{
    /// <summary>
    /// メモリベース入力のフレーム最適化クラス
    /// メモリ上の画像データを直接処理する
    /// </summary>
    public class MemoryBasedFrameOptimizer
    {
        private readonly string _exePath;
        private readonly string _workingDirectory;

        /// <summary>
        /// コンストラクタ
        /// </summary>
        /// <param name="exePath">FrameOptimizer.exeのパス</param>
        /// <param name="workingDirectory">作業ディレクトリ</param>
        public MemoryBasedFrameOptimizer(string exePath, string workingDirectory = null)
        {
            _exePath = exePath ?? throw new ArgumentNullException(nameof(exePath));
            _workingDirectory = workingDirectory ?? Path.GetDirectoryName(exePath);
            
            if (!File.Exists(_exePath))
            {
                throw new FileNotFoundException($"FrameOptimizer.exeが見つかりません: {_exePath}");
            }
        }

        /// <summary>
        /// メモリ上の画像データからフレーム最適化を実行（非同期）
        /// C#システム内で画像を直接処理する場合に使用
        /// </summary>
        /// <param name="imageDataList">画像データのリスト</param>
        /// <param name="outputDir">出力画像ディレクトリ</param>
        /// <param name="sharpnessThreshold">鮮明度閾値</param>
        /// <param name="similarityThreshold">類似度閾値</param>
        /// <param name="progressCallback">進捗コールバック</param>
        /// <returns>実行結果</returns>
        public async Task<MemoryOptimizationResult> OptimizeFramesFromMemoryAsync(
            List<byte[]> imageDataList,
            string outputDir,
            double sharpnessThreshold = 100.0,
            double similarityThreshold = 0.85,
            IProgress<string> progressCallback = null)
        {
            try
            {
                progressCallback?.Report("メモリからのフレーム最適化を開始しています...");

                // 引数の検証
                ValidateImageData(imageDataList);
                ValidateOutputDirectory(outputDir);

                // 一時ディレクトリを作成
                var tempDir = Path.Combine(Path.GetTempPath(), $"FrameOptimizer_{Guid.NewGuid()}");
                Directory.CreateDirectory(tempDir);

                try
                {
                    // 画像データを一時ファイルとして保存
                    var tempImageFiles = await SaveImagesToTempFiles(imageDataList, tempDir, progressCallback);

                    progressCallback?.Report($"{imageDataList.Count}個の画像を一時ファイルに保存しました");

                    // 一時ディレクトリから最適化を実行
                    var result = await ExecuteOptimizationFromDirectory(
                        tempDir, 
                        outputDir, 
                        sharpnessThreshold, 
                        similarityThreshold, 
                        progressCallback
                    );

                    // 結果にメモリベースの情報を追加
                    result.InputImageCount = imageDataList.Count;
                    result.InputImageSizes = imageDataList.Select(img => img.Length).ToArray();
                    result.TempDirectory = tempDir;

                    // 一時ファイルをクリーンアップ
                    await CleanupTempFiles(tempImageFiles, tempDir, progressCallback);

                    return result;
                }
                catch
                {
                    // エラーが発生した場合もクリーンアップ
                    await CleanupTempFiles(tempImageFiles, tempDir, progressCallback);
                    throw;
                }
            }
            catch (Exception ex)
            {
                progressCallback?.Report($"メモリからの最適化でエラーが発生しました: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// 画像オブジェクトからフレーム最適化を実行（非同期）
        /// System.Drawing.Image または System.Windows.Media.ImageSource から
        /// </summary>
        /// <param name="images">画像オブジェクトのリスト</param>
        /// <param name="outputDir">出力画像ディレクトリ</param>
        /// <param name="sharpnessThreshold">鮮明度閾値</param>
        /// <param name="similarityThreshold">類似度閾値</param>
        /// <param name="progressCallback">進捗コールバック</param>
        /// <returns>実行結果</returns>
        public async Task<MemoryOptimizationResult> OptimizeFramesFromImagesAsync<T>(
            List<T> images,
            string outputDir,
            double sharpnessThreshold = 100.0,
            double similarityThreshold = 0.85,
            IProgress<string> progressCallback = null) where T : class
        {
            try
            {
                progressCallback?.Report("画像オブジェクトからのフレーム最適化を開始しています...");

                // 画像をバイト配列に変換
                var imageDataList = new List<byte[]>();
                
                for (int i = 0; i < images.Count; i++)
                {
                    progressCallback?.Report($"画像 {i + 1}/{images.Count} を変換中...");
                    byte[] imageBytes = await ConvertImageToBytesAsync(images[i]);
                    imageDataList.Add(imageBytes);
                }

                progressCallback?.Report("すべての画像の変換が完了しました");

                // バイト配列から最適化を実行
                return await OptimizeFramesFromMemoryAsync(
                    imageDataList, 
                    outputDir, 
                    sharpnessThreshold, 
                    similarityThreshold, 
                    progressCallback
                );
            }
            catch (Exception ex)
            {
                progressCallback?.Report($"画像オブジェクトからの最適化でエラーが発生しました: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// 画像オブジェクトをバイト配列に変換
        /// </summary>
        private async Task<byte[]> ConvertImageToBytesAsync<T>(T image) where T : class
        {
            return await Task.Run(() =>
            {
                // ここで画像の種類に応じてバイト配列に変換
                // System.Drawing.Image, System.Windows.Media.ImageSource などに対応
                
                if (image is System.Drawing.Image drawingImage)
                {
                    using var ms = new MemoryStream();
                    drawingImage.Save(ms, System.Drawing.Imaging.ImageFormat.Jpeg);
                    return ms.ToArray();
                }
                
                // 他の画像形式にも対応可能
                throw new NotSupportedException($"サポートされていない画像形式: {image.GetType().Name}");
            });
        }

        /// <summary>
        /// 画像データを一時ファイルに保存
        /// </summary>
        private async Task<List<string>> SaveImagesToTempFiles(
            List<byte[]> imageDataList, 
            string tempDir, 
            IProgress<string> progressCallback)
        {
            var tempImageFiles = new List<string>();

            for (int i = 0; i < imageDataList.Count; i++)
            {
                var tempFilePath = Path.Combine(tempDir, $"temp_image_{i:04d}.jpeg");
                await File.WriteAllBytesAsync(tempFilePath, imageDataList[i]);
                tempImageFiles.Add(tempFilePath);
                
                progressCallback?.Report($"一時ファイル作成: {i + 1}/{imageDataList.Count}");
            }

            return tempImageFiles;
        }

        /// <summary>
        /// 一時ディレクトリから最適化を実行
        /// </summary>
        private async Task<MemoryOptimizationResult> ExecuteOptimizationFromDirectory(
            string tempDir,
            string outputDir,
            double sharpnessThreshold,
            double similarityThreshold,
            IProgress<string> progressCallback)
        {
            // コマンドライン引数を構築
            var arguments = BuildArguments(tempDir, outputDir, sharpnessThreshold, similarityThreshold);

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
            var result = new MemoryOptimizationResult
            {
                Success = process.ExitCode == 0,
                ExitCode = process.ExitCode,
                Output = outputLines.ToArray(),
                Errors = errorLines.ToArray(),
                OutputDirectory = outputDir,
                SharpnessThreshold = sharpnessThreshold,
                SimilarityThreshold = similarityThreshold
            };

            if (result.Success)
            {
                progressCallback?.Report("メモリベースの最適化が完了しました");
                
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
                progressCallback?.Report($"メモリベースの最適化が失敗しました（終了コード: {process.ExitCode}）");
            }

            return result;
        }

        /// <summary>
        /// 一時ファイルをクリーンアップ
        /// </summary>
        private async Task CleanupTempFiles(List<string> tempFiles, string tempDir, IProgress<string> progressCallback)
        {
            try
            {
                progressCallback?.Report("一時ファイルをクリーンアップ中...");

                // 一時ファイルを削除
                foreach (var tempFile in tempFiles)
                {
                    if (File.Exists(tempFile))
                    {
                        File.Delete(tempFile);
                    }
                }

                // 一時ディレクトリを削除
                if (Directory.Exists(tempDir))
                {
                    Directory.Delete(tempDir, true);
                }

                progressCallback?.Report("一時ファイルのクリーンアップが完了しました");
            }
            catch (Exception ex)
            {
                progressCallback?.Report($"一時ファイルのクリーンアップでエラーが発生しました: {ex.Message}");
                // クリーンアップの失敗は致命的ではないため、ログのみ出力
            }
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
        /// 画像データを検証
        /// </summary>
        private void ValidateImageData(List<byte[]> imageDataList)
        {
            if (imageDataList == null || imageDataList.Count == 0)
                throw new ArgumentException("画像データが指定されていません", nameof(imageDataList));

            if (imageDataList.Count > 1000)
                throw new ArgumentException("画像数が多すぎます（最大1000枚）", nameof(imageDataList));

            foreach (var imageData in imageDataList)
            {
                if (imageData == null || imageData.Length == 0)
                    throw new ArgumentException("空の画像データが含まれています");

                if (imageData.Length > 50 * 1024 * 1024) // 50MB制限
                    throw new ArgumentException("画像サイズが大きすぎます（最大50MB）");
            }
        }

        /// <summary>
        /// 出力ディレクトリを検証
        /// </summary>
        private void ValidateOutputDirectory(string outputDir)
        {
            if (string.IsNullOrEmpty(outputDir))
                throw new ArgumentException("出力ディレクトリが指定されていません", nameof(outputDir));

            // 出力ディレクトリが存在しない場合は作成
            if (!Directory.Exists(outputDir))
            {
                Directory.CreateDirectory(outputDir);
            }
        }

        /// <summary>
        /// コマンドライン引数を構築
        /// </summary>
        private string BuildArguments(string tempDir, string outputDir, double sharpnessThreshold, double similarityThreshold)
        {
            // パス区切り文字をWindows形式に統一
            var normalizedTempDir = Path.GetFullPath(tempDir);
            var normalizedOutputDir = Path.GetFullPath(outputDir);
            
            return $"\"{normalizedTempDir}\" \"{normalizedOutputDir}\" --sharpness {sharpnessThreshold:F1} --similarity {similarityThreshold:F2}";
        }

        /// <summary>
        /// 標準出力から詳細情報を抽出
        /// </summary>
        private void ParseOutputDetails(MemoryOptimizationResult result, List<string> outputLines)
        {
            foreach (var line in outputLines)
            {
                // 入力画像数を抽出
                if (line.Contains("入力画像数:"))
                {
                    var match = System.Text.RegularExpressions.Regex.Match(line, @"入力画像数:\s*(\d+)");
                    if (match.Success && int.TryParse(match.Groups[1].Value, out int inputCount))
                    {
                        result.ProcessedImageCount = inputCount;
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
    /// メモリベース最適化の実行結果
    /// </summary>
    public class MemoryOptimizationResult
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
        /// 入力画像数（メモリ上の画像）
        /// </summary>
        public int InputImageCount { get; set; }

        /// <summary>
        /// 入力画像のサイズ配列（バイト）
        /// </summary>
        public int[] InputImageSizes { get; set; } = Array.Empty<int>();

        /// <summary>
        /// 処理された画像数（一時ファイルに保存された画像）
        /// </summary>
        public int ProcessedImageCount { get; set; }

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
        /// 一時ディレクトリのパス
        /// </summary>
        public string TempDirectory { get; set; }

        /// <summary>
        /// 実行時間（ミリ秒）
        /// </summary>
        public long ExecutionTimeMs { get; set; }

        /// <summary>
        /// 総入力サイズ（バイト）
        /// </summary>
        public long TotalInputSize => InputImageSizes.Sum(size => (long)size);

        /// <summary>
        /// 平均入力画像サイズ（バイト）
        /// </summary>
        public double AverageInputSize => InputImageCount > 0 ? (double)TotalInputSize / InputImageCount : 0;
    }
}
