// =============================================================================
// EyeshotService.cs — Eyeshot SDK wrapper
// =============================================================================
// Encapsulates all interactions with the devDept Eyeshot CAD engine.
// Currently uses placeholder/simulated logic so the API can be tested
// end-to-end without an Eyeshot license.
//
// Replace the stub implementations with real Eyeshot calls when the
// NuGet package is installed and a valid license key is available.
// =============================================================================

namespace CadEngine.Services
{
    /// <summary>
    /// Singleton service that manages the Eyeshot CAD workspace.
    /// </summary>
    public class EyeshotService
    {
        private readonly ILogger<EyeshotService> _logger;

        // Placeholder for the actual Eyeshot Design / Workspace object
        // private Design _workspace;

        public EyeshotService(ILogger<EyeshotService> logger)
        {
            _logger = logger;

            // TODO: Unlock Eyeshot license on startup
            // devDept.LicenseManager.Unlock("YOUR-EYESHOT-LICENSE-KEY");

            _logger.LogInformation("EyeshotService initialised (stub mode)");
        }

        /// <summary>
        /// Loads a STEP or IGES file into the CAD workspace.
        /// </summary>
        /// <param name="filePath">Absolute or relative path to the model file.</param>
        /// <returns>True if the model was loaded successfully.</returns>
        public bool LoadModel(string filePath)
        {
            _logger.LogInformation("[EyeshotService] Loading model from {FilePath}", filePath);

            // Real implementation:
            // var reader = new ReadSTEP(filePath);
            // reader.DoWork();
            // _workspace.Entities.AddRange(reader.Entities);

            return true; // Stub: always succeeds
        }

        /// <summary>
        /// Lists high-level information about every entity in the workspace.
        /// </summary>
        public object ListEntities()
        {
            _logger.LogInformation("[EyeshotService] Listing workspace entities");

            // Stub data — replace with _workspace.Entities enumeration
            return new
            {
                TotalEntities = 12,
                Layers = new[] { "Default", "Construction" }
            };
        }

        /// <summary>
        /// Returns geometric and material properties for a given entity.
        /// </summary>
        /// <param name="id">The entity identifier.</param>
        public object GetEntityProperties(string id)
        {
            _logger.LogInformation("[EyeshotService] Properties requested for entity {Id}", id);

            // Stub data — replace with real bounding-box / mass-property queries
            return new
            {
                Id = id,
                Volume = 1250.45,
                SurfaceArea = 600.22,
                Material = "Steel"
            };
        }
    }
}
