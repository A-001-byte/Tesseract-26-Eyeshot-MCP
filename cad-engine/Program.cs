// =============================================================================
// Program.cs — CAD Engine API Entry Point
// =============================================================================
// This is the main entry point for the ASP.NET Core Web API that wraps the
// devDept Eyeshot SDK. It configures:
//   • Controller-based routing
//   • Swagger / OpenAPI documentation
//   • CORS (permissive for dev, restrict in production)
//   • Dependency Injection for the EyeshotService
// =============================================================================

var builder = WebApplication.CreateBuilder(args);

// ---------------------------------------------------------------------------
// 1. Register MVC Controllers
// ---------------------------------------------------------------------------
builder.Services.AddControllers();

// ---------------------------------------------------------------------------
// 2. Swagger / OpenAPI — available in all environments for hackathon ease
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
// 3. Dependency Injection — register application services
// ---------------------------------------------------------------------------
// EyeshotService is registered as a Singleton because the underlying CAD
// workspace is a long-lived, shared resource across requests.
builder.Services.AddSingleton<CadEngine.Services.EyeshotService>();

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

// Enable Swagger in ALL environments (hackathon-friendly; gate behind
// IsDevelopment() for production deployments).
app.UseSwagger();
app.UseSwaggerUI(options =>
{
    options.SwaggerEndpoint("/swagger/v1/swagger.json", "CAD Engine API v1");
    options.RoutePrefix = "swagger";            // accessible at /swagger
});

app.UseCors("AllowAll");
app.UseAuthorization();
app.MapControllers();

// ---------------------------------------------------------------------------
// 6. Start the server
// ---------------------------------------------------------------------------
app.Run();
