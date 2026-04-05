// =============================================================================
// HealthController.cs — Lightweight health-check endpoint
// =============================================================================
// Provides GET /api/health for Docker health-checks, load balancers, and the
// MCP backend to verify the CAD Engine is alive.
//
// Namespace: cad_engine.Controllers (matches csproj RootNamespace)
// =============================================================================

using Microsoft.AspNetCore.Mvc;

namespace cad_engine.Controllers
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
            Console.WriteLine("[HealthController] GET /api/health — OK");
            return Ok("CAD Engine Running");
        }
    }
}
