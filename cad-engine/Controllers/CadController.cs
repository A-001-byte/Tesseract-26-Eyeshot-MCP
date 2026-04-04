using cad_engine.Models;
using cad_engine.Services;
using Microsoft.AspNetCore.Mvc;

namespace cad_engine.Controllers;

/// <summary>
/// Controller exposing REST API endpoints for CAD operations.
/// </summary>
[ApiController]
[Route("api/cad")]
public class CadController : ControllerBase
{
    private readonly EyeshotService _eyeshotService;

    public CadController(EyeshotService eyeshotService)
    {
        _eyeshotService = eyeshotService;
    }

    /// <summary>
    /// Loads a CAD model.
    /// </summary>
    /// <param name="request">Request containing the file path.</param>
    /// <returns>Success message if loaded.</returns>
    [HttpPost("load_model")]
    public IActionResult LoadModel([FromBody] LoadModelRequest request)
    {
        // Ask service to load model using provided file path
        bool success = _eyeshotService.LoadModel(request.FilePath);

        if (success)
        {
            return Ok(new { message = "Model loaded successfully." });
        }
        
        return BadRequest(new { message = "Failed to load model. Invalid or missing FilePath." });
    }

    /// <summary>
    /// Lists entities from the (dummy) loaded model.
    /// </summary>
    /// <returns>A list of CAD entities.</returns>
    [HttpGet("list_entities")]
    public IActionResult ListEntities()
    {
        var entities = _eyeshotService.ListEntities();
        return Ok(entities);
    }
}
