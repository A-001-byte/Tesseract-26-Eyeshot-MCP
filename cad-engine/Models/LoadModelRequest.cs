namespace cad_engine.Models;

/// <summary>
/// Request model for loading a CAD file.
/// </summary>
public class LoadModelRequest
{
    /// <summary>
    /// The path to the CAD file to load.
    /// </summary>
    public string FilePath { get; set; } = string.Empty;
}
