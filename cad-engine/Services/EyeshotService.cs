using cad_engine.Models;

namespace cad_engine.Services;

/// <summary>
/// Service acting as an abstraction layer for the CAD engine.
/// Placeholder logic for future Eyeshot integration.
/// </summary>
public class EyeshotService
{
    /// <summary>
    /// Simulates loading a CAD model from a file path.
    /// </summary>
    /// <param name="filePath">Path to the CAD file.</param>
    /// <returns>True if the model loaded successfully, false otherwise.</returns>
    public bool LoadModel(string filePath)
    {
        // Placeholder return until actual Eyeshot logic is integrated
        return !string.IsNullOrWhiteSpace(filePath);
    }

    /// <summary>
    /// Retrieves a list of dummy entities from the loaded CAD model.
    /// </summary>
    /// <returns>A list of CAD entities.</returns>
    public IEnumerable<EntityResponse> ListEntities()
    {
        // Returning dummy values as a placeholder
        return new List<EntityResponse>
        {
            new EntityResponse { Id = Guid.NewGuid().ToString(), Type = "Line" },
            new EntityResponse { Id = Guid.NewGuid().ToString(), Type = "Circle" },
            new EntityResponse { Id = Guid.NewGuid().ToString(), Type = "Mesh" }
        };
    }
}
