from typing import Dict, List
from jinja2 import Template
import os

class CSharpCodeGenerator:
    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Template]:
        """Load C# code templates"""
        
        templates = {}
        
        # Base program template
        templates["program"] = Template("""
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
                {{ voxel_size }}f,  // Voxel size in mm
                Run
            );
        }

        static void Run()
        {
            try
            {
                Console.WriteLine("Generating {{ device_type }}...");
                
                {{ device_class }} device = new {{ device_class }}(
                    {{ constructor_params }}
                );
                
                Voxels voxResult = device.Generate();
                
                // Export
                Library.oViewer().Add(voxResult);
                Voxels.SaveToStlFile(voxResult, "{{ output_file }}.stl");
                
                // Export metadata
                System.IO.File.WriteAllText(
                    "{{ output_file }}_meta.json",
                    device.GetMetadata()
                );
                
                Console.WriteLine("Generation complete!");
                Console.WriteLine($"STL: {{ output_file }}.stl");
                Console.WriteLine($"Metadata: {{ output_file }}_meta.json");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
                Console.WriteLine(ex.StackTrace);
                Environment.Exit(1);
            }
        }
    }

    {{ device_implementation }}
}
""")
        
        # Robot arm template
        templates["robot_arm"] = Template("""
public class RobotArm
{
    private float m_fLength;
    private float m_fDiameter;
    private float m_fWallThickness;
    private string m_sMaterial;
    private bool m_bUseLattice;
    private int m_nSegments;
    
    public RobotArm(
        float fLength,
        float fDiameter,
        float fWallThickness,
        string sMaterial,
        bool bUseLattice,
        int nSegments)
    {
        m_fLength = fLength;
        m_fDiameter = fDiameter;
        m_fWallThickness = fWallThickness;
        m_sMaterial = sMaterial;
        m_bUseLattice = bUseLattice;
        m_nSegments = nSegments;
    }
    
    public Voxels Generate()
    {
        Voxels voxFinal = new Voxels();
        
        float fSegmentLength = m_fLength / m_nSegments;
        
        for (int i = 0; i < m_nSegments; i++)
        {
            Vector3 vecStart = new Vector3(0, 0, i * fSegmentLength);
            Vector3 vecEnd = new Vector3(0, 0, (i + 1) * fSegmentLength);
            
            Voxels voxSegment = CreateSegment(vecStart, vecEnd);
            voxFinal.BoolAdd(voxSegment);
            
            // Add joint between segments
            if (i < m_nSegments - 1)
            {
                Voxels voxJoint = CreateJoint(vecEnd);
                voxFinal.BoolAdd(voxJoint);
            }
        }
        
        if (m_bUseLattice)
        {
            voxFinal = AddLatticeStructure(voxFinal);
        }
        
        return voxFinal;
    }
    
    private Voxels CreateSegment(Vector3 vecStart, Vector3 vecEnd)
    {
        // Create hollow cylindrical segment
        BaseCylinder cylOuter = new BaseCylinder(
            new LocalFrame(vecStart, vecEnd),
            m_fDiameter / 2.0f
        );
        
        BaseCylinder cylInner = new BaseCylinder(
            new LocalFrame(vecStart, vecEnd),
            (m_fDiameter / 2.0f) - m_fWallThickness
        );
        
        Voxels voxOuter = cylOuter.voxConstruct();
        Voxels voxInner = cylInner.voxConstruct();
        
        voxOuter.BoolSubtract(voxInner);
        
        return voxOuter;
    }
    
    private Voxels CreateJoint(Vector3 vecPosition)
    {
        // Create spherical joint
        float fJointRadius = m_fDiameter / 2.0f + 2.0f;
        
        BaseSphere sphere = new BaseSphere(
            new LocalFrame(vecPosition),
            fJointRadius
        );
        
        return sphere.voxConstruct();
    }
    
    private Voxels AddLatticeStructure(Voxels voxShell)
    {
        // Create lattice infill for weight reduction
        Lattice latInfill = new Lattice();
        
        // Add longitudinal beams
        float fBeamRadius = m_fWallThickness * 0.5f;
        
        for (int i = 0; i < 6; i++)
        {
            float fAngle = (float)(i * Math.PI / 3.0);
            float fRadialPos = (m_fDiameter / 2.0f - m_fWallThickness) * 0.7f;
            
            Vector3 vecStart = new Vector3(
                fRadialPos * (float)Math.Cos(fAngle),
                fRadialPos * (float)Math.Sin(fAngle),
                0
            );
            
            Vector3 vecEnd = new Vector3(
                fRadialPos * (float)Math.Cos(fAngle),
                fRadialPos * (float)Math.Sin(fAngle),
                m_fLength
            );
            
            latInfill.AddBeam(vecStart, vecEnd, fBeamRadius);
        }
        
        // Add cross bracing
        int nBraces = (int)(m_fLength / 50.0f);
        for (int i = 0; i < nBraces; i++)
        {
            float fZ = (i + 0.5f) * (m_fLength / nBraces);
            
            for (int j = 0; j < 6; j++)
            {
                float fAngle1 = (float)(j * Math.PI / 3.0);
                float fAngle2 = (float)((j + 1) * Math.PI / 3.0);
                float fRadialPos = (m_fDiameter / 2.0f - m_fWallThickness) * 0.7f;
                
                Vector3 vec1 = new Vector3(
                    fRadialPos * (float)Math.Cos(fAngle1),
                    fRadialPos * (float)Math.Sin(fAngle1),
                    fZ
                );
                
                Vector3 vec2 = new Vector3(
                    fRadialPos * (float)Math.Cos(fAngle2),
                    fRadialPos * (float)Math.Sin(fAngle2),
                    fZ
                );
                
                latInfill.AddBeam(vec1, vec2, fBeamRadius * 0.7f);
            }
        }
        
        Voxels voxLattice = latInfill.voxConstruct();
        
        // Combine shell with lattice
        voxShell.BoolAdd(voxLattice);
        
        return voxShell;
    }
    
    public string GetMetadata()
    {
        var metadata = new
        {
            device_type = "robot_arm",
            length = m_fLength,
            diameter = m_fDiameter,
            wall_thickness = m_fWallThickness,
            material = m_sMaterial,
            segments = m_nSegments,
            uses_lattice = m_bUseLattice,
            estimated_weight = CalculateWeight(),
            estimated_strength = CalculateStrength()
        };
        
        return System.Text.Json.JsonSerializer.Serialize(metadata);
    }
    
    private float CalculateWeight()
    {
        // Simplified weight calculation
        float fVolume = (float)(Math.PI * Math.Pow(m_fDiameter / 2.0, 2) * m_fLength);
        float fInnerVolume = (float)(Math.PI * Math.Pow((m_fDiameter / 2.0) - m_fWallThickness, 2) * m_fLength);
        float fShellVolume = fVolume - fInnerVolume;
        
        // Material density (example for PLA: 1.25 g/cm³)
        float fDensity = 1.25f;
        
        // Convert mm³ to cm³
        float fWeightGrams = (fShellVolume / 1000.0f) * fDensity;
        
        // Reduce by 70% if using lattice
        if (m_bUseLattice)
            fWeightGrams *= 0.3f;
        
        return fWeightGrams;
    }
    
    private float CalculateStrength()
    {
        // Simplified strength calculation (cantilever beam)
        // Returns max load in kg that can be supported at the end
        
        float fMomentOfInertia = (float)(Math.PI / 4.0 * (
            Math.Pow(m_fDiameter / 2.0, 4) - 
            Math.Pow((m_fDiameter / 2.0) - m_fWallThickness, 4)
        ));
        
        // Assume PLA: yield strength ~40 MPa
        float fYieldStrength = 40.0f;  // MPa
        float fSafetyFactor = 2.0f;
        float fAllowableStress = fYieldStrength / fSafetyFactor;
        
        // Max bending moment = F * L
        // Bending stress = M * c / I
        // where c = outer radius
        
        float fMaxMoment = (fAllowableStress * fMomentOfInertia) / (m_fDiameter / 2.0f);
        float fMaxForce = fMaxMoment / m_fLength;  // Newtons
        
        return fMaxForce / 9.81f;  // Convert to kg
    }
}
""")
        
        # Gripper template
        templates["gripper"] = Template("""
public class Gripper
{
    private float m_fJawWidth;
    private float m_fJawLength;
    private float m_fThickness;
    private float m_fGripRange;
    private string m_sMaterial;
    
    public Gripper(
        float fJawWidth,
        float fJawLength,
        float fThickness,
        float fGripRange,
        string sMaterial)
    {
        m_fJawWidth = fJawWidth;
        m_fJawLength = fJawLength;
        m_fThickness = fThickness;
        m_fGripRange = fGripRange;
        m_sMaterial = sMaterial;
    }
    
    public Voxels Generate()
    {
        Voxels voxFinal = new Voxels();
        
        // Create base mounting block
        Voxels voxBase = CreateBase();
        voxFinal.BoolAdd(voxBase);
        
        // Create two symmetric jaws
        Voxels voxJaw1 = CreateJaw(m_fGripRange / 2.0f);
        Voxels voxJaw2 = CreateJaw(-m_fGripRange / 2.0f);
        
        voxFinal.BoolAdd(voxJaw1);
        voxFinal.BoolAdd(voxJaw2);
        
        // Add servo mounting points
        Voxels voxServoMount = CreateServoMount();
        voxFinal.BoolAdd(voxServoMount);
        
        return voxFinal;
    }
    
    private Voxels CreateBase()
    {
        BaseBox box = new BaseBox(
            new LocalFrame(Vector3.Zero),
            new Vector3(m_fJawWidth * 2.0f, m_fThickness * 3.0f, 20.0f)
        );
        
        return box.voxConstruct();
    }
    
    private Voxels CreateJaw(float fOffset)
    {
        // Create jaw with gripper surface
        Vector3 vecPosition = new Vector3(fOffset, 0, 10.0f);
        
        BaseBox boxJaw = new BaseBox(
            new LocalFrame(vecPosition),
            new Vector3(m_fThickness, m_fJawWidth, m_fJawLength)
        );
        
        Voxels voxJaw = boxJaw.voxConstruct();
        
        // Add gripper teeth/texture
        for (int i = 0; i < 5; i++)
        {
            float fZ = 5.0f + i * (m_fJawLength / 5.0f);
            Vector3 vecTooth = new Vector3(
                fOffset + (Math.Sign(fOffset) * m_fThickness / 2.0f),
                0,
                fZ
            );
            
            BaseSphere tooth = new BaseSphere(
                new LocalFrame(vecTooth),
                1.5f
            );
            
            voxJaw.BoolAdd(tooth.voxConstruct());
        }
        
        return voxJaw;
    }
    
    private Voxels CreateServoMount()
    {
        // Standard servo mounting holes (23mm spacing)
        Voxels voxMount = new Voxels();
        
        float[] afHolePositions = { -11.5f, 11.5f };
        
        foreach (float fX in afHolePositions)
        {
            BaseCylinder hole = new BaseCylinder(
                new LocalFrame(
                    new Vector3(fX, 0, -5.0f),
                    new Vector3(fX, 0, 5.0f)
                ),
                2.0f  // M4 screw hole
            );
            
            voxMount.BoolAdd(hole.voxConstruct());
        }
        
        return voxMount;
    }
    
    public string GetMetadata()
    {
        var metadata = new
        {
            device_type = "gripper",
            jaw_width = m_fJawWidth,
            jaw_length = m_fJawLength,
            grip_range = m_fGripRange,
            material = m_sMaterial,
            estimated_grip_force = CalculateGripForce()
        };
        
        return System.Text.Json.JsonSerializer.Serialize(metadata);
    }
    
    private float CalculateGripForce()
    {
        // Simplified grip force calculation
        // Assumes servo torque of 10 kg·cm
        float fServoTorque = 10.0f;  // kg·cm
        float fLeverArm = m_fJawLength / 10.0f;  // cm
        
        return fServoTorque / fLeverArm;  // kg
    }
}
""")
        
        return templates
    
    def generate(self, spec: Dict, device_type: str) -> str:
        """Generate complete C# program"""
        
        # Determine which device template to use
        if device_type == "robot_arm":
            device_class = "RobotArm"
            device_impl = self.templates["robot_arm"].render()
            constructor_params = self._generate_arm_params(spec)
        elif device_type == "gripper":
            device_class = "Gripper"
            device_impl = self.templates["gripper"].render()
            constructor_params = self._generate_gripper_params(spec)
        else:
            device_class = "CustomDevice"
            device_impl = self._generate_custom_device(spec)
            constructor_params = ""
        
        # Generate main program
        code = self.templates["program"].render(
            voxel_size=spec.get("voxel_size", 0.5),
            device_type=device_type,
            device_class=device_class,
            constructor_params=constructor_params,
            output_file=spec.get("output_file", "output"),
            device_implementation=device_impl
        )
        
        return code
    
    def _generate_arm_params(self, spec: Dict) -> str:
        dims = spec.get("dimensions", {})
        return f"""
            {dims.get("length", 200)}f,        // length
            {dims.get("diameter", 50)}f,       // diameter
            {spec.get("wall_thickness", 3)}f,  // wall thickness
            "{spec.get("material", "PLA")}",   // material
            {str(spec.get("use_lattice", True)).lower()},  // use lattice
            {spec.get("segments", 3)}           // segments
        """.strip()
    
    def _generate_gripper_params(self, spec: Dict) -> str:
        dims = spec.get("dimensions", {})
        return f"""
            {dims.get("jaw_width", 30)}f,      // jaw width
            {dims.get("jaw_length", 50)}f,     // jaw length
            {dims.get("thickness", 5)}f,       // thickness
            {dims.get("grip_range", 40)}f,     // grip range
            "{spec.get("material", "PLA")}"    // material
        """.strip()
    
    def _generate_custom_device(self, spec: Dict) -> str:
        """Generate custom device class from spec"""
        
        return """
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
"""