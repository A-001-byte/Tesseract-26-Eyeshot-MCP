namespace CadEngine.Models
{
    public class CadResponse
    {
        public string Status { get; set; } = "Success";
        public string? Message { get; set; }
        public object? Data { get; set; }
    }
}
