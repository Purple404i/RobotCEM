
using PicoGK;
using Leap71.ShapeKernel;
using Leap71.LatticeLibrary;
using System;
using System.Numerics;
using System.Collections.Generic;

namespace GeneratedCEM
{
    class Program
    {
        static void Main()
        {
            Library.Go(
                0.5f,  // Voxel size in mm
                Run
            );
        }

        static void Run()
        {
            try
            {
                Console.WriteLine("Generating custom...");
                
                CustomDevice device = new CustomDevice(
                    
                );
                
                Voxels voxResult = device.Generate();
                
                // Export
                Library.oViewer().Add(voxResult);
                Voxels.SaveToStlFile(voxResult, "output.stl");
                
                // Export metadata
                System.IO.File.WriteAllText(
                    "output_meta.json",
                    device.GetMetadata()
                );
                
                Console.WriteLine("Generation complete!");
                Console.WriteLine($"STL: output.stl");
                Console.WriteLine($"Metadata: output_meta.json");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
                Console.WriteLine(ex.StackTrace);
                Environment.Exit(1);
            }
        }
    }

    
public class CustomDevice
{
    public Voxels Generate()
    {
        // Custom device generation
        Voxels voxResult = new Voxels();
        
        // Add your custom geometry here
        
        return voxResult;
    }
    
    public string GetMetadata()
    {
        return "{}";
    }
}

}