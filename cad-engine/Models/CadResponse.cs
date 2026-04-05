// =============================================================================
// CadResponse.cs — Standard API response envelope
// =============================================================================
// INTEGRATION NOTE:
//   This replaces the old anonymous-object responses.  Every endpoint in
//   CadController returns a CadResponse for consistent JSON shape.
// =============================================================================

namespace cad_engine.Models
{
    /// <summary>
    /// Uniform response wrapper returned by all CAD Engine endpoints.
    /// </summary>
    public class CadResponse
    {
        /// <summary>"Success" or "Error".</summary>
        public string Status { get; set; } = "Success";

        /// <summary>Human-readable message (loaded, failed, etc.).</summary>
        public string? Message { get; set; }

        /// <summary>Arbitrary payload (entity list, properties, counts, etc.).</summary>
        public object? Data { get; set; }
    }
}
