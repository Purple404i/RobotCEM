using System.Numerics;

namespace RobotCEM.Utils
{
    public static class GeometryUtils
    {
        public static float Distance(Vector3 a, Vector3 b)
        {
            return Vector3.Distance(a, b);
        }

        public static Vector3 Lerp(Vector3 a, Vector3 b, float t)
        {
            return Vector3.Lerp(a, b, t);
        }
    }
}
