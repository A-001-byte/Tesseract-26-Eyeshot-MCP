namespace cad_engine.Models;

/// <summary>
/// Response model representing a CAD entity.
/// </summary>
public class EntityResponse
{
    /// <summary>
    /// The unique identifier of the entity.
    /// </summary>
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// The type of the entity (e.g., Line, Circle, Mesh).
    /// </summary>
    public string Type { get; set; } = string.Empty;
}
