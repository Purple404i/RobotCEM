namespace RobotCEM.Utils
{
    public static class ValidationUtils
    {
        public static bool ValidateDimensions(float length, float width, float height)
        {
            return length > 0 && width > 0 && height > 0;
        }
    }
}
