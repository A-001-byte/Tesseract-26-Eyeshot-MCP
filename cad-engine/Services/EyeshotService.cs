// =============================================================================
// EyeshotService.cs — devDept Eyeshot SDK Wrapper (Merged)
// =============================================================================
// INTEGRATION NOTE:
//   This file merges the placeholder EyeshotService (bool LoadModel, dummy
//   ListEntities) with the production Eyeshot SDK implementation.  The old
//   placeholder logic has been fully replaced; this is the single source of
//   truth for all CAD operations.
//
// Namespace:  cad_engine.Services  (matches csproj RootNamespace)
//
// Logging strategy:
//   LogDebug       — Low-level steps (reader selection, iteration details)
//   LogInformation — Key milestones (model loaded, entity counts returned)
//   LogWarning     — Recoverable issues (empty file, unsupported format)
//   LogError       — Exceptions that prevent an operation from completing
// =============================================================================

using System.Diagnostics;
using devDept.Eyeshot;
using devDept.Eyeshot.Entities;
using devDept.Eyeshot.Translators;
using devDept.Geometry;

namespace cad_engine.Services
{
    /// <summary>
    /// Singleton service that owns the Eyeshot <see cref="Model"/> workspace
    /// and provides CAD operations to the rest of the application.
    /// Registered as Singleton in Program.cs so model state persists.
    /// </summary>
    public class EyeshotService
    {
        private readonly ILogger<EyeshotService> _logger;

        // ---------------------------------------------------------------
        // The core Eyeshot object that holds all loaded 3D entities.
        // Using Model (headless) instead of Design (WinForms control)
        // so we can run inside a Web API without a GUI.
        // ---------------------------------------------------------------
        private readonly Model _model;

        public EyeshotService(ILogger<EyeshotService> logger)
        {
            _logger = logger;

            _logger.LogDebug("Unlocking Eyeshot license...");
            Console.WriteLine("[EyeshotService] Initialising — unlocking license...");

            // Fetch the Eyeshot license key from the EYESHOT_LICENSE_KEY environment variable.
            string? licenseKey = Environment.GetEnvironmentVariable("EYESHOT_LICENSE_KEY");

            if (string.IsNullOrWhiteSpace(licenseKey))
            {
                string errorMsg = "CRITICAL: EYESHOT_LICENSE_KEY environment variable is missing or empty. Eyeshot cannot be unlocked.";
                _logger.LogCritical(errorMsg);
                Console.WriteLine($"[EyeshotService] {errorMsg}");
                throw new InvalidOperationException(errorMsg);
            }

            // Unlock the Eyeshot license (required before any SDK call)
            devDept.LicenseManager.Unlock(typeof(Model), licenseKey);

            // Create a blank headless model
            _model = new Model();

            _logger.LogInformation("EyeshotService initialised — Model workspace ready (0 entities)");
            Console.WriteLine("[EyeshotService] Ready — workspace initialised with 0 entities");
        }

        // =================================================================
        // LoadModel — Import a STEP, IGES, or OBJ file
        // =================================================================
        /// <summary>
        /// Resolves the supplied path to an absolute path, validates the file
        /// exists, clears the workspace, and imports all entities from the file.
        /// Supported: .step, .stp, .iges, .igs, .obj
        /// </summary>
        /// <param name="filePath">Absolute or relative path to the CAD file.</param>
        /// <returns>A human-readable success or error message.</returns>
        public string LoadModel(string filePath)
        {
            var sw = Stopwatch.StartNew();

            try
            {
                // 1. Resolve to absolute path
                string absolutePath = Path.GetFullPath(filePath);
                _logger.LogInformation("LoadModel started — raw: \"{RawPath}\", resolved: \"{AbsPath}\"", filePath, absolutePath);
                Console.WriteLine($"[LoadModel] Loading: {absolutePath}");

                // 2. Validate file exists
                if (!File.Exists(absolutePath))
                {
                    _logger.LogWarning("LoadModel FAILED — file not found: {AbsPath}", absolutePath);
                    Console.WriteLine($"[LoadModel] ERROR — File not found: {absolutePath}");
                    return $"Error: File not found — {absolutePath}";
                }

                _logger.LogDebug("File verified on disk: {AbsPath}", absolutePath);

                // 3. Clear workspace
                int previousCount = _model.Entities.Count;
                _model.Entities.Clear();
                _logger.LogInformation("Workspace cleared ({PreviousCount} entities removed)", previousCount);
                Console.WriteLine($"[LoadModel] Cleared {previousCount} previous entities");

                // 4. Select reader based on extension
                string extension = Path.GetExtension(absolutePath).ToLowerInvariant();
                ReadFileAsync reader;

                switch (extension)
                {
                    case ".step":
                    case ".stp":
                        reader = new ReadSTEP(absolutePath);
                        _logger.LogDebug("Reader selected: ReadSTEP for extension {Ext}", extension);
                        Console.WriteLine("[LoadModel] Using ReadSTEP reader");
                        break;

                    case ".iges":
                    case ".igs":
                        reader = new ReadIGES(absolutePath);
                        _logger.LogDebug("Reader selected: ReadIGES for extension {Ext}", extension);
                        Console.WriteLine("[LoadModel] Using ReadIGES reader");
                        break;

                    case ".obj":
                        reader = new ReadOBJ(absolutePath);
                        _logger.LogDebug("Reader selected: ReadOBJ for extension {Ext}", extension);
                        Console.WriteLine("[LoadModel] Using ReadOBJ reader");
                        break;

                    default:
                        _logger.LogWarning("LoadModel FAILED — unsupported extension: {Ext}", extension);
                        Console.WriteLine($"[LoadModel] ERROR — Unsupported format: {extension}");
                        return $"Error: Unsupported file format '{extension}'. Supported: .step, .stp, .iges, .igs, .obj";
                }

                // 5. Execute reader (synchronous / blocking)
                _logger.LogDebug("Starting file read...");
                Console.WriteLine("[LoadModel] Reading file...");
                reader.DoWork();
                _logger.LogDebug("File read completed in {Elapsed}ms", sw.ElapsedMilliseconds);

                // 6. Check results
                if (reader.Entities == null || reader.Entities.Length == 0)
                {
                    _logger.LogWarning("LoadModel completed but file contained 0 entities — {File}", Path.GetFileName(absolutePath));
                    Console.WriteLine("[LoadModel] WARNING — No entities found in file");
                    return "Warning: File was read successfully but contained no entities.";
                }

                // 7. Add parsed entities to workspace
                _model.Entities.AddRange(reader.Entities);

                sw.Stop();
                string fileName = Path.GetFileName(absolutePath);

                _logger.LogInformation(
                    "LoadModel SUCCESS — {Count} entities loaded from \"{File}\" in {Elapsed}ms",
                    reader.Entities.Length, fileName, sw.ElapsedMilliseconds);
                Console.WriteLine($"[LoadModel] SUCCESS — {reader.Entities.Length} entities from {fileName} ({sw.ElapsedMilliseconds}ms)");

                return $"Success: Loaded {reader.Entities.Length} entities from {fileName}";
            }
            catch (Exception ex)
            {
                sw.Stop();
                _logger.LogError(ex,
                    "LoadModel EXCEPTION after {Elapsed}ms — FilePath: \"{FilePath}\", Message: {ErrorMsg}",
                    sw.ElapsedMilliseconds, filePath, ex.Message);
                Console.WriteLine($"[LoadModel] EXCEPTION — {ex.Message}");
                return $"Error: {ex.Message}";
            }
        }

        // =================================================================
        // GetEntityCount
        // =================================================================
        /// <summary>
        /// Returns the total number of entities currently loaded.
        /// </summary>
        public int GetEntityCount()
        {
            try
            {
                int count = _model.Entities.Count;
                _logger.LogInformation("GetEntityCount — {Count} entities in workspace", count);
                Console.WriteLine($"[GetEntityCount] {count} entities");
                return count;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "GetEntityCount FAILED — {ErrorMsg}", ex.Message);
                Console.WriteLine($"[GetEntityCount] ERROR — {ex.Message}");
                return 0;
            }
        }

        // =================================================================
        // ListEntityIds
        // =================================================================
        /// <summary>
        /// Returns synthesised identifiers (Index_Type_Layer) for every entity.
        /// Eyeshot entities don't have a built-in ID, so we build one from
        /// the index, type name, and layer name.
        /// </summary>
        public List<string> ListEntityIds()
        {
            var ids = new List<string>();

            try
            {
                _logger.LogDebug("ListEntityIds — iterating {Count} entities", _model.Entities.Count);

                for (int i = 0; i < _model.Entities.Count; i++)
                {
                    var entity = _model.Entities[i];
                    string typeName  = entity.GetType().Name;
                    string layerName = entity.LayerName ?? "Default";
                    ids.Add($"{i}_{typeName}_{layerName}");
                }

                _logger.LogInformation("ListEntityIds — returned {Count} identifiers", ids.Count);
                Console.WriteLine($"[ListEntityIds] {ids.Count} IDs returned");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "ListEntityIds FAILED — {ErrorMsg}", ex.Message);
                Console.WriteLine($"[ListEntityIds] ERROR — {ex.Message}");
            }

            return ids;
        }

        // =================================================================
        // GetEntityProperties
        // =================================================================
        /// <summary>
        /// Returns geometric and visual properties for the entity at the
        /// given synthesised ID (e.g. "3_Mesh_Default").
        /// </summary>
        public object GetEntityProperties(string id)
        {
            try
            {
                _logger.LogDebug("GetEntityProperties called with ID: {Id}", id);

                string indexPart = id.Split('_')[0];
                if (!int.TryParse(indexPart, out int index) || index < 0 || index >= _model.Entities.Count)
                {
                    _logger.LogWarning("GetEntityProperties — invalid ID: {Id} (workspace has {Count} entities)", id, _model.Entities.Count);
                    return new { Error = $"Invalid entity ID: {id}" };
                }

                var entity = _model.Entities[index];

                var result = new
                {
                    Id        = id,
                    Index     = index,
                    Type      = entity.GetType().Name,
                    LayerName = entity.LayerName ?? "Default",
                    Visible   = entity.Visible,
                    Color     = entity.Color.ToString()
                };

                _logger.LogInformation("GetEntityProperties — returned props for entity {Id} (Type: {Type})", id, result.Type);
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "GetEntityProperties FAILED for ID {Id} — {ErrorMsg}", id, ex.Message);
                return new { Error = ex.Message };
            }
        }
    }
}
