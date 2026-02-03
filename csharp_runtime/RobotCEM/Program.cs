using Leap71.ShapeKernel;
using PicoGK;
using System;

namespace RobotCEM
{
    class Program
    {
        static void Main(string[] args)
        {
            try
            {
                // Output folder for generated files
                string strOutputFolder = Environment.GetEnvironmentVariable("ROBOTCEM_OUTPUT") ?? "./outputs";
                
                // Ensure output directory exists
                if (!Directory.Exists(strOutputFolder))
                {
                    Directory.CreateDirectory(strOutputFolder);
                }
                
                Console.WriteLine($"RobotCEM Design Generation Started");
                Console.WriteLine($"Output folder: {strOutputFolder}");
                
                // Run design generation in headless mode
                Generated.GeneratedDesign.GenerateDesign(strOutputFolder);
                
                Console.WriteLine("RobotCEM Design Generation Completed Successfully");
            }
            catch (Exception e)
            {
                Console.WriteLine("ERROR: RobotCEM Design Generation Failed");
                Console.WriteLine(e.ToString());
                Environment.Exit(1);
            }
        }
    }
}
