using System.IO;
using System.Xml;
using UnityEditor.Android;

// Add permissions to the generated library manifest; leave PICO/OpenXR manifest processing intact.
public sealed class DoorBleManifest : IPostGenerateGradleAndroidProject
{
    public int callbackOrder => 200;
    const string Android="http://schemas.android.com/apk/res/android";
    public void OnPostGenerateGradleAndroidProject(string path)
    {
        string file=Path.Combine(path,"src/main/AndroidManifest.xml");
        var doc=new XmlDocument();doc.Load(file);var root=doc.DocumentElement;
        void Permission(string name,string max=null,bool noLocation=false)
        {
            XmlElement found=null;
            foreach(XmlNode node in root.ChildNodes)if(node is XmlElement e&&e.Name=="uses-permission"&&e.GetAttribute("name",Android)==name)found=e;
            if(found==null){found=doc.CreateElement("uses-permission");root.AppendChild(found);}
            found.SetAttribute("name",Android,name);
            if(max!=null)found.SetAttribute("maxSdkVersion",Android,max);
            if(noLocation)found.SetAttribute("usesPermissionFlags",Android,"neverForLocation");
        }
        Permission("android.permission.BLUETOOTH","30");Permission("android.permission.BLUETOOTH_ADMIN","30");
        Permission("android.permission.ACCESS_FINE_LOCATION","30");
        Permission("android.permission.BLUETOOTH_SCAN",null,true);Permission("android.permission.BLUETOOTH_CONNECT");
        doc.Save(file);
    }
}
