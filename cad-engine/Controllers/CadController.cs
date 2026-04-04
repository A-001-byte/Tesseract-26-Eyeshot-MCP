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

        [HttpPost("load")]
        public IActionResult LoadModel([FromBody] CadRequest request)
        {
            _logger.LogInformation($"Received request to load model: {request.FilePath}");
            
            if (string.IsNullOrEmpty(request.FilePath))
                return BadRequest("File path cannot be empty.");

            var success = _eyeshotService.LoadModel(request.FilePath);

            if (success)
            {
                return Ok(new CadResponse { Status = "Success", Message = $"Model loaded: {request.FilePath}" });
            }

            return StatusCode(500, new CadResponse { Status = "Error", Message = "Failed to load model." });
        }

        [HttpGet("entities")]
        public IActionResult ListEntities()
        {
            _logger.LogInformation("Listing entities");
            var entities = _eyeshotService.ListEntities();
            return Ok(new CadResponse { Status = "Success", Data = entities });
        }

        [HttpGet("entities/{id}")]
        public IActionResult GetEntityProperties(string id)
        {
            _logger.LogInformation($"Getting properties for entity {id}");
            var properties = _eyeshotService.GetEntityProperties(id);
            return Ok(new CadResponse { Status = "Success", Data = properties });
        }
    }
}
