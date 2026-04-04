namespace CadEngine.Models
{
    public class CadRequest
    {
        public string? FilePath { get; set; }
        public string? Action { get; set; }
        public object? Parameters { get; set; }
    }
}
