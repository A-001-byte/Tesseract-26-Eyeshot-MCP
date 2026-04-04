// =============================================================================
// CadRequest.cs — Inbound request model for CAD operations
// =============================================================================
// INTEGRATION NOTE:
//   This replaces the old LoadModelRequest model.  CadRequest is the single
//   request model used by CadController for all endpoints that accept a body.
// =============================================================================

namespace cad_engine.Models
{
    /// <summary>
    /// Represents a request from the MCP backend to perform a CAD operation.
    /// </summary>
    public class CadRequest
    {
        /// <summary>Path to the STEP / IGES / OBJ file to load.</summary>
        public string? FilePath { get; set; }

        /// <summary>The CAD action to perform (e.g. "load_model", "list_entities").</summary>
        public string? Action { get; set; }

        /// <summary>Optional additional parameters for the action.</summary>
        public object? Parameters { get; set; }
    }
}
