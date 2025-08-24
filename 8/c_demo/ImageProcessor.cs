using System.Diagnostics;

namespace ImageQualityScreener
{
    /// <summary>
    /// 画像品質スクリーニングを実行するクラス
    /// </summary>
    public class ImageProcessor
    {
        private readonly string _exePath;
        
        public ImageProcessor()
        {
            // .exeファイルの場所（同じディレクトリ）
            _exePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "ImageQualityScreener.exe");
        }
        
        /// <summary>
        /// 画像品質スクリーニングを実行
        /// </summary>
        /// <param name="inputDir">入力画像ディレクトリ</param>
        /// <param name="outputDir">出力画像ディレクトリ</param>
        /// <returns>処理が成功したかどうか</returns>
        public async Task<bool> ProcessImagesAsync(string inputDir, string outputDir)
        {
            try
            {
                // .exeファイルの存在確認
                if (!File.Exists(_exePath))
                {
                    Console.WriteLine($"❌ ImageQualityScreener.exeが見つかりません: {_exePath}");
                    return false;
                }
                
                // 入力ディレクトリの存在確認
                if (!Directory.Exists(inputDir))
                {
                    Console.WriteLine($"❌ 入力ディレクトリが存在しません: {inputDir}");
                    return false;
                }
                
                // 出力ディレクトリを作成
                Directory.CreateDirectory(outputDir);
                
                Console.WriteLine($"🔍 入力ディレクトリ: {inputDir}");
                Console.WriteLine($"📁 出力ディレクトリ: {outputDir}");
                Console.WriteLine($"🚀 画像品質スクリーニングを開始...");
                
                // プロセス起動
                var startInfo = new ProcessStartInfo
                {
                    FileName = _exePath,
                    Arguments = $"\"{inputDir}\" \"{outputDir}\"",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    WorkingDirectory = AppDomain.CurrentDomain.BaseDirectory
                };
                
                using var process = Process.Start(startInfo);
                if (process == null)
                {
                    Console.WriteLine("❌ プロセスの起動に失敗しました");
                    return false;
                }
                
                // 出力を非同期で読み取り
                var outputTask = process.StandardOutput.ReadToEndAsync();
                var errorTask = process.StandardError.ReadToEndAsync();
                
                // プロセスの完了を待機
                await process.WaitForExitAsync();
                
                var output = await outputTask;
                var error = await errorTask;
                
                // 結果の表示
                if (!string.IsNullOrEmpty(output))
                {
                    Console.WriteLine("📋 処理ログ:");
                    Console.WriteLine(output);
                }
                
                if (process.ExitCode == 0)
                {
                    Console.WriteLine("✅ 画像品質スクリーニングが完了しました");
                    
                    // 結果の確認
                    var outputFiles = Directory.GetFiles(outputDir, "*.jpeg");
                    Console.WriteLine($"📊 スクリーニング済み画像: {outputFiles.Length}枚");
                    
                    return true;
                }
                else
                {
                    Console.WriteLine($"❌ エラーが発生しました (終了コード: {process.ExitCode})");
                    if (!string.IsNullOrEmpty(error))
                    {
                        Console.WriteLine($"エラー詳細: {error}");
                    }
                    return false;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ 処理エラー: {ex.Message}");
                return false;
            }
        }
        
        /// <summary>
        /// 画像品質スクリーニングを実行（同期的）
        /// </summary>
        /// <param name="inputDir">入力画像ディレクトリ</param>
        /// <param name="outputDir">出力画像ディレクトリ</param>
        /// <returns>処理が成功したかどうか</returns>
        public bool ProcessImages(string inputDir, string outputDir)
        {
            return ProcessImagesAsync(inputDir, outputDir).GetAwaiter().GetResult();
        }
    }
}
