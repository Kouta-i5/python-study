namespace ImageQualityScreener
{
    class Program
    {
        static async Task Main(string[] args)
        {
            Console.WriteLine("🔧 画像品質スクリーニングシステム - C#デモ");
            Console.WriteLine("=" * 60);
            
            var processor = new ImageProcessor();
            
            // 入力・出力ディレクトリ
            string inputDir = "InputImages";
            string outputDir = "OutputImages";
            
            // コマンドライン引数がある場合は使用
            if (args.Length >= 2)
            {
                inputDir = args[0];
                outputDir = args[1];
            }
            
            Console.WriteLine($"📂 入力ディレクトリ: {inputDir}");
            Console.WriteLine($"📂 出力ディレクトリ: {outputDir}");
            Console.WriteLine();
            
            try
            {
                // 画像品質スクリーニングを実行
                bool success = await processor.ProcessImagesAsync(inputDir, outputDir);
                
                if (success)
                {
                    Console.WriteLine();
                    Console.WriteLine("🎉 処理が正常に完了しました！");
                    
                    // 結果の詳細表示
                    if (Directory.Exists(outputDir))
                    {
                        var outputFiles = Directory.GetFiles(outputDir, "*.jpeg");
                        var inputFiles = Directory.GetFiles(inputDir, "*.jpeg");
                        
                        Console.WriteLine();
                        Console.WriteLine("📊 処理結果:");
                        Console.WriteLine($"  入力画像: {inputFiles.Length}枚");
                        Console.WriteLine($"  スクリーニング済み: {outputFiles.Length}枚");
                        Console.WriteLine($"  除外された画像: {inputFiles.Length - outputFiles.Length}枚");
                        
                        if (outputFiles.Length > 0)
                        {
                            Console.WriteLine();
                            Console.WriteLine("📁 スクリーニング済み画像:");
                            foreach (var file in outputFiles.OrderBy(f => f))
                            {
                                var fileName = Path.GetFileName(file);
                                var fileSize = new FileInfo(file).Length / 1024; // KB
                                Console.WriteLine($"  - {fileName} ({fileSize} KB)");
                            }
                        }
                    }
                }
                else
                {
                    Console.WriteLine();
                    Console.WriteLine("❌ 処理が失敗しました");
                    Environment.ExitCode = 1;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine();
                Console.WriteLine($"❌ 予期しないエラーが発生しました: {ex.Message}");
                Environment.ExitCode = 1;
            }
            
            Console.WriteLine();
            Console.WriteLine("終了するには何かキーを押してください...");
            Console.ReadKey();
        }
    }
}
