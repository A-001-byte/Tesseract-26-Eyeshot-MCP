// =============================================================================
// HealthController.cs — Lightweight health-check endpoint
// =============================================================================
// Provides a simple GET /api/health endpoint used by Docker health-checks,
// load balancers, and the MCP backend to verify the CAD Engine is alive.
// =============================================================================

using Microsoft.AspNetCore.Mvc;

namespace CadEngine.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class HealthController : ControllerBase
    {
        /// <summary>
        /// Basic liveness probe for the CAD Engine service.
        /// </summary>
        /// <returns>A plain-text confirmation string.</returns>
        [HttpGet]
        [ProducesResponseType(StatusCodes.Status200OK)]
        public IActionResult Get()
        {
            return Ok("CAD Engine Running");
        }
    }
}
