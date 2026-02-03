using PicoGK;
using RobotCEM.Generated;
using System;

namespace RobotCEM
{
    class Program 
    {
        static void Main(string[] args)
        {
            try
            {
                // Check for headless mode
                bool headless = args.Length > 0 && args[0] == "--headless";
                
                // Initialize PicoGK
                float voxelSize = 0.5f; // 0.5mm voxel size - adjust as needed
                
                if (headless)
                {
                    Console.WriteLine("Starting PicoGK in HEADLESS mode...");
                    Library.Go(
                        voxelSize,
                        GeneratedDesign.Task,
                        Library.RunMode.Headless
                    );
                }
                else
                {
                    Console.WriteLine("Starting PicoGK with VIEWER...");
                    Library.Go(
                        voxelSize,
                        GeneratedDesign.Task
                    );
                }
                
                Console.WriteLine("PicoGK execution completed successfully!");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"FATAL ERROR: {ex.Message}");
                Console.WriteLine(ex.StackTrace);
                Environment.Exit(1);
            }
        }
    }
}