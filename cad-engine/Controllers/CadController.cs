// =============================================================================
// CadController.cs — Core CAD operation endpoints
// =============================================================================
// Exposes REST endpoints that the MCP backend calls to perform CAD operations
// through the Eyeshot SDK wrapper (EyeshotService).
//
// Endpoints:
//   POST /api/cad/load           — Load a STEP / IGES model into the workspace
//   GET  /api/cad/entities       — List all entities currently in the workspace
//   GET  /api/cad/entities/{id}  — Get properties of a specific entity
// =============================================================================

using Microsoft.AspNetCore.Mvc;
using CadEngine.Models;
using CadEngine.Services;

namespace CadEngine.Controllers
{
    [ApiController]
    [Route("api/cad")]
    public class CadController : ControllerBase
    {
        private readonly EyeshotService _eyeshotService;
        private readonly ILogger<CadController> _logger;

        public CadController(EyeshotService eyeshotService, ILogger<CadController> logger)
        {
            _eyeshotService = eyeshotService;
            _logger = logger;
        }

        /// <summary>
        /// Loads a 3D model file (STEP / IGES) into the CAD workspace.
        /// </summary>
        [HttpPost("load")]
        [ProducesResponseType(typeof(CadResponse), StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public IActionResult LoadModel([FromBody] CadRequest request)
        {
            _logger.LogInformation("Received request to load model: {FilePath}", request.FilePath);

            if (string.IsNullOrEmpty(request.FilePath))
                return BadRequest(new CadResponse { Status = "Error", Message = "File path cannot be empty." });

            var success = _eyeshotService.LoadModel(request.FilePath);

            if (success)
                return Ok(new CadResponse { Status = "Success", Message = $"Model loaded: {request.FilePath}" });

            return StatusCode(500, new CadResponse { Status = "Error", Message = "Failed to load model." });
        }

        /// <summary>
        /// Returns all entities currently loaded in the CAD workspace.
        /// </summary>
        [HttpGet("entities")]
        [ProducesResponseType(typeof(CadResponse), StatusCodes.Status200OK)]
        public IActionResult ListEntities()
        {
            _logger.LogInformation("Listing entities in workspace");
            var entities = _eyeshotService.ListEntities();
            return Ok(new CadResponse { Status = "Success", Data = entities });
        }

        /// <summary>
        /// Returns geometric and material properties for a specific entity.
        /// </summary>
        [HttpGet("entities/{id}")]
        [ProducesResponseType(typeof(CadResponse), StatusCodes.Status200OK)]
        public IActionResult GetEntityProperties(string id)
        {
            _logger.LogInformation("Fetching properties for entity {EntityId}", id);
            var properties = _eyeshotService.GetEntityProperties(id);
            return Ok(new CadResponse { Status = "Success", Data = properties });
        }
    }
}
