// =============================================================================
// Program.cs — CAD Engine API Entry Point (Merged)
// =============================================================================
// This is the single, authoritative entry point for the cad-engine service.
// It wires up:
//   1. MVC Controllers
//   2. Swagger / OpenAPI (always on for hackathon ease)
//   3. EyeshotService as a Singleton (model state persists across requests)
//   4. CORS (permissive for dev — MCP backend + React frontend can call us)
//   5. Kestrel on port 5000
//
// INTEGRATION NOTE:
//   This file merges the minimal scaffold Program.cs with the production-
//   grade configuration.  There is exactly ONE Program.cs in the project.
// =============================================================================

using cad_engine.Services;

var builder = WebApplication.CreateBuilder(args);

// ---------------------------------------------------------------------------
// 1. Register MVC Controllers — auto-discovers CadController + HealthController
// ---------------------------------------------------------------------------
builder.Services.AddControllers();

// ---------------------------------------------------------------------------
// 2. Swagger / OpenAPI — available in ALL environments for easy testing
// ---------------------------------------------------------------------------
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title       = "CAD Engine API",
        Version     = "v1",
        Description = "REST API wrapping the devDept Eyeshot SDK for AI-driven CAD operations."
    });
});

// ---------------------------------------------------------------------------
// 3. Dependency Injection — EyeshotService is a SINGLETON
//    Why Singleton?  The underlying Eyeshot Model is a long-lived, shared
//    resource.  We want loaded entities to persist across HTTP requests.
// ---------------------------------------------------------------------------
builder.Services.AddSingleton<EyeshotService>();

// ---------------------------------------------------------------------------
// 4. CORS — allow the Python MCP backend and React frontend to call us
// ---------------------------------------------------------------------------
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// ---------------------------------------------------------------------------
// 5. Middleware Pipeline
// ---------------------------------------------------------------------------

// Swagger UI — accessible at /swagger
app.UseSwagger();
app.UseSwaggerUI(options =>
{
    options.SwaggerEndpoint("/swagger/v1/swagger.json", "CAD Engine API v1");
    options.RoutePrefix = "swagger";
});

app.UseCors("AllowAll");
app.UseAuthorization();
app.MapControllers();

// ---------------------------------------------------------------------------
// 6. Startup log — confirms the server is alive
// ---------------------------------------------------------------------------
Console.WriteLine("============================================");
Console.WriteLine("  CAD Engine API started");
Console.WriteLine("  Swagger UI → http://localhost:5000/swagger");
Console.WriteLine("  Health     → http://localhost:5000/api/health");
Console.WriteLine("============================================");

app.Run();
