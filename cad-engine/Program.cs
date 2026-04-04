using cad_engine.Services;

// Configure ASP.NET Core Web API
var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddControllers();

// Enable Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Register EyeshotService as Singleton
builder.Services.AddSingleton<EyeshotService>();

// Build the application
var app = builder.Build();

// Configure the HTTP request pipeline.
// Enable Swagger UI unconditionally as requested for the scaffold
app.UseSwagger();
app.UseSwaggerUI();

app.MapControllers();

app.Run();
