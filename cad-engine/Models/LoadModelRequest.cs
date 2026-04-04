// =============================================================================
// LoadModelRequest.cs — Request model for POST /api/cad/load
// =============================================================================
// A focused, minimal request body for the load endpoint.
// Swagger will generate a clean JSON input with a single "filePath" field.
// =============================================================================

namespace cad_engine.Models
{
    /// <summary>
    /// Request body for loading a CAD model from a file path.
    /// </summary>
    public class LoadModelRequest
    {
        /// <summary>
        /// Absolute path to the CAD file to load.
        /// Supported formats: .step, .stp, .iges, .igs, .obj
        /// Example: "C:\\models\\part.step"
        /// </summary>
        public string FilePath { get; set; } = string.Empty;
    }
}
