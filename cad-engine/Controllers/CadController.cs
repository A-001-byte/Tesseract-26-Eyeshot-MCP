// =============================================================================
// CadController.cs — Core CAD Operation Endpoints (Merged)
// =============================================================================
// INTEGRATION NOTE:
//   This file merges the old scaffold controller (load_model, list_entities)
//   with the production controller.  There is exactly ONE CadController.
//   It uses CadRequest/CadResponse models and delegates to EyeshotService.
//
// Route prefix: /api/cad
//
// Endpoints:
//   POST /api/cad/load             — Load a STEP / IGES / OBJ model
//   GET  /api/cad/entities/count   — Total entity count
//   GET  /api/cad/entities/list    — List of entity IDs
//   GET  /api/cad/entities/{id}    — Properties for a single entity
//
// Logging:
//   • Every request logged on entry with parameters
//   • Every response logged with status before returning
//   • Unhandled exceptions caught → logged at Error → returned as 500 JSON
// =============================================================================

using Microsoft.AspNetCore.Mvc;
using cad_engine.Models;
using cad_engine.Services;

namespace cad_engine.Controllers
{
    [ApiController]
    [Route("api/cad")]
    public class CadController : ControllerBase
    {
        // --------------------------------------------------------------------
        // Dependencies — injected by the ASP.NET Core DI container.
        // EyeshotService is a Singleton registered in Program.cs.
        // --------------------------------------------------------------------
        private readonly EyeshotService _eyeshotService;
        private readonly ILogger<CadController> _logger;

        public CadController(EyeshotService eyeshotService, ILogger<CadController> logger)
        {
            _eyeshotService = eyeshotService;
            _logger = logger;
        }

        // =============================================================
        // POST /api/cad/load
        // =============================================================
        /// <summary>
        /// Loads a 3D CAD model from the given file path.
        /// Accepts a JSON body with a single "filePath" field.
        /// Clears any previously loaded entities before importing.
        /// </summary>
        /// <param name="request">
        /// JSON body: <code>{ "filePath": "C:\\models\\part.step" }</code>
        /// </param>
        /// <returns>
        /// 200: <code>{ "status": "success", "message": "Model loaded successfully" }</code><br/>
        /// 400: filePath is empty or missing<br/>
        /// 500: file not found, unsupported format, or read failure
        /// </returns>
        [HttpPost("load")]
        [ProducesResponseType(typeof(CadResponse), StatusCodes.Status200OK)]
        [ProducesResponseType(typeof(CadResponse), StatusCodes.Status400BadRequest)]
        [ProducesResponseType(typeof(CadResponse), StatusCodes.Status500InternalServerError)]
        public IActionResult LoadModel([FromBody] LoadModelRequest request)
        {
            // --- Input validation ---
            if (string.IsNullOrWhiteSpace(request.FilePath))
            {
                _logger.LogWarning("POST /api/cad/load — rejected: empty filePath");
                Console.WriteLine("[CadController] POST /load — REJECTED (empty path)");
                return BadRequest(new CadResponse
                {
                    Status  = "error",
                    Message = "filePath cannot be empty."
                });
            }

            _logger.LogInformation("POST /api/cad/load — FilePath: \"{FilePath}\"", request.FilePath);
            Console.WriteLine($"[CadController] POST /load — {request.FilePath}");

            try
            {
                // Delegate to EyeshotService — no business logic changes
                string result = _eyeshotService.LoadModel(request.FilePath);

                if (result.StartsWith("Success", StringComparison.OrdinalIgnoreCase))
                {
                    _logger.LogInformation("POST /api/cad/load — 200: {Result}", result);
                    Console.WriteLine($"[CadController] POST /load — 200 OK");
                    return Ok(new CadResponse
                    {
                        Status  = "success",
                        Message = "Model loaded successfully"
                    });
                }

                // Non-success (file not found, unsupported format, etc.)
                _logger.LogWarning("POST /api/cad/load — 500: {Result}", result);
                Console.WriteLine($"[CadController] POST /load — 500 Error");
                return StatusCode(500, new CadResponse { Status = "error", Message = result });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "POST /api/cad/load — unhandled exception for \"{FilePath}\"", request.FilePath);
                Console.WriteLine($"[CadController] POST /load — EXCEPTION: {ex.Message}");
                return StatusCode(500, new CadResponse { Status = "error", Message = $"Internal error: {ex.Message}" });
            }
        }

        // =============================================================
        // GET /api/cad/entities/count
        // =============================================================
        /// <summary>
        /// Returns the total entity count in the CAD workspace.
        /// </summary>
        [HttpGet("entities/count")]
        [ProducesResponseType(typeof(CadResponse), StatusCodes.Status200OK)]
        public IActionResult GetEntityCount()
        {
            _logger.LogInformation("GET /api/cad/entities/count — request received");
            Console.WriteLine("[CadController] GET /entities/count");

            try
            {
                int count = _eyeshotService.GetEntityCount();

                _logger.LogInformation("GET /api/cad/entities/count — {Count}", count);
                Console.WriteLine($"[CadController] GET /entities/count — {count}");

                return Ok(new CadResponse
                {
                    Status = "Success",
                    Data   = new { TotalEntities = count }
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "GET /api/cad/entities/count — unhandled exception");
                Console.WriteLine($"[CadController] GET /entities/count — EXCEPTION: {ex.Message}");
                return StatusCode(500, new CadResponse { Status = "Error", Message = $"Internal error: {ex.Message}" });
            }
        }

        // =============================================================
        // GET /api/cad/entities/list
        // =============================================================
        /// <summary>
        /// Lists all entity identifiers currently in the workspace.
        /// </summary>
        [HttpGet("entities/list")]
        [ProducesResponseType(typeof(CadResponse), StatusCodes.Status200OK)]
        public IActionResult ListEntityIds()
        {
            _logger.LogInformation("GET /api/cad/entities/list — request received");
            Console.WriteLine("[CadController] GET /entities/list");

            try
            {
                var ids = _eyeshotService.ListEntityIds();

                _logger.LogInformation("GET /api/cad/entities/list — {Count} IDs", ids.Count);
                Console.WriteLine($"[CadController] GET /entities/list — {ids.Count} IDs");

                return Ok(new CadResponse
                {
                    Status = "Success",
                    Data   = ids
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "GET /api/cad/entities/list — unhandled exception");
                Console.WriteLine($"[CadController] GET /entities/list — EXCEPTION: {ex.Message}");
                return StatusCode(500, new CadResponse { Status = "Error", Message = $"Internal error: {ex.Message}" });
            }
        }

        // =============================================================
        // GET /api/cad/entities/{id}
        // =============================================================
        /// <summary>
        /// Returns properties (type, layer, visibility, colour) for one entity.
        /// </summary>
        /// <param name="id">Synthesised entity ID (e.g. "3_Mesh_Default").</param>
        [HttpGet("entities/{id}")]
        [ProducesResponseType(typeof(CadResponse), StatusCodes.Status200OK)]
        public IActionResult GetEntityProperties(string id)
        {
            _logger.LogInformation("GET /api/cad/entities/{EntityId} — request received", id);
            Console.WriteLine($"[CadController] GET /entities/{id}");

            try
            {
                var properties = _eyeshotService.GetEntityProperties(id);

                _logger.LogInformation("GET /api/cad/entities/{EntityId} — properties returned", id);

                return Ok(new CadResponse
                {
                    Status = "Success",
                    Data   = properties
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "GET /api/cad/entities/{EntityId} — unhandled exception", id);
                Console.WriteLine($"[CadController] GET /entities/{id} — EXCEPTION: {ex.Message}");
                return StatusCode(500, new CadResponse { Status = "Error", Message = $"Internal error: {ex.Message}" });
            }
        }
    }
}
