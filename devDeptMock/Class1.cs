using System;
using System.Collections.Generic;
using System.Drawing;

namespace devDept
{
    public class LicenseManager
    {
        public static void Unlock(Type type, string key) { }
    }
}

namespace devDept.Eyeshot
{
    public class Model
    {
        public devDept.Eyeshot.Entities.EntityList Entities { get; set; } = new devDept.Eyeshot.Entities.EntityList();
    }
}

namespace devDept.Eyeshot.Entities
{
    public class Entity
    {
        public string LayerName { get; set; } = "Default";
        public bool Visible { get; set; } = true;
        public Color Color { get; set; } = Color.Gray;
    }

    public class EntityList : List<Entity> { }
}

namespace devDept.Eyeshot.Translators
{
    public class ReadFileAsync
    {
        public devDept.Eyeshot.Entities.Entity[] Entities { get; set; } = Array.Empty<devDept.Eyeshot.Entities.Entity>();
        public virtual void DoWork()
        {
            // Demo-friendly mock behavior: reading any supported file returns one stub entity.
            Entities = new[] { new devDept.Eyeshot.Entities.Entity() };
        }
    }

    public class ReadSTEP : ReadFileAsync
    {
        public ReadSTEP(string path) { }
    }

    public class ReadIGES : ReadFileAsync
    {
        public ReadIGES(string path) { }
    }

    public class ReadOBJ : ReadFileAsync
    {
        public ReadOBJ(string path) { }
    }
}

namespace devDept.Geometry
{
    public class Point3D
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double Z { get; set; }
    }
}

namespace devDept.Eyeshot.Control
{
    // Empty namespace to satisfy the DLL requirement
}
