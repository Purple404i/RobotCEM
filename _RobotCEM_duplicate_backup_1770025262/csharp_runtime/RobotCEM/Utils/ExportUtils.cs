using System;

namespace RobotCEM.Utils
{
    public static class ExportUtils
    {
        public static void ExportMetadata(string filePath, object metadata)
        {
            string json = System.Text.Json.JsonSerializer.Serialize(metadata);
            System.IO.File.WriteAllText(filePath, json);
            Console.WriteLine($"Metadata exported to: {filePath}");
        }
    }
}
