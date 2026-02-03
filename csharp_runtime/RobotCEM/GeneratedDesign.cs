using Leap71.ShapeKernel;
using Leap71.LatticeLibrary;
using PicoGK;
using System;
using System.IO;
using System.Numerics;

namespace RobotCEM.Generated
{
    public class GeneratedDesign
    {
        public static void Task()
        {
            try
            {
                Library.Log("╔════════════════════════════════════════╗");
                Library.Log("║   RobotCEM Design Generation Started  ║");
                Library.Log("╚════════════════════════════════════════╝");
                
                // Design parameters
                string deviceType = "test_component";
                float safetyFactor = 1.5f;
                
                Library.Log($"Device Type: {deviceType}");
                Library.Log($"Safety Factor: {safetyFactor}");
                Library.Log($"Voxel Size: {Library.fVoxelSizeMM}mm");
                

                // Create Sphere using ShapeKernel
                BaseSphere oSphere = new BaseSphere(
                    new LocalFrame(), 
                    15f
                );
                Voxels voxShape = oSphere.voxConstruct();
                Library.Log($"Created sphere with radius {oSphere.fRadius} mm");


                // Apply lattice infill for weight reduction
                Library.Log("Applying BodyCentered lattice with beam thickness 2.0mm");
                
                ICellArray xCellArray = new RegularCellArray(voxShape, 20, 20, 20);
                ILatticeType xLatticeType = new BodyCenteredLattice();
                IBeamThickness xBeamThickness = new ConstantBeamThickness(2.0f);
                xBeamThickness.SetBoundingVoxels(voxShape);

                uint nSubSample = 5;
                Voxels voxLattice = voxGetFinalLatticeGeometry(
                    xCellArray,
                    xLatticeType,
                    xBeamThickness,
                    nSubSample);

                // Boolean intersection to combine lattice with base shape
                Voxels voxFinal = voxShape & voxLattice;
                Library.Log("Lattice infill applied successfully");

                // Convert to mesh
                Library.Log("Converting voxels to triangulated mesh...");
                Mesh msh = new Mesh(voxFinal);
                
                Library.Log($"Mesh statistics:");
                Library.Log($"  - Triangles: {msh.nTriangleCount()}");
                Library.Log($"  - Vertices: {msh.nVertexCount()}");
                
                // Export STL
                string outputPath = Path.Combine(Library.strLogFolder, "test_design.stl");
                Library.Log($"Saving to: {outputPath}");
                msh.SaveToStlFile(outputPath);
                
                // Export metadata
                var metadata = new
                {
                    DeviceType = deviceType,
                    SafetyFactor = safetyFactor,
                    VoxelSize = Library.fVoxelSizeMM,
                    Triangles = msh.nTriangleCount(),
                    Vertices = msh.nVertexCount(),
                    Timestamp = DateTime.Now.ToString("O")
                };
                
                string metaPath = Path.Combine(Library.strLogFolder, "test_design_meta.json");
                File.WriteAllText(metaPath, System.Text.Json.JsonSerializer.Serialize(metadata, 
                    new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
                
                Library.Log("╔════════════════════════════════════════╗");
                Library.Log("║     Generation Completed Successfully  ║");
                Library.Log("╚════════════════════════════════════════╝");
                
                // Add to viewer if not headless
                if (!Library.bHeadlessMode)
                {
                    Library.oViewer().Add(voxFinal);
                }
            }
            catch (Exception ex)
            {
                Library.Log($"ERROR: {ex.Message}");
                Library.Log(ex.StackTrace);
                if (!Library.bHeadlessMode)
                {
                    Library.oViewer().SetBackgroundColor(Cp.clrWarning);
                }
                throw;
            }
        }
    }
}
